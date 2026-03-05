import pandas as pd
import sqlite3
import os

# 파일 경로 정의
base_dir = r'c:\Users\ENS-1000\Documents\Antigravity\MES'
excel_file = os.path.join(base_dir, '.tmp', 'material_infomation.xlsx')
db_file = os.path.join(base_dir, 'mes_database.db')

def register_material_info():
    if not os.path.exists(excel_file):
        print(f"엑셀 파일을 찾을 수 없습니다: {excel_file}")
        return

    print(f"엑셀 파일 읽는 중: {os.path.basename(excel_file)}")
    
    # 1. 엑셀 데이터 로드
    try:
        df = pd.read_excel(excel_file)
        
        # 컬럼 매핑
        # 원본: ['코드번호', '제 품 명', 'Cat. No.', 'Lot No.', '구 입 량', '제 조 사', '구 매 처', '입 고 일', 'Q.C.일', '유효기간', '구매요청서 문서 번호']
        mapping = {
            '코드번호': 'item_code',
            '제 품 명': 'product_name',
            'Cat. No.': 'cat_no',
            'Lot No.': 'lot_no',
            '구 입 량': 'purchase_qty',
            '제 조 사': 'manufacturer',
            '구 매 처': 'vendor',
            '입 고 일': 'receive_date',
            'Q.C.일': 'qc_date',
            '유효기간': 'expire_date',
            '구매요청서 문서 번호': 'po_no'
        }
        df = df.rename(columns=mapping)
        
        # 날짜 컬럼 형식 변환 (YYYY-MM-DD 유지)
        date_cols = ['receive_date', 'qc_date', 'expire_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].dt.strftime('%Y-%m-%d') if pd.api.types.is_datetime64_any_dtype(df[col]) else df[col].astype(str)

        # 문자열 내 줄바꿈 및 특수 공백 평탄화 처리
        df = df.map(lambda x: " ".join(str(x).split()) if isinstance(x, str) else x)
        
        print(f"데이터 로드 완료: {len(df)} 행")
        
    except Exception as e:
        print(f"엑셀 로드 실패: {e}")
        return

    # 2. SQLite 연결 및 테이블 생성
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS material_info")
        
        cursor.execute("""
            CREATE TABLE material_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT,
                product_name TEXT,
                cat_no TEXT,
                lot_no TEXT,
                purchase_qty REAL,
                manufacturer TEXT,
                vendor TEXT,
                receive_date TEXT,
                qc_date TEXT,
                expire_date TEXT,
                po_no TEXT
            )
        """)
        
        # 3. 데이터 삽입
        df.to_sql('material_info', conn, if_exists='append', index=False)
        
        conn.commit()
        print(f"데이터베이스 등록 완료: {db_file}")
        
        cursor.execute("SELECT COUNT(*) FROM material_info")
        count = cursor.fetchone()[0]
        print(f"최종 등록된 상세정보 행 수: {count}")
        
    except Exception as e:
        print(f"데이터베이스 등록 실패: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    register_material_info()
