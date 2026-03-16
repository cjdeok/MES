import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
import re

# .env 파일 로드
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def upload_data():
    file_path = r"c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\원료구매요청서.xlsx"
    if not os.path.exists(file_path):
        print(f"Error: File not found {file_path}")
        return

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
        return

    # Supabase 클라이언트 생성
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # 데이터 로드 (Sheet1)
        df = pd.read_excel(file_path, sheet_name='Sheet1')
        
        # 컬럼명 전처리: 공백 제거 및 소문자 변환
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # 특정 컬럼명 맵핑 (스키마와 일치)
        column_mapping = {
            'cat.no': 'cat_no',
            'e-mail': 'email'
        }
        df = df.rename(columns=column_mapping)
        
        # 날짜 데이터 형식 변환 (ISO format 문자열 또는 datetime 객체)
        if '작성일자' in df.columns:
            df['작성일자'] = pd.to_datetime(df['작성일자'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # 수치형 데이터 전처리 (NaN -> None)
        numeric_cols = ['수량', '단가', '금액', '실단가', '실입고량']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').where(pd.notnull(df[col]), None)

        # 데이터 정리 (NaN -> None)
        df = df.where(pd.notnull(df), None)
        
        # 딕셔너리 리스트로 변환 시 NaN 처리
        data = []
        for _, row in df.iterrows():
            record = {}
            for col, val in row.items():
                if pd.isna(val):
                    record[col] = None
                else:
                    record[col] = val
            data.append(record)
        
        print(f"Uploading {len(data)} rows to purchase_info table...")
        
        # Batch insert (500개씩)
        batch_size = 500
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            result = supabase.table("purchase_info").insert(batch).execute()
            print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} rows")
            
        print("Upload completed successfully!")

    except Exception as e:
        print(f"Error during upload: {e}")

if __name__ == "__main__":
    upload_data()
