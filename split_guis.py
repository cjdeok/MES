import os

base_dir = r"c:\Users\ENS-1000\Documents\Antigravity\MES"
bom_html_path = os.path.join(base_dir, "web", "templates", "bom_calculator.html")
prod_html_path = os.path.join(base_dir, "web", "templates", "production.html")

# Read the current bom_calculator.html, which is the "advanced" one
with open(bom_html_path, "r", encoding="utf-8") as f:
    adv_html = f.read()

# Make it production.html
# 1. Point the API to /api/generate_bom_allocated
adv_prod = adv_html.replace("fetch('/api/generate_bom'", "fetch('/api/generate_bom_allocated'")
# 2. Fix the navigation
# First, remove `class="active"` from /bom-calculator
adv_prod = adv_prod.replace('<a href="/bom-calculator" class="active">', '<a href="/bom-calculator">')
# Next, add `active` to production
adv_prod = adv_prod.replace('<a href="/production" class="nav-btn">', '<a href="/production" class="nav-btn active">')
adv_prod = adv_prod.replace('<a href="/production"><i class="fa-solid fa-calculator"></i>생산 지시</a>', '<a href="/production" class="active"><i class="fa-solid fa-calculator"></i>생산 지시</a>')

with open(prod_html_path, "w", encoding="utf-8") as f:
    f.write(adv_prod)


# For bom_calculator.html, we need to revert it to the SIMPLE version.
# Let's write the SIMPLE version.
simple_template = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>생산 관리 - BOM 전개 계산기</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .form-control {
            width: 100%;
            padding: 0.8rem 1rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            background: rgba(0, 0, 0, 0.2);
            color: var(--text-main);
            font-size: 1rem;
            font-family: inherit;
        }
        .form-control:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
        .action-btn { background: var(--primary); color: white; border: none; padding: 0 2rem; border-radius: var(--radius-md); font-weight: 500; font-size: 1rem; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 0.5rem; height: 48px; }
        .action-btn:hover { background: #2563eb; transform: translateY(-1px); }
        .input-group-container { display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 1.5rem; }
        .input-group-container label { font-size: 0.9rem; color: var(--text-muted); font-weight: 500; }
        .level-section { margin-bottom: 24px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: var(--radius-lg); overflow: hidden; }
        .level-header { background-color: rgba(255, 255, 255, 0.05); padding: 12px 16px; font-weight: 600; border-bottom: 1px solid rgba(255, 255, 255, 0.08); display: flex; justify-content: space-between; color: #fff; }
        .highlight { color: #10b981; font-weight: 700; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 16px; text-align: left; font-size: 0.9rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
        th { background-color: rgba(255, 255, 255, 0.02); color: var(--text-muted); font-weight: 600; }
        .result-area { display: none; }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- HEADER PLACEHOLDER -->
        <main>
            <section class="control-panel glass-panel">
                <h2><i class="fa-solid fa-sitemap"></i> BOM 전개 계산기 (Original)</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="input-group-container">
                        <label>수식 마스터 파일 선택</label>
                        <select id="formulaFileSelect" class="form-control"><option value="">파일 목록을 불러오는 중...</option></select>
                    </div>
                    <div class="input-group-container">
                        <label>목표 생산량 (Level 0)</label>
                        <div style="display: flex; gap: 0.5rem;">
                            <input type="number" id="targetQty" class="form-control" placeholder="수량을 입력하세요" min="1" value="256" />
                            <button onclick="calculateBOM()" class="action-btn" style="white-space: nowrap;"><i class="fa-solid fa-wand-magic-sparkles"></i> 분석</button>
                        </div>
                    </div>
                </div>
            </section>
            
            <div id="spinner" class="hidden" style="text-align: center; padding: 40px; color: var(--text-muted); display: none;">
                <div class="spinner"></div><p>BOM 전개 중...</p>
            </div>
            
            <div id="emptyState" class="empty-state">
                <i class="fa-solid fa-clipboard-check"></i><p>수식 파일과 목표 생산량을 설정하고 분석 버튼을 눌러주세요.</p>
            </div>
            
            <section id="resultArea" class="results-section result-area">
                <div class="history-panel glass-panel">
                    <div id="summaryInfo" style="margin-bottom: 20px; font-weight: 500; color: var(--text-muted);"></div>
                    <div class="level-section">
                        <div class="level-header">Level 1 (포장/완제품) <span id="l1Count"></span></div>
                        <div class="table-container">
                            <table>
                                <thead><tr><th style="width: 25%;">상위 Lot</th><th style="width: 30%;">생산LOT</th><th style="width: 25%;">명칭 / 구성품</th><th style="width: 10%;">소요량</th><th style="width: 10%;">단위</th></tr></thead>
                                <tbody id="l1Table"></tbody>
                            </table>
                        </div>
                    </div>
                    <div class="level-section">
                        <div class="level-header">Level 2 (반제품 제조) <span id="l2Count"></span></div>
                        <div class="table-container">
                            <table>
                                <thead><tr><th style="width: 25%;">상위 Lot</th><th style="width: 30%;">생산LOT</th><th style="width: 25%;">명칭 / 구성품</th><th style="width: 10%;">소요량</th><th style="width: 10%;">단위</th></tr></thead>
                                <tbody id="l2Table"></tbody>
                            </table>
                        </div>
                    </div>
                    <div class="level-section">
                        <div class="level-header">Level 3 (하위 조제) <span id="l3Count"></span></div>
                        <div class="table-container">
                            <table>
                                <thead><tr><th style="width: 25%;">상위 Lot</th><th style="width: 30%;">생산LOT</th><th style="width: 25%;">명칭 / 구성품</th><th style="width: 10%;">소요량</th><th style="width: 10%;">단위</th></tr></thead>
                                <tbody id="l3Table"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    </div>
    <script>
        fetch('/api/lots/bom').then(res => res.json()).then(data => {
            const select = document.getElementById('formulaFileSelect'); select.innerHTML = '';
            if(data && data.length > 0) { data.forEach(item => { const opt = document.createElement('option'); opt.value = item.filename; opt.textContent = item.filename; if(item.filename.includes('BCE01_BOM')) opt.selected = true; select.appendChild(opt); }); } else { select.innerHTML = '<option value="">가용한 파일 없음</option>'; }
        }).catch(err => { select.innerHTML = '<option value="">오류 발생</option>'; });

        function calculateBOM() {
            const formulaFile = document.getElementById('formulaFileSelect').value;
            const targetQty = document.getElementById('targetQty').value;
            document.getElementById('emptyState').style.display = 'none'; document.getElementById('resultArea').style.display = 'none'; document.getElementById('spinner').style.display = 'block';

            fetch('/api/generate_bom', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ formula_file: formulaFile, target_qty: targetQty })
            }).then(res => res.json()).then(data => {
                document.getElementById('spinner').style.display = 'none';
                if (data.error) { alert(data.error); return; }
                renderResults(data); document.getElementById('resultArea').style.display = 'block';
            }).catch(err => { document.getElementById('spinner').style.display = 'none'; alert("오류가 발생했습니다."); });
        }

        function renderResults(data) {
            document.getElementById('summaryInfo').innerText = `파일 [${data.level0.제품명.replace('전개 소스: ', '')}]을(를) 사용. (목표수량: ${data.level0.목표수량})`;
            renderTable('l1Table', 'l1Count', data.level1); renderTable('l2Table', 'l2Count', data.level2); renderTable('l3Table', 'l3Count', data.level3);
        }

        function renderTable(tableId, countId, items) {
            const tbody = document.getElementById(tableId); tbody.innerHTML = '';
            document.getElementById(countId).innerText = `${items.length} 항목`;
            if (items.length === 0) { tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">해당 데이터가 없습니다.</td></tr>`; return; }

            items.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${item['상위Lot']}</td>
                    <td style="font-weight: 600; color: var(--primary);">${item['생산Lot'] || ''}</td>
                    <td><span style="font-size: 0.85rem; color: var(--text-muted);">${item['명칭 / 구성품']}</span></td>
                    <td class="highlight">${item['계산된_소요량'].toLocaleString()}</td>
                    <td><span style="font-size:0.75rem; color:gray">${item['단위']}</span></td>
                `;
                tbody.appendChild(tr);
            });
        }
    </script>
</body>
</html>"""

# Now extract the header from the OLD advanced HTML to ensure the nav links have the right "active" class
import re
match = re.search(r'(?s)<header class="top-header">.*?</header>', adv_html)
header_str = match.group(0) if match else "<!-- FAIL -->"
# Here "bom-calculator" should be active, which it already was in adv_html!
final_simple_html = simple_template.replace('<!-- HEADER PLACEHOLDER -->', header_str)

with open(bom_html_path, "w", encoding="utf-8") as f:
    f.write(final_simple_html)

print("split_guis done")
