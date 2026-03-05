import sqlite3
import os

db_file = r'c:\Users\ENS-1000\Documents\Antigravity\MES\mes_database.db'

def setup_bom_system():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 1. BOM 테이블 생성
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bom (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_item_code TEXT NOT NULL,  -- 완제품 또는 반제품 코드
        child_item_code TEXT NOT NULL,   -- 투입되는 원부자재/반제품 코드
        qty_per REAL NOT NULL,           -- 원단위 (생산 1단위당 필요량)
        unit TEXT,                       -- 단위
        loss_rate REAL DEFAULT 0,        -- 로스율 (0.05 = 5%)
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. 샘플 데이터 입력 (예제: 완제품 FG001을 만들기 위해 BCM001 2개, BCM002 1.5개 필요)
    sample_bom = [
        ('FG001', 'BCM001', 2.0, 'ea', 0.0),
        ('FG001', 'BCM002', 1.5, 'kg', 0.05) # 로스율 5% 적용 예시
    ]
    
    cursor.executemany("""
    INSERT INTO bom (parent_item_code, child_item_code, qty_per, unit, loss_rate)
    VALUES (?, ?, ?, ?, ?)
    """, sample_bom)
    
    conn.commit()
    conn.close()
    print("BOM 테이블 생성 및 샘플 데이터 등록 완료")

if __name__ == "__main__":
    setup_bom_system()
