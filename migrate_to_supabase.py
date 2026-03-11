import sqlite3
import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def migrate_data():
    # 1. SQLite 연결
    sqlite_conn = sqlite3.connect('mes_database.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 2. Supabase REST 클라이언트 연결
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    tables_cols = {
        'raw_materials': ['id','product_name','item_code','lot_no','transaction_type','transaction_date','purpose','quantity'],
        'material_info': ['id','item_code','product_name','cat_no','lot_no','purchase_qty','manufacturer','vendor','receive_date','qc_date','expire_date','po_no'],
        'kit_bom': ['id','material_code','material_name','kit_qty','usage_qty'],
        'finished_products': ['id','product_code','product_name','lot_no','transaction_type','transaction_date','expire_date','quantity_kit','destination','qc_info','remark']
    }
    
    for table, cols in tables_cols.items():
        print(f"\n--- Migrating: {table} ---")
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"  No data for {table}.")
            continue
        
        # dict 변환
        data = []
        for row in rows:
            d = {}
            for col in cols:
                val = row[col] if col in row.keys() else None
                # None 변환
                if val is None:
                    d[col] = None
                else:
                    d[col] = val
            data.append(d)
        
        # batch insert (500개씩 나누어)
        batch_size = 500
        total = len(data)
        for i in range(0, total, batch_size):
            batch = data[i:i+batch_size]
            try:
                result = supabase.table(table).insert(batch).execute()
                print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} rows")
            except Exception as e:
                print(f"  Error in batch {i//batch_size + 1}: {e}")
        
        # 시퀀스 조정 (id 자동증가 값 맞추기)
        try:
            max_id = max(d['id'] for d in data)
            supabase.rpc('setval_seq', {'table_name': table, 'val': max_id}).execute()
        except:
            pass  # RPC가 없으면 무시
            
        print(f"  Total: {total} rows migrated for {table}")
    
    sqlite_conn.close()
    print("\n=== Migration Complete! ===")

if __name__ == '__main__':
    migrate_data()
