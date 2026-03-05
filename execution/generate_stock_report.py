"""
원부자재 / 반제품 / 완제품 재고 현황을 로컬 CSV 파일로 저장합니다.
출력: .tmp/stock_report_{type}_{date}.csv

사용법:
  python generate_stock_report.py --type all
"""

import os, argparse, csv
import pymysql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    host=os.getenv("MES_DB_HOST"), user=os.getenv("MES_DB_USER"),
    passwd=os.getenv("MES_DB_PASS"), db="mes_db", charset="utf8mb4"
)

def update_raw_materials():
    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT material_code, material_name, unit,
                   current_qty, allocated_qty,
                   (current_qty - allocated_qty) AS available_qty,
                   safety_stock,
                   CASE
                     WHEN (current_qty - allocated_qty) = 0 THEN '🔴 소진'
                     WHEN (current_qty - allocated_qty) <= safety_stock THEN '⚠️ 부족'
                     ELSE '✅ 정상'
                   END AS status
            FROM material_stock
            WHERE is_active = 1
        """)
        rows = cur.fetchall()
    conn.close()

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(".tmp", exist_ok=True)
    file_path = f".tmp/stock_report_raw_{date_str}.csv"
    
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["코드", "품명", "단위", "현재고", "할당재고", "가용재고", "안전재고", "상태"])
        for r in rows:
            writer.writerow([
                r["material_code"], r["material_name"], r["unit"],
                float(r["current_qty"]), float(r["allocated_qty"]),
                float(r["available_qty"]), float(r["safety_stock"]), r["status"]
            ])
            
    print(f"✅ 원부자재 재고 보고서 저장 완료: {file_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["raw", "semi", "finished", "all"], default="all")
    args = parser.parse_args()

    if args.type in ["raw", "all"]:
        update_raw_materials()

if __name__ == "__main__":
    main()
