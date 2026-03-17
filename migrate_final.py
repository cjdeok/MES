import os
import pandas as pd
import time
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def migrate_robust():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    excel_path = r'c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\facilities.xlsx'
    print(f"Reading {excel_path}...")
    df = pd.read_excel(excel_path)
    
    # 엑셀에 실제로 존재하는 컬럼을 기반으로 매핑 시도
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
    
    # 존재하는 컬럼만 필터링하여 매핑 적용
    present_mapping = {k: v for k, v in mapping.items() if k in df.columns}
    print(f"Mapping present columns: {list(present_mapping.keys())}")
    
    final_df = df[list(present_mapping.keys())].rename(columns=present_mapping)
    
    # 전처리
    if 'purchase_date' in final_df.columns:
        final_df['purchase_date'] = pd.to_datetime(final_df['purchase_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    if 'purchase_price' in final_df.columns:
        final_df['purchase_price'] = pd.to_numeric(final_df['purchase_price'], errors='coerce').fillna(0).astype(int)
    
    if 'useful_life' in final_df.columns:
        final_df['useful_life'] = pd.to_numeric(final_df['useful_life'], errors='coerce').fillna(0).astype(int)
    
    final_df = final_df.where(pd.notnull(final_df), None)
    
    records = final_df.to_dict('records')
    print(f"Total records to upload: {len(records)}")
    
    # 업로드
    try:
        # 기존 데이터 삭제 (필요한 경우)
        # supabase.table('facilities').delete().neq('id', 0).execute()
        
        chunk_size = 50
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            supabase.table('facilities').insert(chunk).execute()
            print(f"Uploaded chunk {i//chunk_size + 1}/{(len(records)-1)//chunk_size + 1}")
        
        print("Migration successful via robust script!")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_robust()
