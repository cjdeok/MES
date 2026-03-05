import pandas as pd
import sqlite3
import os
import glob

# 경로 정의
base_dir = r'c:\Users\ENS-1000\Documents\Antigravity\MES'
tmp_dir = os.path.join(base_dir, '.tmp')
db_file = os.path.join(base_dir, 'mes_database.db')

def register_to_sqlite():
    # .tmp 폴더에서 xlsx 파일 찾기 (이름에 '원료'가 포함된 파일)
    files = glob.glob(os.path.join(tmp_dir, "*.xlsx"))
    excel_file = None
    for f in files:
        if "원료" in f or "DB" in f:
            excel_file = f
            break
            
    if not excel_file:
        print(f"엑셀 파일을 찾을 수 없습니다. (.tmp 폴더 확인)")
        return

    print(f"엑셀 파일 읽는 중: {os.path.basename(excel_file)}")
    
    # 1. 엑셀 데이터 로드
    try:
        df = pd.read_excel(excel_file)
        df.columns = [c.strip() for c in df.columns]
        
        mapping = {
            '제품명': 'product_name',
            '코드번호': 'item_code',
            'Lot No.': 'lot_no',
            '입고/출고': 'transaction_type',
            '사용일자': 'transaction_date',
            '사용목적': 'purpose',
            '수량': 'quantity'
        }
        df = df.rename(columns=mapping)
        
        # 날짜 형식 변환
        if 'transaction_date' in df.columns:
            df['transaction_date'] = df['transaction_date'].dt.strftime('%Y-%m-%d') if pd.api.types.is_datetime64_any_dtype(df['transaction_date']) else df['transaction_date'].astype(str)
        
        # 문자열 내 포함된 개행문자(\n, \r) 등을 공백으로 처리하여 데이터 정제
        df = df.map(lambda x: " ".join(str(x).split()) if isinstance(x, str) else x)

        print(f"데이터 로드 완료: {len(df)} 행")
        
    except Exception as e:
        print(f"엑셀 로드 실패: {e}")
        return

    # 2. SQLite 연결 및 테이블 생성
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS raw_materials")
        
        cursor.execute("""
            CREATE TABLE raw_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT,
                item_code TEXT,
                lot_no TEXT,
                transaction_type TEXT,
                transaction_date TEXT,
                purpose TEXT,
                quantity REAL
            )
        """)
        
        # 3. 데이터 삽입
        df.to_sql('raw_materials', conn, if_exists='append', index=False)
        
        conn.commit()
        print(f"데이터베이스 등록 완료: {db_file}")
        
        cursor.execute("SELECT COUNT(*) FROM raw_materials")
        count = cursor.fetchone()[0]
        print(f"최종 등록된 행 수: {count}")
        
    except Exception as e:
        print(f"데이터베이스 등록 실패: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    register_to_sqlite()
