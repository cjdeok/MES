import os
import re

base_dir = r"c:\Users\ENS-1000\Documents\Antigravity\MES"
bom_html_path = os.path.join(base_dir, "web", "templates", "bom_calculator.html")
prod_html_path = os.path.join(base_dir, "web", "templates", "production.html")

with open(prod_html_path, "r", encoding="utf-8") as f:
    prod_html = f.read()

match = re.search(r'(?s)<header class="top-header">.*?</header>', prod_html)
if match:
    header_str = match.group(0)
else:
    header_str = "<!-- Header not found -->"

# Adjust classes and links for BOM calculator
header_str = header_str.replace('<a href="/production" class="nav-btn active">', '<a href="/production" class="nav-btn">')
header_str = header_str.replace('<a href="/production" class="active"><i class="fa-solid fa-calculator"></i>생산 지시</a>', '<a href="/production"><i class="fa-solid fa-calculator"></i>생산 지시</a>')
header_str = header_str.replace('<a href="/bom-calculator"><i class="fa-solid fa-sitemap"></i>BOM 계산기</a>', '<a href="/bom-calculator" class="active"><i class="fa-solid fa-sitemap"></i>BOM 계산기</a>')

template = """<!DOCTYPE html>
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

        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }

        .action-btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0 2rem;
            border-radius: var(--radius-md);
            font-weight: 500;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            height: 48px;
        }

        .action-btn:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }

        .input-group-container {
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            margin-bottom: 1.5rem;
        }

        .input-group-container label {
            font-size: 0.9rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .level-section {
            margin-bottom: 24px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius-lg);
            overflow: hidden;
        }

        .level-header {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 12px 16px;
            font-weight: 600;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            justify-content: space-between;
            color: #fff;
        }
        
        .highlight {
            color: #10b981;
            font-weight: 700;
        }
        
        .result-area {
            display: none;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px 16px;
            text-align: left;
            font-size: 0.9rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        th {
            background-color: rgba(255, 255, 255, 0.02);
            color: var(--text-muted);
            font-weight: 600;
        }
    </style>
</head>

<body>
    <div class="app-container">
        <!-- HEADER PLACEHOLDER -->
        
        <main>
            <section class="control-panel glass-panel">
                <h2><i class="fa-solid fa-sitemap"></i> BOM 계산 설정</h2>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="input-group-container">
                        <label>수식 마스터 파일 선택</label>
                        <select id="formulaFileSelect" class="form-control">
                            <option value="">파일 목록을 불러오는 중...</option>
                        </select>
                    </div>

                    <div class="input-group-container">
                        <label>목표 생산량 (Level 0)</label>
                        <div style="display: flex; gap: 0.5rem;">
                            <input type="number" id="targetQty" class="form-control" placeholder="수량을 입력하세요" min="1" value="256" />
                            <button onclick="calculateBOM()" class="action-btn" style="white-space: nowrap;">
                                <i class="fa-solid fa-wand-magic-sparkles"></i> BOM 전개 및 계산
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            <div id="spinner" class="hidden" style="text-align: center; padding: 40px; color: var(--text-muted); display: none;">
                <div class="spinner"></div>
                <p>데이터를 바탕으로 계산 중입니다...</p>
            </div>

            <div id="emptyState" class="empty-state">
                <i class="fa-solid fa-clipboard-check"></i>
                <p>수식 파일과 목표 생산량을 설정하고 계산 버튼을 눌러주세요.</p>
            </div>

            <section id="resultArea" class="results-section result-area">
                <div class="history-panel glass-panel">
                    <div class="panel-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <h2><i class="fa-solid fa-list-check"></i> 전개 결과 (BOM Tree)</h2>
                        </div>
                    </div>
                    
                    <div id="summaryInfo" style="margin-bottom: 20px; font-weight: 500; color: var(--text-muted);"></div>
                    
                    <div class="level-section">
                        <div class="level-header">Level 1 (포장/완제품) <span id="l1Count"></span></div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 20%;">상위 Lot</th>
                                    <th style="width: 30%;">구성품</th>
                                    <th style="width: 25%;">생산Lot</th>
                                    <th style="width: 15%;">수량</th>
                                    <th style="width: 10%;">단위</th>
                                </tr>
                            </thead>
                            <tbody id="l1Table"></tbody>
                        </table>
                    </div>

                    <div class="level-section">
                        <div class="level-header">Level 2 (반제품 제조) <span id="l2Count"></span></div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 20%;">상위 Lot</th>
                                    <th style="width: 30%;">구성품</th>
                                    <th style="width: 25%;">생산Lot</th>
                                    <th style="width: 15%;">수량</th>
                                    <th style="width: 10%;">단위</th>
                                </tr>
                            </thead>
                            <tbody id="l2Table"></tbody>
                        </table>
                    </div>

                    <div class="level-section">
                        <div class="level-header">Level 3 (하위 조제) <span id="l3Count"></span></div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 20%;">상위 Lot</th>
                                    <th style="width: 30%;">구성품</th>
                                    <th style="width: 25%;">생산Lot</th>
                                    <th style="width: 15%;">수량</th>
                                    <th style="width: 10%;">단위</th>
                                </tr>
                            </thead>
                            <tbody id="l3Table"></tbody>
                        </table>
                    </div>
                </div>
            </section>
        </main>
    </div>

    <script>
        fetch('/api/lots/bom')
            .then(res => res.json())
            .then(data => {
                const select = document.getElementById('formulaFileSelect');
                select.innerHTML = '';
                
                if(data && data.length > 0) {
                    data.forEach(item => {
                        const opt = document.createElement('option');
                        opt.value = item.filename;
                        opt.textContent = item.filename;
                        if(item.filename.includes('BCE01_BOM')) opt.selected = true;
                        select.appendChild(opt);
                    });
                } else {
                    select.innerHTML = '<option value="">가용한 파일 없음</option>';
                }
            })
            .catch(err => {
                console.error("파일 목록을 불러오지 못했습니다.", err);
                const select = document.getElementById('formulaFileSelect');
                select.innerHTML = '<option value="">파일 로드 중 오류 발생</option>';
            });

        function calculateBOM() {
            const formulaFile = document.getElementById('formulaFileSelect').value;
            const targetQty = document.getElementById('targetQty').value;

            if (!formulaFile) {
                alert("수식 마스터 파일을 선택해주세요.");
                return;
            }
            if (!targetQty || targetQty <= 0) {
                alert("유효한 목표 생산량을 입력해주세요.");
                return;
            }

            document.getElementById('emptyState').style.display = 'none';
            document.getElementById('resultArea').style.display = 'none';
            document.getElementById('spinner').style.display = 'block';

            fetch('/api/generate_bom', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    formula_file: formulaFile,
                    target_qty: targetQty 
                })
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('spinner').style.display = 'none';
                if (data.error) {
                    alert(data.error);
                    return;
                }
                renderResults(data);
                document.getElementById('resultArea').style.display = 'block';
            })
            .catch(err => {
                document.getElementById('spinner').style.display = 'none';
                alert("서버 통신 중 오류가 발생했습니다.");
                console.error(err);
            });
        }

        function renderResults(data) {
            document.getElementById('summaryInfo').innerText = 
                `파일 [${data.level0.제품명.replace('전개 소스: ', '')}]을(를) 사용하여 전개한 결과입니다. (목표수량: ${data.level0.목표수량})`;

            const targetCols = ['상위Lot', '명칭 / 구성품', '생산Lot', '계산된_소요량', '단위'];

            renderTable('l1Table', 'l1Count', data.level1, targetCols);
            renderTable('l2Table', 'l2Count', data.level2, targetCols);
            renderTable('l3Table', 'l3Count', data.level3, targetCols);
        }

        function renderTable(tableId, countId, items, cols) {
            const tbody = document.getElementById(tableId);
            tbody.innerHTML = '';
            document.getElementById(countId).innerText = `${items.length} 항목`;
            
            items.forEach(item => {
                let row = '<tr>';
                cols.forEach(col => {
                    let val = item[col] || '';
                    if(col === '계산된_소요량') {
                        row += `<td class="highlight">${val}</td>`;
                    } else {
                        row += `<td>${val}</td>`;
                    }
                });
                row += '</tr>';
                tbody.innerHTML += row;
            });
        }
    </script>
</body>
</html>
"""

final_html = template.replace('<!-- HEADER PLACEHOLDER -->', header_str)

with open(bom_html_path, "w", encoding="utf-8") as f:
    f.write(final_html)
print("done")
