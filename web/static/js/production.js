document.addEventListener('DOMContentLoaded', () => {
    const kitQtyInput = document.getElementById('kit-qty-input');
    const calcBtn = document.getElementById('calc-btn');
    const loadingEl = document.getElementById('loading');
    const emptyStateEl = document.getElementById('empty-state');
    const resultsSection = document.getElementById('results-section');
    const tbody = document.getElementById('production-tbody');
    const kitLabel = document.getElementById('kit-label');
    const downloadBtn = document.getElementById('download-xlsx-btn');

    let lastCalculatedData = null;

    calcBtn.addEventListener('click', async () => {
        const qty = parseInt(kitQtyInput.value);
        if (isNaN(qty) || qty < 1 || qty > 256) {
            alert('키트 생산 수량은 1에서 256 사이의 숫자를 입력해주세요.');
            return;
        }

        // UI Reset
        emptyStateEl.classList.add('hidden');
        resultsSection.classList.add('hidden');
        loadingEl.classList.remove('hidden');

        try {
            const params = new URLSearchParams({ kit_qty: qty });
            const response = await fetch(`/api/production/calculate?${params.toString()}`);
            const result = await response.json();

            loadingEl.classList.add('hidden');

            if (result.status === 'success') {
                kitLabel.textContent = `${qty} Kit 필요 원료`;
                lastCalculatedData = result.data; // 데이터 저장
                renderTable(result.data);
                resultsSection.classList.remove('hidden');
            } else {
                alert('계산 중 오류가 발생했습니다: ' + result.message);
                emptyStateEl.classList.remove('hidden');
            }
        } catch (error) {
            loadingEl.classList.add('hidden');
            alert('서버와의 통신에 실패했습니다.');
            console.error('Error:', error);
            emptyStateEl.classList.remove('hidden');
        }
    });

    // 엑셀 다운로드 처리
    downloadBtn.addEventListener('click', async () => {
        if (!lastCalculatedData) {
            alert('먼저 소요량 계산을 수행해 주세요.');
            return;
        }

        try {
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> 다운로드 중...';

            const response = await fetch('/api/production/export-excel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    items: lastCalculatedData,
                    usage_date: '',
                    usage_purpose: ''
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `생산할당내역_${new Date().toISOString().split('T')[0].replace(/-/g, '')}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const errResult = await response.json();
                alert('엑셀 생성 중 오류가 발생했습니다: ' + (errResult.message || '알 수 없는 오류'));
            }
        } catch (error) {
            console.error('Excel Download Error:', error);
            alert('엑셀 다운로드 중 서버 통신 오류가 발생했습니다.');
        } finally {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = '<i class="fa-solid fa-file-excel"></i> 엑셀 다운로드';
        }
    });

    function renderTable(data) {
        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">해당 수량에 대한 BOM 데이터가 없습니다.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const tr = document.createElement('tr');

            // Lot List Formatting
            let lotHtml = '<ul class="alloc-list">';
            if (item.allocated_lots && item.allocated_lots.length > 0) {
                item.allocated_lots.forEach(lot => {
                    lotHtml += `
                        <li class="alloc-item">
                            <span class="lot-badge">${lot.lot_no}</span>
                            <span class="date-badge" style="margin-left: auto;"><i class="fa-regular fa-calendar-days"></i> ${lot.expire_date}</span>
                            <span class="qty-badge" style="font-weight: 700; color: #fff; min-width: 60px; text-align: right;">${lot.allocated_qty.toLocaleString()}</span>
                        </li>
                    `;
                });
            } else {
                lotHtml += `<li class="alloc-item" style="color: var(--text-muted);">할당 가능 재고 없음</li>`;
            }
            lotHtml += '</ul>';

            // Shortage status
            let statusHtml = '';
            let shortageClass = '';
            if (item.status === 'success') {
                statusHtml = `<span class="badge success-text"><i class="fa-solid fa-check"></i> 할당 완료</span>`;
            } else {
                statusHtml = `<span class="badge shortage"><i class="fa-solid fa-triangle-exclamation"></i> 재고 부족</span>`;
                shortageClass = 'shortage';
            }

            tr.innerHTML = `
                <td>
                    <div style="font-weight: 600; color: var(--primary); margin-bottom: 0.2rem;">${item.material_code}</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">${item.material_name}</div>
                </td>
                <td style="text-align: right; font-weight: bold; font-size: 1.1rem;">${item.required_qty.toLocaleString()}</td>
                <td>${lotHtml}</td>
                <td style="text-align: right;" class="${shortageClass}">${item.shortage_qty.toLocaleString()}</td>
                <td style="text-align: center;">${statusHtml}</td>
            `;

            tbody.appendChild(tr);
        });
    }
});
