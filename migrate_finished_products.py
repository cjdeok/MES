import sqlite3
import pandas as pd
import os

BASE_DIR = r'c:\Users\ENS-1000\Documents\Antigravity\MES'
DB_FILE = os.path.join(BASE_DIR, 'mes_database.db')
XLSX_FILE = os.path.join(BASE_DIR, '.tmp', 'Finished Product(2026.02.13).xlsx')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finished_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT,
            product_name TEXT,
            lot_no TEXT,
            transaction_type TEXT,
            transaction_date TEXT,
            expire_date TEXT,
            quantity_kit REAL,
            destination TEXT,
            qc_info TEXT,
            remark TEXT
        )
    ''')
    # 기존 데이터가 있다면 초기화 (테스트용)
    cursor.execute('DELETE FROM finished_products')
    conn.commit()
    conn.close()

def migrate_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. 입고 시트 파싱
    print("--- 입고 시트 파싱 중 ---")
    df_in = pd.read_excel(XLSX_FILE, sheet_name='입고', header=None)
    # 실제 데이터는 index 3(4행)부터 시작
    for i, row in df_in.iterrows():
        if i < 3: continue
        
        # 값이 비어있으면 스킵
        if pd.isna(row.get(0)) and pd.isna(row.get(1)) and pd.isna(row.get(2)):
            continue
            
        product_code = str(row.get(1, '')).strip() if pd.notna(row.get(1)) else ''
        product_name = str(row.get(2, '')).strip() if pd.notna(row.get(2)) else ''
        lot_no = str(row.get(3, '')).strip() if pd.notna(row.get(3)) else ''
        
        if lot_no == '23BCEPP-001':
            product_code = 'BCEPP'
            
        if not lot_no or not product_code or product_code == '제품코드':
            continue
            
        # 날짜 처리 (입고일/제조일: index 4, 유효기간: index 5)
        tx_date = str(row.get(4, '')).strip()[:10] if pd.notna(row.get(4)) else ''
        exp_date = str(row.get(5, '')).strip()[:10] if pd.notna(row.get(5)) else ''
        
        # 수량 (Kit 기준: index 6)
        qty = 0.0
        try:
            if pd.notna(row.get(6)):
                qty = float(row.get(6, 0))
        except ValueError:
            pass
            
        qc_info = str(row.get(10, '')).strip() if pd.notna(row.get(10)) else ''
        remark = str(row.get(11, '')).strip() if pd.notna(row.get(11)) else ''

        cursor.execute('''
            INSERT INTO finished_products 
            (product_code, product_name, lot_no, transaction_type, transaction_date, expire_date, quantity_kit, destination, qc_info, remark)
            VALUES (?, ?, ?, '완제품입고', ?, ?, ?, '', ?, ?)
        ''', (product_code, product_name, lot_no, tx_date, exp_date, qty, qc_info, remark))

    # 2. 출고 시트 파싱
    print("--- 출고 시트 파싱 중 ---")
    df_out = pd.read_excel(XLSX_FILE, sheet_name='출고', header=None)
    for i, row in df_out.iterrows():
        if i < 3: continue  # 출고 시트 헤더(0~2행) 건너뜀, 데이터는 3행부터 시작
        
        # 값이 비어있으면 스킵 (Column B, C, D)
        if pd.isna(row.get(1)) and pd.isna(row.get(2)) and pd.isna(row.get(3)):
            continue
            
        product_code = str(row.get(1, '')).strip() if pd.notna(row.get(1)) else ''
        product_name = str(row.get(2, '')).strip() if pd.notna(row.get(2)) else ''
        lot_no = str(row.get(3, '')).strip() if pd.notna(row.get(3)) else ''
        
        if lot_no == '23BCEPP-001':
            product_code = 'BCEPP'
            
        if not lot_no or not product_code or product_code == '제품코드':
            continue
            
        # 출고일자 (index 6), 유효기간 (index 5)
        tx_date = str(row.get(6, '')).strip()[:10] if pd.notna(row.get(6)) else ''
        exp_date = str(row.get(5, '')).strip()[:10] if pd.notna(row.get(5)) else ''
        
        # 수량 (kit 기준: index 7)
        qty = 0.0
        try:
            if pd.notna(row.get(7)):
                qty = float(row.get(7, 0))
        except ValueError:
            pass
            
        # 출고처 (index 9)
        destination = str(row.get(9, '')).strip() if pd.notna(row.get(9)) else ''
        qc_info = str(row.get(12, '')).strip() if pd.notna(row.get(12)) else ''
        remark = str(row.get(13, '')).strip() if pd.notna(row.get(13)) else ''

        cursor.execute('''
            INSERT INTO finished_products 
            (product_code, product_name, lot_no, transaction_type, transaction_date, expire_date, quantity_kit, destination, qc_info, remark)
            VALUES (?, ?, ?, '완제품 출고', ?, ?, ?, ?, ?, ?)
        ''', (product_code, product_name, lot_no, tx_date, exp_date, qty, destination, qc_info, remark))

    conn.commit()
    conn.close()
    print("데이터 마이그레이션이 완료되었습니다.")

if __name__ == '__main__':
    print("1. 테이블 생성 및 초기화 중...")
    init_db()
    print("2. 엑셀 데이터 추출 및 DB 적재 시작...")
    migrate_data()
