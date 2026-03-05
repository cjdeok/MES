"""
BOM 전개 후 원부자재/반제품/완제품 재고 충분 여부를 계산합니다.
출력: .tmp/stock_check_{order_no}.json

사용법:
  python check_material_stock.py --product FG-1001 --qty 200
  python check_material_stock.py --type semifinished --code WIP-2001
  python check_material_stock.py --all
"""

import os, json, argparse
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    host   = os.getenv("MES_DB_HOST"),
    user   = os.getenv("MES_DB_USER"),
    passwd = os.getenv("MES_DB_PASS"),
    db     = "mes_db",
    charset= "utf8mb4"
)

def get_bom(product_code: str, qty: int, level: int = 0) -> list[dict]:
    """BOM 재귀 전개 (최대 5레벨)"""
    if level >= 5:
        return []

    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT material_code, material_name, qty_per, unit
            FROM bom
            WHERE product_code = %s AND is_active = 1
        """, (product_code,))
        rows = cur.fetchall()
    conn.close()

    materials = []
    for row in rows:
        needed_qty = row["qty_per"] * qty
        materials.append({
            "material_code": row["material_code"],
            "material_name": row["material_name"],
            "needed_qty":    needed_qty,
            "unit":          row["unit"],
            "level":         level
        })
        # 하위 BOM 재귀 전개
        sub = get_bom(row["material_code"], needed_qty, level + 1)
        materials.extend(sub)

    return materials

def get_current_stock(material_code: str) -> dict:
    """현재 재고, 할당재고, 가용재고 조회"""
    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT current_qty, allocated_qty,
                   (current_qty - allocated_qty) AS available_qty,
                   safety_stock
            FROM material_stock
            WHERE material_code = %s
        """, (material_code,))
        row = cur.fetchone()
    conn.close()
    return row or {"current_qty": 0, "allocated_qty": 0, "available_qty": 0, "safety_stock": 0}

def check_product_materials(product_code: str, qty: int) -> dict:
    """완제품 생산 시 원부자재 충분 여부 확인"""
    bom_items = get_bom(product_code, qty)

    results = []
    has_shortage = False

    for item in bom_items:
        stock  = get_current_stock(item["material_code"])
        available = stock["available_qty"]
        shortage  = max(0, item["needed_qty"] - available)

        if shortage > 0:
            has_shortage = True

        results.append({
            **item,
            "current_qty":   stock["current_qty"],
            "allocated_qty": stock["allocated_qty"],
            "available_qty": available,
            "shortage":      shortage,
            "is_ok":         shortage == 0
        })

    return {"product_code": product_code, "qty": qty,
            "has_shortage": has_shortage, "materials": results}

def check_all_stocks() -> list[dict]:
    """전체 원부자재 안전재고 이하 품목 조회"""
    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT material_code, material_name,
                   current_qty, allocated_qty,
                   (current_qty - allocated_qty) AS available_qty,
                   safety_stock, unit
            FROM material_stock
            WHERE is_active = 1
            ORDER BY (current_qty - allocated_qty) ASC
        """)
        rows = cur.fetchall()
    conn.close()
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", help="완제품 코드")
    parser.add_argument("--qty",     type=int, default=1)
    parser.add_argument("--type",    choices=["raw", "semifinished", "finished"], default="raw")
    parser.add_argument("--code",    help="반제품/완제품 코드 (단건 조회)")
    parser.add_argument("--all",     action="store_true", help="전체 재고 조회")
    parser.add_argument("--order_no",help="생산지시 번호 (출력 파일명용)")
    args = parser.parse_args()

    os.makedirs(".tmp", exist_ok=True)

    if args.all:
        result = check_all_stocks()
        output_path = ".tmp/stock_check_all.json"
    elif args.product:
        result = check_product_materials(args.product, args.qty)
        order_no = args.order_no or "draft"
        output_path = f".tmp/stock_check_{order_no}.json"
    else:
        # 단건 재고 조회
        result = get_current_stock(args.code)
        output_path = f".tmp/stock_check_{args.code}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"재고 확인 완료: {output_path}")

    # 부족 품목 콘솔 출력
    if isinstance(result, dict) and result.get("has_shortage"):
        print("\n⚠️ 부족 품목:")
        for m in result["materials"]:
            if not m["is_ok"]:
                print(f"  {m['material_code']} {m['material_name']}: "
                      f"필요 {m['needed_qty']}{m['unit']} / 가용 {m['available_qty']}{m['unit']} "
                      f"(부족 {m['shortage']}{m['unit']})")

if __name__ == "__main__":
    main()
