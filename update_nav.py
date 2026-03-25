import os
import glob

base_dir = r'c:\Users\ENS-1000\Documents\Antigravity\MES'

html_files = glob.glob(os.path.join(base_dir, 'web', 'templates', '*.html'))
html_files.append(os.path.join(base_dir, 'index.html'))

target_string = 'MO 생성</a>'
replacement_string = 'MO 생성</a>\n                    <a href="/bom-calculator"><i class="fa-solid fa-sitemap"></i>BOM 계산기</a>'

count = 0
for filepath in html_files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if target_string in content and '<a href="/bom-calculator">' not in content:
            new_content = content.replace(target_string, replacement_string)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {os.path.basename(filepath)}")
            count += 1

print(f"Total updated: {count} files")
