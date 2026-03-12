import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

sql = """
CREATE TABLE IF NOT EXISTS public.instrument_calibration (
    id SERIAL PRIMARY KEY,
    no TEXT,
    management_no TEXT,
    grade TEXT,
    instrument_name TEXT,
    specification TEXT,
    location TEXT,
    manufacturer TEXT,
    cycle TEXT,
    last_calibration_date TEXT,
    next_plan_date TEXT,
    remark TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

try:
    # rpc를 통한 SQL 실행은 수동으로 생성된 함수가 있어야 하므로, 
    # 테이블 인입 스크립트를 먼저 실행해보고 에러가 나면 직접 생성을 안내하거나 
    # 다른 방식을 시도합니다.
    # 여기서는 포스트그레스트에서 테이블이 없으면 create_client 이후 
    # 첫 insert 시점에 에러가 날 것이므로, 
    # 관리자 또는 사용자가 직접 SQL Editor에서 실행하는 것이 가장 확실합니다.
    print("Please run the following SQL in your Supabase SQL Editor:")
    print(sql)
except Exception as e:
    print(f"Error: {e}")
