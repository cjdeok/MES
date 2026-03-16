import os
import psycopg2
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

import re
import socket

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # 모든 공백 및 제어 문자 제거
    DATABASE_URL = re.sub(r'[\s\x00-\x1f\x7f]', '', DATABASE_URL)

def setup_table():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in .env")
        return

    host_port_db = DATABASE_URL.split('@')[-1]
    host = host_port_db.split(':')[0]
    print(f"Testing connection to host: '{host}'")
    
    try:
        ip = socket.gethostbyname(host)
        print(f"Resolved IP: {ip}")
    except Exception as e:
        print(f"DNS Resolution Error for '{host}': {e}")
        return

    try:
        # DB 연결
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # SQL 파일 읽기
        sql_file_path = os.path.join(os.path.dirname(__file__), "purchase_schema.sql")
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # SQL 실행
        print("Executing SQL to create purchase_info table...")
        cur.execute(sql)
        conn.commit()
        print("Table purchase_info created successfully!")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_table()
