import os
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

def simulate_allocation(kit_qty, mat_code):
    # 1. BOM 소요량 조회
    res_bom = sb.table('kit_bom').select('material_code, material_name, usage_qty').eq('kit_qty', kit_qty).eq('material_code', mat_code).execute()
    if not res_bom.data:
        print(f"No BOM entry for {mat_code} at kit_qty {kit_qty}")
        return
    item = res_bom.data[0]
    required_qty = item['usage_qty']
    print(f"Required for {mat_code}: {required_qty}")

    # 2. material_info (expire_date 등)
    res_info = sb.table('material_info').select('item_code, lot_no, receive_date, expire_date').eq('item_code', mat_code).execute()
    info_map = {}
    for r in res_info.data:
        info_map[(r['item_code'], r['lot_no'])] = {
            'receive_date': r['receive_date'],
            'expire_date': r['expire_date']
        }

    # 3. raw_materials 재고 조회
    res_raw = sb.table('raw_materials').select('item_code, lot_no, transaction_type, quantity').eq('item_code', mat_code).execute()
    lot_stocks = defaultdict(float)
    lot_in_qty = defaultdict(float)
    for r in res_raw.data:
        key = (r['item_code'], r['lot_no'])
        if r['transaction_type'] == '입고':
            lot_stocks[key] += (r['quantity'] or 0)
            lot_in_qty[key] += (r['quantity'] or 0)
        else:
            lot_stocks[key] -= (r['quantity'] or 0)

    print("\nCurrent Stocks for lots of {}:".format(mat_code))
    for key, stock in lot_stocks.items():
        print(f"  Lot: {key[1]}, Stock: {stock}")

    # 가용 재고 목록 생성
    available_lots = []
    for (itm_cd, lot_no), stock in lot_stocks.items():
        if itm_cd == mat_code and stock > 0:
            info = info_map.get((itm_cd, lot_no), {})
            available_lots.append({
                'lot_no': lot_no,
                'current_stock': stock,
                'rec_date': info.get('receive_date') or '9999-12-31',
                'exp_date': info.get('expire_date') or '9999-12-31'
            })
    
    # 정렬 (간략화)
    available_lots.sort(key=lambda x: (x['exp_date'], x['rec_date'], x['lot_no']))

    allocated_lots = []
    remaining_to_allocate = required_qty
    
    print("\nAllocating Lots:")
    for lot in available_lots:
        if remaining_to_allocate <= 0:
            break
        alloc_qty = min(remaining_to_allocate, lot['current_stock'])
        print(f"  Picked Lot: {lot['lot_no']}, Stock: {lot['current_stock']}, Allocating: {alloc_qty}")
        allocated_lots.append({
            'lot_no': lot['lot_no'],
            'allocated_qty': round(alloc_qty, 4)
        })
        remaining_to_allocate -= alloc_qty
        
    shortage_qty = round(max(0, remaining_to_allocate), 4)
    status = 'success' if shortage_qty == 0 else 'shortage'
    print(f"\nResult: shortage_qty={shortage_qty}, status={status}")

if __name__ == '__main__':
    simulate_allocation(56, 'CMA007')
