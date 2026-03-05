"""
생산지시 확정 시 원부자재 재고를 가용재고 → 할당재고로 이동합니다.
(실제 차감은 반제품/완제품 입고 시 처리)

사용법:
  python deduct_material_stock.py --order_no WO-20250227-0041
"""

import os, json, argparse
import pymysql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    host=os.getenv("MES_DB_HOST"), user=os.getenv("MES_DB_USER"),
    passwd=os.getenv("MES_DB_PASS"), db="mes_db", charset="utf8mb4"
)

def allocate_materials(order_no: str, force: bool = False):
    """BOM 기준으로 원부자재 할당 처리"""
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # 생산지시 기준 필요 자재 조회
            cur.execute("""
                SELECT b.material_code, b.qty_per * po.qty AS needed_qty, b.unit
                FROM production_orders po
                JOIN bom b ON b.product_code = po.product_code
                WHERE po.order_no = %s AND po.status = 'CONFIRMED'
            """, (order_no,))
            materials = cur.fetchall()

            results = []
            for mat in materials:
                # 가용재고 확인
                cur.execute("""
                    SELECT current_qty, allocated_qty
                    FROM material_stock
                    WHERE material_code = %s
                    FOR UPDATE
                """, (mat["material_code"],))
                stock = cur.fetchone()
                if not stock:
                    print(f"  ⚠️ {mat['material_code']}: 재고 마스터 정보 없음")
                    continue

                available = stock["current_qty"] - stock["allocated_qty"]
                actual_alloc = min(available, mat["needed_qty"])  # 가용분까지만 할당

                # 할당재고 증가
                cur.execute("""
                    UPDATE material_stock
                    SET allocated_qty = allocated_qty + %s,
                        updated_at    = %s
                    WHERE material_code = %s
                """, (actual_alloc, datetime.now(), mat["material_code"]))

                # 이력 기록
                cur.execute("""
                    INSERT INTO material_transactions
                    (material_code, trans_type, qty, order_no, note, created_at)
                    VALUES (%s, 'ALLOCATE', %s, %s, '생산지시 자재할당', %s)
                """, (mat["material_code"], actual_alloc, order_no, datetime.now()))

                shortage = mat["needed_qty"] - actual_alloc
                results.append({
                    "material_code": mat["material_code"],
                    "needed": mat["needed_qty"],
                    "allocated": actual_alloc,
                    "shortage": shortage
                })
                print(f"  {mat['material_code']}: 할당 {actual_alloc}{mat['unit']}"
                      + (f" / 부족 {shortage}{mat['unit']} ⚠️" if shortage > 0 else " ✅"))

        conn.commit()
        print(f"\n할당 완료: {order_no}")
        return results

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--order_no", required=True)
    parser.add_argument("--force", action="store_true", help="재고 부족 시에도 강제 진행")
    args = parser.parse_args()
    allocate_materials(args.order_no, args.force)

if __name__ == "__main__":
    main()
