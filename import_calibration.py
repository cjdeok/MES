import pandas as pd
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def import_calibration():
    path = r'c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\생산팀 계측기 검교정 일자(26.01).xlsx'
    # Sheet1에서 데이터 로드
    df = pd.read_excel(path, sheet_name='Sheet1')
    
    # 2026년 예정일에 데이터가 있는 행만 추출 (또는 전체 데이터 인입 후 필터링)
    # 여기서는 전체 데이터를 인입하되 번호가 있는 행 위주로 처리
    df = df.dropna(subset=['번호'])
    
    print(f"Total rows to import: {len(df)}")
    
    data_to_insert = []
    for _, row in df.iterrows():
        # NaN 처리 및 데이터 매핑
        item = {
            "no": str(row.get('번호', '')).split('.')[0] if pd.notna(row.get('번호')) else '',
            "management_no": str(row.get('설비번호', '')) if pd.notna(row.get('설비번호')) else '',
            "grade": str(row.get('설비\n등급', '')) if pd.notna(row.get('설비\n등급')) else '',
            "instrument_name": str(row.get('장비명', '')) if pd.notna(row.get('장비명')) else '',
            "specification": str(row.get('모 델/\n제조번호', '')) if pd.notna(row.get('모 델/\n제조번호')) else '',
            "location": str(row.get('설치장소', '')) if pd.notna(row.get('설치장소')) else '',
            "manufacturer": str(row.get('제조회사', '')) if pd.notna(row.get('제조회사')) else '',
            "cycle": str(row.get('교정\n주기', '')) if pd.notna(row.get('교정\n주기')) else '',
            "last_calibration_date": str(row.get('검교정 일자\n(2025년)', '')) if pd.notna(row.get('검교정 일자\n(2025년)')) else '',
            "next_plan_date": str(row.get('검교정 일자\n(2026년 예정)', '')) if pd.notna(row.get('검교정 일자\n(2026년 예정)')) else '',
            "remark": str(row.get('비고', '')) if pd.notna(row.get('비고')) else ''
        }
        data_to_insert.append(item)
    
    # Supabase에 데이터 삽입 (기존 데이터 삭제 후 삽입하는 방식 권장)
    try:
        # 기존 내용 삭제 (필요한 경우)
        supabase.table("instrument_calibration").delete().neq("id", -1).execute()
        
        # 50개씩 끊어서 삽입
        for i in range(0, len(data_to_insert), 50):
            chunk = data_to_insert[i:i+50]
            supabase.table("instrument_calibration").insert(chunk).execute()
            print(f"Inserted chunk {i//50 + 1}")
            
        print("Successfully imported instrument calibration data.")
    except Exception as e:
        print(f"Error during import: {e}")

if __name__ == "__main__":
    import_calibration()
