import os
import glob
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

import httpx
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# 타임아웃 설정을 위해 커스텀 httpx 클라이언트 생성
# httpx.Client(timeout=60.0) 처럼 설정할 수도 있으나, supabase-py 내부 구조에 맞춰 Client 설정
supabase: Client = create_client(url, key)
# 참고: supabase-py 0.1.0+ 버전에서는 별도의 타임아웃 설정이 필요할 수 있음
# 여기서는 단순 재호출로 해결될 가능성이 크므로 구조만 유지하고 재실행

BUCKET_NAME = "equipment-photos"
PHOTO_DIR = r"c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\equipment_photos"

def upload_photos():
    # 1. 버킷 확인 및 생성 (없을 경우)
    try:
        supabase.storage.get_bucket(BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' already exists.")
    except Exception:
        print(f"Creating bucket '{BUCKET_NAME}'...")
        supabase.storage.create_bucket(BUCKET_NAME, options={"public": True})

    # 2. 사진 파일 목록 가져오기
    photo_files = glob.glob(os.path.join(PHOTO_DIR, "*.*"))
    print(f"Found {len(photo_files)} photos in {PHOTO_DIR}")

    for file_path in photo_files:
        file_name = os.path.basename(file_path)
        
        # 파일 읽기
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        # 3. 업로드
        # content_type 설정 (확장자에 따라)
        ext = os.path.splitext(file_name)[1].lower()
        content_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"
        
        try:
            # upsert=True를 사용하여 기존 파일이 있으면 덮어씀
            res = supabase.storage.from_(BUCKET_NAME).upload(
                path=file_name,
                file=file_data,
                file_options={"cache-control": "3600", "upsert": "true", "content-type": content_type}
            )
            print(f"Successfully uploaded: {file_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Skipping (already exists): {file_name}")
            else:
                print(f"Error uploading {file_name}: {e}")

if __name__ == "__main__":
    upload_photos()
