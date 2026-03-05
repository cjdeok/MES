"""
반제품 입고를 MES DB에 등록합니다.
사용법:
  python record_semifinished_in.py \
    --code WIP-2001 --order_no WO-20250227-0041 \
    --qty_produced 150 --qty_defect 3 --work_center LINE-01
"""

import os, argparse
import pymysql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    host=os.getenv("MES_DB_HOST"), user=os.getenv("MES_DB_USER"),
    passwd=os.getenv("MES_DB_PASS"), db="mes_db", charset="utf8mb4"
)

def record_in(code, order_no, qty_produced, qty_defect, work_center):
    qty_good = qty_produced - qty_defect
    defect_rate = round(qty_defect / qty_produced * 100, 2) if qty_produced > 0 else 0

    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            # 반제품 재고 증가
            cur.execute("""
                INSERT INTO semifinished_stock (material_code, current_qty, updated_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    current_qty = current_qty + %s,
                    updated_at  = %s
            """, (code, qty_good, datetime.now(), qty_good, datetime.now()))

            # 입고 이력
            cur.execute("""
                INSERT INTO semifinished_transactions
                (material_code, trans_type, qty_good, qty_defect,
                 defect_rate, order_no, work_center, created_at)
                VALUES (%s, 'IN', %s, %s, %s, %s, %s, %s)
            """, (code, qty_good, qty_defect, defect_rate,
                  order_no, work_center, datetime.now()))

            # 생산지시 진행 이력 업데이트
            cur.execute("""
                UPDATE production_orders
                SET qty_completed = qty_completed + %s, updated_at = %s
                WHERE order_no = %s
            """, (qty_good, datetime.now(), order_no))

        conn.commit()
        print(f"반제품 입고 완료: {code} 양품 {qty_good}ea / 불량 {qty_defect}ea ({defect_rate}%)")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code",         required=True)
    parser.add_argument("--order_no",     required=True)
    parser.add_argument("--qty_produced", required=True, type=int)
    parser.add_argument("--qty_defect",   required=True, type=int)
    parser.add_argument("--work_center",  required=True)
    args = parser.parse_args()
    record_in(args.code, args.order_no, args.qty_produced, args.qty_defect, args.work_center)

if __name__ == "__main__":
    main()
