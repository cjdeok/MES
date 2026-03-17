import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def setup_db():
    print("Connecting to Supabase Database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # 1. 테이블 생성 구문
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS facilities (
        id SERIAL PRIMARY KEY,
        management_team TEXT,
        location TEXT,
        status TEXT,
        facility_no TEXT,
        department TEXT,
        manager_primary TEXT,
        manager_secondary TEXT,
        facility_name TEXT,
        specification TEXT,
        manufacturer TEXT,
        serial_no TEXT,
        supplier TEXT,
        as_contact TEXT,
        purchase_date TEXT,
        purchase_price BIGINT,
        useful_life INTEGER
    );
    """
    
    try:
        print("Creating 'facilities' table if not exists...")
        cur.execute(create_table_sql)
        conn.commit()
        print("Table created successfully!")
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()
        return
    finally:
        cur.close()
        conn.close()

    # 2. 데이터 마이그레이션 (기존 migrate_facilities.py 로직 활용)
    from migrate_facilities import migrate
    print("Starting data migration...")
    migrate()

if __name__ == "__main__":
    setup_db()
