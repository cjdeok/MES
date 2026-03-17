import os
import re

# 업데이트할 파일 목록 (절대 경로로 변환하여 처리)
base_dir = r"c:\Users\ENS-1000\Documents\Antigravity\MES"
files = [
    os.path.join(base_dir, "index.html"),
    os.path.join(base_dir, "web", "templates", "calibration.html"),
    os.path.join(base_dir, "web", "templates", "finished_product.html"),
    os.path.join(base_dir, "web", "templates", "inventory.html"),
    os.path.join(base_dir, "web", "templates", "material_info.html"),
    os.path.join(base_dir, "web", "templates", "producible.html"),
    os.path.join(base_dir, "web", "templates", "production.html"),
    os.path.join(base_dir, "web", "templates", "purchase_dashboard.html"),
    os.path.join(base_dir, "web", "templates", "raw_material.html"),
    os.path.join(base_dir, "web", "templates", "upload_receiving.html"),
    os.path.join(base_dir, "web", "templates", "upload_usage.html"),
    os.path.join(base_dir, "web", "templates", "validation.html")
]

new_nav = """            <a href="/facilities" class="nav-btn">
                <i class="fa-solid fa-tools"></i>
                설비 관리
            </a>"""

for full_path in files:
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        continue
    
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 이미 설비 관리 메뉴가 있는지 확인
    if '/facilities' in content:
        print(f"Already updated: {os.path.basename(full_path)}")
        continue
    
    # '구매 대시보드' <a> 태그를 찾아 그 뒤에 삽입
    # re.DOTALL을 사용하여 여러 줄에 걸친 <a> 태그 매칭
    pattern = r'(<a href="/purchase-dashboard".*?</a>)'
    if re.search(pattern, content, flags=re.DOTALL):
        # \1은 매칭된 '구매 대시보드' <a> 태그 전체를 의미함
        new_content = re.sub(pattern, r'\1\n' + new_nav, content, flags=re.DOTALL)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated: {os.path.basename(full_path)}")
    else:
        print(f"Target pattern not found in: {os.path.basename(full_path)}")
