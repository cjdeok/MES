document.addEventListener('DOMContentLoaded', () => {
    const materialSelect = document.getElementById('material-select');
    const lotSelect = document.getElementById('lot-select');
    const loadingEl = document.getElementById('loading');
    const emptyStateEl = document.getElementById('empty-state');
    const resultsSection = document.getElementById('results-section');
    const historyTbody = document.getElementById('history-tbody');

    // Stats elements
    const totalInEl = document.getElementById('total-in');
    const totalOutEl = document.getElementById('total-out');
    const currentStockEl = document.getElementById('current-stock');
    const productLabel = document.getElementById('product-label');

    // 1. Load initial materials list
    fetchMaterials();

    // Event Listeners
    materialSelect.addEventListener('change', async (e) => {
        const itemCode = e.target.value;
        const itemName = e.target.options[e.target.selectedIndex].text;

        // Reset state
        resetUI();
        lotSelect.innerHTML = '<option value="">Lot 번호를 선택하세요...</option>';
        productLabel.textContent = itemName !== '원료를 선택하세요...' ? itemName : '';

        if (!itemCode) {
            lotSelect.disabled = true;
            return;
        }

        // Fetch lots for selected material
        lotSelect.disabled = false;
        await fetchLots(itemCode);
    });

    lotSelect.addEventListener('change', async (e) => {
        const itemCode = materialSelect.value;
        const lotNo = e.target.value;

        if (!itemCode || !lotNo) {
            resetUI();
            return;
        }

        await fetchInventory(itemCode, lotNo);
    });

    // API calls
    async function fetchMaterials() {
        try {
            const response = await fetch('/api/materials');
            const result = await response.json();

            if (result.status === 'success') {
                result.data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.code;
                    option.textContent = `${item.code} (${item.name})`;
                    materialSelect.appendChild(option);
                });
            } else {
                console.error("Failed to load materials:", result.message);
                alert("원료 목록을 불러오는데 실패했습니다.");
            }
        } catch (error) {
            console.error("Error fetching materials:", error);
        }
    }

    async function fetchLots(itemCode) {
        showLoading(true);
        try {
            const response = await fetch(`/api/lots/${itemCode}`);
            const result = await response.json();

            if (result.status === 'success') {
                if (result.data.length === 0) {
                    lotSelect.innerHTML = '<option value="">등록된 Lot 없음</option>';
                    lotSelect.disabled = true;
                } else {
                    result.data.forEach(lot => {
                        const option = document.createElement('option');
                        option.value = lot;
                        option.textContent = lot;
                        lotSelect.appendChild(option);
                    });
                }
            } else {
                console.error("Failed to load lots:", result.message);
            }
        } catch (error) {
            console.error("Error fetching lots:", error);
        } finally {
            showLoading(false);
        }
    }

    async function fetchInventory(itemCode, lotNo) {
        showLoading(true);
        try {
            const params = new URLSearchParams({ item_code: itemCode, lot_no: lotNo });
            const response = await fetch(`/api/inventory?${params.toString()}`);
            const result = await response.json();

            if (result.status === 'success') {
                updateUIWithData(result.summary, result.history, result.material_details);
            } else {
                console.error("Failed to load inventory:", result.message);
            }
        } catch (error) {
            console.error("Error fetching inventory:", error);
        } finally {
            showLoading(false);
            emptyStateEl.classList.add('hidden');
            resultsSection.classList.remove('hidden');
        }
    }

    // UI Updates
    function updateUIWithData(summary, history, details) {
        // Update stats with animation
        animateValue(totalInEl, 0, summary.total_in, 800);
        animateValue(totalOutEl, 0, summary.total_out, 800);
        animateValue(currentStockEl, 0, summary.current_stock, 800);

        // Update Material Info Panel
        const infoPanel = document.getElementById('material-info-panel');
        if (details) {
            document.getElementById('info-receive-date').textContent = details.receive_date || '-';
            document.getElementById('info-qc-date').textContent = details.qc_date || '-';
            document.getElementById('info-expire-date').textContent = details.expire_date || '-';
            infoPanel.classList.remove('hidden');
        } else {
            infoPanel.classList.add('hidden');
        }

        // Populate table
        historyTbody.innerHTML = '';
        if (history.length === 0) {
            historyTbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">이력 데이터가 없습니다.</td></tr>';
            return;
        }

        history.forEach((row, index) => {
            const tr = document.createElement('tr');
            tr.style.animation = `fadeIn 0.3s ease-in forwards ${index * 0.05}s`;
            tr.style.opacity = '0'; // For animation

            const typeClass = row.transaction_type === '입고' ? 'type-in' : 'type-out';
            const icon = row.transaction_type === '입고' ? '<i class="fa-solid fa-arrow-down-long"></i>' : '<i class="fa-solid fa-arrow-up-long"></i>';

            tr.innerHTML = `
                <td>${row.transaction_date || '-'}</td>
                <td class="${typeClass}">${icon} ${row.transaction_type}</td>
                <td style="font-weight: 500;">${row.quantity.toLocaleString()}</td>
                <td><span style="opacity:0.8;">${row.purpose || '-'}</span></td>
            `;
            historyTbody.appendChild(tr);
        });
    }

    function resetUI() {
        emptyStateEl.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        historyTbody.innerHTML = '';
        totalInEl.textContent = '0';
        totalOutEl.textContent = '0';
        currentStockEl.textContent = '0';
    }

    function showLoading(isLoading) {
        if (isLoading) {
            loadingEl.classList.remove('hidden');
            emptyStateEl.classList.add('hidden');
            resultsSection.classList.add('hidden');
        } else {
            loadingEl.classList.add('hidden');
        }
    }

    // Number counter animation function
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            // easeOutQuart
            const easeOutProgress = 1 - Math.pow(1 - progress, 4);
            const currentVal = Math.floor(easeOutProgress * (end - start) + start);

            obj.innerHTML = currentVal.toLocaleString();

            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                obj.innerHTML = end.toLocaleString(); // Ensure exact final value
            }
        };
        window.requestAnimationFrame(step);
    }
});
