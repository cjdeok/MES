import os
import openpyxl
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 로드
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def import_validation_plan():
    file_path = r"c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\연간밸리데이션 계획 (2026).xlsx"
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active

    sb = get_supabase_client()
    
    # 기존 데이터 삭제 (필요 시)
    # sb.table('validation_plan').delete().neq('id', 0).execute()

    insert_data = []
    
    # 2행부터 데이터 시작 (1행은 헤더)
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[1]: # 대상 명칭이 없으면 건너뜀
            continue
            
        insert_data.append({
            'no': str(row[0]) if row[0] is not None else "",
            'target_name': str(row[1]) if row[1] is not None else "",
            'equipment_no': str(row[2]) if row[2] is not None else "",
            'validation_cycle': str(row[3]) if row[3] is not None else "",
            'safety_grade': str(row[4]) if row[4] is not None else "",
            'last_inspection_date': str(row[5]).strip() if row[5] is not None else "",
            'next_plan_date': str(row[6]).strip() if row[6] is not None else "",
            'suitability': str(row[7]) if row[7] is not None else "",
            'performer': str(row[8]) if row[8] is not None else "",
            'remark': str(row[9]) if row[9] is not None else ""
        })

    if insert_data:
        try:
            # 배치 인서트
            res = sb.table('validation_plan').insert(insert_data).execute()
            print(f"Successfully inserted {len(insert_data)} rows into validation_plan table.")
        except Exception as e:
            print(f"Error inserting data: {e}")
            # 테이블이 없을 경우 에러가 발생할 수 있음. 
            # 일반적인 경우 Supabase GUI에서 테이블을 생성해야 하지만, 
            # 여기서는 첫 인서트 시 테이블 구조가 자동 생성되지는 않으므로 
            # 테이블이 존재함을 전제로 함.
    else:
        print("No data to insert.")

if __name__ == "__main__":
    import_validation_plan()
