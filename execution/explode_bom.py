import sqlite3
import json
import os

db_file = r'c:\Users\ENS-1000\Documents\Antigravity\MES\mes_database.db'

def explode_bom(item_code, target_qty):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # BOM 조회
    cursor.execute("""
        SELECT child_item_code, qty_per, unit, loss_rate 
        FROM bom 
        WHERE parent_item_code = ? AND is_active = 1
    """, (item_code,))
    
    bom_items = cursor.fetchall()
    
    results = []
    for item in bom_items:
        # 수식 적용: (원단위 * 생산수량) / (1 - 로스율)
        needed_qty = (item['qty_per'] * target_qty) / (1 - item['loss_rate'])
        
        results.append({
            "material_code": item['child_item_code'],
            "base_qty_per": item['qty_per'],
            "needed_qty": round(needed_qty, 4),
            "unit": item['unit'],
            "loss_rate": item['loss_rate']
        })
    
    conn.close()
    return results

if __name__ == "__main__":
    # 테스트: FG001을 100개 생산할 때 필요한 자재 계산
    order_qty = 100
    needed_materials = explode_bom('FG001', order_qty)
    
    print(f"\n[생산지시: FG001, 수량: {order_qty}]")
    print("-" * 50)
    for m in needed_materials:
        print(f"품목: {m['material_code']} | 필요수량: {m['needed_qty']} {m['unit']} (로스율: {m['loss_rate']*100}%)")
