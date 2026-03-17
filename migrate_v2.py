import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def migrate_v2():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    excel_path = r'c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\facilities.xlsx'
    
    print(f"Reading {excel_path}...")
    df = pd.read_excel(excel_path)
    
    # 엑셀 실제 컬럼명 기반 정확한 매핑
    mapping = {
        '관리팀': 'management_team',
        '설치장소': 'location',
        '사용유무': 'status',
        '설비번호': 'facility_no',
        '장비명': 'facility_name',
        '장비명분류': 'equipment_class',
        '설비등급': 'facility_grade',
        '검교정': 'calibration',
        '밸리데이션': 'validation',
        '부서': 'department',
        '정': 'manager_primary',
        '부': 'manager_secondary',
        '제작회사': 'manufacturer',
        '모델/제조번호': 'serial_no',
        '구입사': 'supplier',
        'A/S  연락처': 'as_contact',
        '구입일': 'purchase_date',
        '구입가\n(단위 : 원)': 'purchase_price',
        '내용연수': 'useful_life'
    }
    
    # 존재하는 컬럼만 필터링
    present_mapping = {k: v for k, v in mapping.items() if k in df.columns}
    final_df = df[list(present_mapping.keys())].rename(columns=present_mapping)
    
    # 전처리
    if 'purchase_date' in final_df.columns:
        final_df['purchase_date'] = pd.to_datetime(final_df['purchase_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    for int_col in ['purchase_price', 'useful_life']:
        if int_col in final_df.columns:
            final_df[int_col] = pd.to_numeric(final_df[int_col], errors='coerce').fillna(0).astype(int)
    
    final_df = final_df.where(pd.notnull(final_df), None)
    records = final_df.to_dict('records')
    
    print(f"Uploading {len(records)} records (V2)...")
    try:
        # 기존 데이터 삭제 (테이블을 재생성하므로 안전)
        supabase.table('facilities').delete().neq('id', 0).execute()
        
        chunk_size = 50
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            supabase.table('facilities').insert(chunk).execute()
            print(f"Uploaded chunk {i//chunk_size + 1}/{(len(records)-1)//chunk_size + 1}")
        
        print("Migration V2 completed successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate_v2()
