import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def migrate_direct():
    excel_path = r'c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\facilities.xlsx'
    print(f"Reading {excel_path}...")
    df = pd.read_excel(excel_path)
    
    mapping = {
        '관리팀': 'management_team',
        '설치장소': 'location',
        '사용유무': 'status',
        '관리번호': 'facility_no',
        '부서': 'department',
        '정': 'manager_primary',
        '부': 'manager_secondary',
        '설비명': 'facility_name',
        '규격': 'specification',
        '제작사': 'manufacturer',
        '제조 번호': 'serial_no',
        '구입사': 'supplier',
        'A/S  연락처': 'as_contact',
        '구입일': 'purchase_date',
        '구입가\n(단위 : 원)': 'purchase_price',
        '내용연수': 'useful_life'
    }
    df = df.rename(columns=mapping)
    
    # Preprocessing
    if 'purchase_date' in df.columns:
        df['purchase_date'] = pd.to_datetime(df['purchase_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df['purchase_price'] = pd.to_numeric(df['purchase_price'], errors='coerce').fillna(0).astype(int)
    df['useful_life'] = pd.to_numeric(df['useful_life'], errors='coerce').fillna(0).astype(int)
    df = df.where(pd.notnull(df), None)
    
    records = df.to_dict('records')
    
    print(f"Connecting to DB and uploading {len(records)} records...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Clear existing data to avoid duplicates since we're re-running
        cur.execute("DELETE FROM facilities;")
        
        insert_query = """
        INSERT INTO facilities (
            management_team, location, status, facility_no, department, 
            manager_primary, manager_secondary, facility_name, specification, 
            manufacturer, serial_no, supplier, as_contact, purchase_date, 
            purchase_price, useful_life
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for r in records:
            cur.execute(insert_query, (
                r.get('management_team'), r.get('location'), r.get('status'), r.get('facility_no'),
                r.get('department'), r.get('manager_primary'), r.get('manager_secondary'),
                r.get('facility_name'), r.get('specification'), r.get('manufacturer'),
                r.get('serial_no'), r.get('supplier'), r.get('as_contact'), r.get('purchase_date'),
                r.get('purchase_price'), r.get('useful_life')
            ))
        
        conn.commit()
        print("Migration via psycopg2 completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate_direct()
