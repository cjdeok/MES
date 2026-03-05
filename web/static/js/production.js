document.addEventListener('DOMContentLoaded', () => {
    const kitQtyInput = document.getElementById('kit-qty-input');
    const calcBtn = document.getElementById('calc-btn');
    const loadingEl = document.getElementById('loading');
    const emptyStateEl = document.getElementById('empty-state');
    const resultsSection = document.getElementById('results-section');
    const tbody = document.getElementById('production-tbody');
    const kitLabel = document.getElementById('kit-label');

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
                            <span class="date-badge"><i class="fa-regular fa-clock"></i> ${lot.receive_date}</span>
                            <span class="qty-badge">${lot.allocated_qty.toLocaleString()}</span>
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
