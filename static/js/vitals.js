// ── Vitals Management ────────────────────────────────────────────────────────
let vitalsLineChart = null;

async function loadVitals() {
    const pid = document.getElementById('v-patsel').value;
    const tb = document.querySelector('#vitals-tbl tbody');
    const addBtn = document.getElementById('btn-new-vital');

    if (!pid) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty">
            <div class="empty-icon">❤️</div>
            <p>Select a patient to view vitals.</p>
        </div></td></tr>`;
        renderVitalsChart([]);
        return;
    }

    document.getElementById('vf-patsel').value = pid;

    let vitals = [];
    try {
        const r = await fetch(`/api/vitals/${pid}`);
        if (!r.ok) throw new Error('fetch failed');
        vitals = await r.json();
    } catch (err) {
        console.error('loadVitals error:', err);
        tb.innerHTML = `<tr><td colspan="6"><div class="empty"><p>Could not load vitals.</p></div></td></tr>`;
        renderVitalsChart([]);
        return;
    }

    const today = new Date().toLocaleDateString('en-CA');
    const hasEntryToday = vitals.some(v => {
        if (!v.recorded_time) return false;
        return v.recorded_time.toString().startsWith(today);
    });
    if (addBtn) {
        addBtn.disabled = hasEntryToday;
        addBtn.innerHTML = hasEntryToday
            ? '<span>✓ Logged Today</span>'
            : '<span>+ New Vital</span>';
    }

    if (!vitals.length) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty"><p>No vitals history for this patient.</p></div></td></tr>`;
        renderVitalsChart([]);
        return;
    }

    tb.innerHTML = vitals.map(v => {
        const cat = v.vitals_category || v.vitalsCategory || v.category || '—';
        return `
        <tr>
            <td><span class="vital-category-badge">❤️ ${cat}</span></td>
            <td>${v.recorded_time || '—'}</td>
            <td><strong>${v.pulse_rate ?? '—'}</strong> bpm &nbsp;/&nbsp; ${v.blood_pressure ?? '—'}</td>
            <td>${v.oxygen_sat ?? '—'}%</td>
            <td>${v.blood_glucose ?? '—'}</td>
            <td><button class="btn btn-danger btn-sm" onclick="delVitals('${v.vitals_id}')">Remove</button></td>
        </tr>`;
    }).join('');

    renderVitalsChart(vitals);
}

function openVitalsForm() {
    const mainPid = document.getElementById('v-patsel').value;
    if (!mainPid) { toast('Select a patient first', 'err'); return; }

    ['vf-pulse', 'vf-bp', 'vf-resp', 'vf-spo2', 'vf-glucose'].forEach(id => {
        document.getElementById(id).value = '';
    });

    document.getElementById('vf-patsel').value = mainPid;

    const form = document.getElementById('vitals-form');
    if (!form.classList.contains('open')) form.classList.add('open');
}

async function saveVitals() {
    const pid = document.getElementById('vf-patsel').value;
    if (!pid) { toast('Select a patient', 'err'); return; }

    const _pf = v => { const n = parseFloat(v); return isNaN(n) ? null : n; };
    const pulse = _pf(document.getElementById('vf-pulse').value);
    const bp = _pf(document.getElementById('vf-bp').value);
    const resp = _pf(document.getElementById('vf-resp').value);
    const spo2 = _pf(document.getElementById('vf-spo2').value);
    const glucose = _pf(document.getElementById('vf-glucose').value);

    if (pulse == null && bp == null && resp == null && spo2 == null && glucose == null) {
        toast('Enter at least one vital reading', 'err');
        return;
    }

    try {
        const checkReq = await fetch(`/api/vitals/${pid}`);
        if (checkReq.ok) {
            const history = await checkReq.json();
            const today = new Date().toLocaleDateString('en-CA');
            if (history.some(v => v.recorded_time && v.recorded_time.toString().startsWith(today))) {
                toast('Vitals already recorded for this patient today', 'err');
                return;
            }
        }
    } catch { /* network issue — let the POST decide */ }

    const categoryValue = document.getElementById('vf-cat').value;
    const body = {
        patient_id: pid,
        vitals_category: categoryValue,
        category: categoryValue,
        pulse_rate: pulse,
        blood_pressure: bp,
        respiratory_rate: resp,
        oxygen_sat: spo2,
        blood_glucose: glucose
    };

    console.log('Saving vitals payload:', body);

    try {
        const r = await fetch('/api/vitals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (r.ok) {
            toast('Vitals saved successfully ✓', 'ok');
            document.getElementById('vitals-form').classList.remove('open');
            document.getElementById('v-patsel').value = pid;
            await loadVitals();
        } else {
            let errMsg = 'Error saving vitals';
            try {
                const errData = await r.json();
                errMsg = errData.detail || errData.message || errData.error || errMsg;
            } catch {
                try { errMsg = await r.text(); } catch { /* ignore */ }
            }
            console.error('saveVitals server error:', errMsg);
            toast(errMsg, 'err');
        }
    } catch (err) {
        console.error('saveVitals network error:', err);
        toast('Network error — could not save vitals', 'err');
    }
}

async function delVitals(id) {
    if (!confirm('Remove this vital record?')) return;
    try {
        const r = await fetch(`/api/vitals/${id}`, { method: 'DELETE' });
        if (r.ok) { toast('Record removed'); loadVitals(); }
        else { toast('Error removing record', 'err'); }
    } catch { toast('Network error', 'err'); }
}

// ── Vitals Trend Chart ────────────────────────────────────────────────────────
// Combo: grouped bars (pulse / O2 / glucose) + total overlay line
// Same style as dashboard — dual Y-axis, matching Image 1
function renderVitalsChart(vitals, retries = 20) {
    const canvas = document.getElementById('vitalsChart');
    const placeholder = document.getElementById('vitals-chart-placeholder');
    if (!canvas) return;

    if (typeof Chart === 'undefined') {
        if (retries > 0) {
            setTimeout(() => renderVitalsChart(vitals, retries - 1), 100);
        } else {
            console.warn('Chart.js did not load — vitals chart skipped');
        }
        return;
    }

    if (!vitals || !vitals.length) {
        if (placeholder) placeholder.style.display = 'flex';
        canvas.style.display = 'none';
        if (vitalsLineChart) { vitalsLineChart.destroy(); vitalsLineChart = null; }
        return;
    }

    if (placeholder) placeholder.style.display = 'none';
    canvas.style.display = 'block';

    // Chronological order, last 10 readings
    const recent = [...vitals].reverse().slice(-10);

    const labels = recent.map(v => {
        if (!v.recorded_time) return '—';
        const s = v.recorded_time.toString();
        return s.includes(' ') ? s.split(' ')[0] : s.split('T')[0];
    });

    const pulseData = recent.map(v => v.pulse_rate ?? null);
    const o2Data = recent.map(v => v.oxygen_sat ?? null);
    const glucData = recent.map(v => v.blood_glucose ?? null);

    // Total line = sum of available readings per entry
    const totalLine = recent.map(v => {
        const vals = [v.pulse_rate, v.oxygen_sat, v.blood_glucose].filter(x => x != null).map(Number);
        return vals.length ? vals.reduce((a, b) => a + b, 0) : null;
    });

    if (vitalsLineChart) vitalsLineChart.destroy();

    vitalsLineChart = new Chart(canvas, {
        data: {
            labels,
            datasets: [
                // ── Grouped bars (left Y axis) ────────────────────────────
                {
                    type: 'bar',
                    label: 'Pulse Rate (bpm)',
                    data: pulseData,
                    backgroundColor: '#a8f0e0',   // mint-dk — cohesive with palette
                    borderRadius: 4,
                    borderSkipped: false,
                    yAxisID: 'yLeft',
                    order: 2
                },
                {
                    type: 'bar',
                    label: 'Oxygen Sat (%)',
                    data: o2Data,
                    backgroundColor: '#231942',
                    borderRadius: 4,
                    borderSkipped: false,
                    yAxisID: 'yLeft',
                    order: 2
                },
                {
                    type: 'bar',
                    label: 'Blood Glucose',
                    data: glucData,
                    backgroundColor: '#b96ac9',
                    borderRadius: 4,
                    borderSkipped: false,
                    yAxisID: 'yLeft',
                    order: 2
                },
                // ── Total overlay line (right Y axis) ────────────────────
                {
                    type: 'line',
                    label: 'Total',
                    data: totalLine,
                    borderColor: '#ffd2fc',
                    backgroundColor: 'transparent',
                    borderWidth: 2.5,
                    tension: 0.35,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#ffd2fc',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    fill: false,
                    yAxisID: 'yRight',
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        font: { family: 'Outfit', size: 12 },
                        color: '#5a4d5e',
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 16
                    }
                },
                tooltip: {
                    backgroundColor: '#231942',
                    titleFont: { family: 'Playfair Display', size: 13 },
                    bodyFont: { family: 'Outfit', size: 12 },
                    padding: 12, cornerRadius: 10,
                    callbacks: {
                        title: ctx => 'Reading on ' + ctx[0].label,
                        afterBody: ctx => {
                            const v = recent[ctx[0].dataIndex];
                            const cat = v.vitals_category || v.vitalsCategory || v.category || '—';
                            return [
                                '─────────────────',
                                `Blood Pressure: ${v.blood_pressure ?? '—'}`,
                                `Resp. Rate: ${v.respiratory_rate ?? '—'} /min`,
                                `Category: ${cat}`
                            ];
                        }
                    }
                }
            },
            scales: {
                yLeft: {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: "Patient's Values",
                        font: { family: 'Outfit', size: 11 },
                        color: '#5a4d5e'
                    },
                    grid: { color: 'rgba(35,25,66,0.05)' },
                    ticks: { font: { family: 'Outfit' }, color: '#5a4d5e' }
                },
                yRight: {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Total',
                        font: { family: 'Outfit', size: 11 },
                        color: '#5a4d5e'
                    },
                    grid: { drawOnChartArea: false },
                    ticks: { font: { family: 'Outfit' }, color: '#5a4d5e' }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Outfit', size: 11 }, color: '#5a4d5e' }
                }
            }
        }
    });
}