import os
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_allocation_with_threshold(kit_qty, mat_code):
    # This script simulates the logic NOW in app.py
    THRESHOLD = 0.0001
    
    # 1. BOM 소요량 조회
    res_bom = sb.table('kit_bom').select('material_code, material_name, usage_qty').eq('kit_qty', kit_qty).eq('material_code', mat_code).execute()
    item = res_bom.data[0]
    required_qty = item['usage_qty']
    print(f"Required for {mat_code}: {required_qty}")

    # 2. raw_materials 재고 조회
    res_raw = sb.table('raw_materials').select('item_code, lot_no, transaction_type, quantity').eq('item_code', mat_code).execute()
    lot_stocks = defaultdict(float)
    for r in res_raw.data:
        key = (r['item_code'], r['lot_no'])
        if r['transaction_type'] == '입고':
            lot_stocks[key] += (r['quantity'] or 0)
        else:
            lot_stocks[key] -= (r['quantity'] or 0)

    # MANUALLY ADD A TINY STOCK LOT FOR TESTING
    lot_stocks[(mat_code, 'TINY_LOT')] = 0.000001
    print("\nStocks (including test TINY_LOT):")
    for key, stock in lot_stocks.items():
        print(f"  Lot: {key[1]}, Stock: {stock}")

    # 가용 재고 목록 생성 (WITH THRESHOLD)
    available_lots = []
    for (itm_cd, lot_no), stock in lot_stocks.items():
        if itm_cd == mat_code and stock > THRESHOLD:
            available_lots.append({
                'lot_no': lot_no,
                'current_stock': stock
            })
    
    print("\nAvailable Lots (stock > {}):".format(THRESHOLD))
    for lot in available_lots:
        print(f"  Lot: {lot['lot_no']}, Stock: {lot['current_stock']}")

    if any(l['lot_no'] == 'TINY_LOT' for l in available_lots):
        print("\nFAILURE: TINY_LOT was included even though it's below threshold!")
    else:
        print("\nSUCCESS: TINY_LOT was correctly excluded.")

if __name__ == '__main__':
    test_allocation_with_threshold(56, 'CMA007')
