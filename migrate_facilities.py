import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate():
    excel_path = r'c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\facilities.xlsx'
    print(f"Reading {excel_path}...")
    
    # 엑셀 파일 읽기
    df = pd.read_excel(excel_path)
    
    # 컬럼 매핑 (엑셀 컬럼 이름 -> DB 필드 이름)
    # 컬럼 순서: ['관리팀', '설치장소', '사용유무', '관리번호', '부서', '정', '부', '설비명', '규격', '제작사', '제조 번호', '구입사', 'A/S  연락처', '구입일', '구입가\n(단위 : 원)', '내용연수']
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
    
    # 데이터 전처리
    # 날짜 처리
    if 'purchase_date' in df.columns:
        df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.strftime('%Y-%m-%d')
    
    # 숫자형 처리 (NaN 처리 포함)
    df['purchase_price'] = pd.to_numeric(df['purchase_price'], errors='coerce').fillna(0).astype(int)
    df['useful_life'] = pd.to_numeric(df['useful_life'], errors='coerce').fillna(0).astype(int)
    
    # NaN 문자열 교체
    df = df.where(pd.notnull(df), None)
    
    records = df.to_dict('records')
    
    supabase = get_supabase_client()
    
    print(f"Uploading {len(records)} records to Supabase...")
    
    # Batch insert (ID 수동 할당 제외하여 SERIAL 작동 유도)
    try:
        # 기존 데이터 삭제 (중복 방지용 선택 사항, 여기서는 추가)
        # supabase.table('facilities').delete().neq('id', 0).execute()
        
        res = supabase.table('facilities').insert(records).execute()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
