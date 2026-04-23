let dashVitalsChart = null;

async function loadDash() {
    try {
        const r = await fetch(`/api/patients/${CF.id}`);
        patients = await r.json();
    } catch (err) {
        console.error('loadDash: could not fetch patients', err);
        patients = [];
    }

    document.getElementById('st-pats').textContent = patients.length;
    document.getElementById('sb-pats').style.width = Math.min(patients.length * 10, 100) + '%';

    try {
        const rt = await fetch(`/api/tasks/stats/${CF.id}`);
        const td = await rt.json();
        document.getElementById('st-tasks').textContent = td.count ?? '—';
    } catch { document.getElementById('st-tasks').textContent = '—'; }

    try {
        const ra = await fetch(`/api/appointments/stats/${CF.id}`);
        const ad = await ra.json();
        document.getElementById('st-appts').textContent = ad.count ?? '—';
    } catch { document.getElementById('st-appts').textContent = '—'; }

    try {
        const re = await fetch(`/api/expenses/stats/${CF.id}`);
        const ed = await re.json();
        document.getElementById('st-exps').textContent = ed.count ?? '—';
    } catch { document.getElementById('st-exps').textContent = '—'; }

    renderDashTbl(patients);
    fillPatSelects(patients);
    waitForChartJs(() => loadVitalsOverview(patients));
}

function waitForChartJs(cb, retries = 20) {
    if (typeof Chart !== 'undefined') {
        cb();
    } else if (retries > 0) {
        setTimeout(() => waitForChartJs(cb, retries - 1), 100);
    } else {
        console.warn('Chart.js did not load in time — vitals overview skipped');
    }
}

function renderDashTbl(list) {
    const tb = document.querySelector('#dash-tbl tbody');
    if (!tb) return;
    if (!list.length) {
        tb.innerHTML = `<tr><td colspan="4"><div class="empty"><div class="empty-icon">👥</div><p>No patients yet.</p></div></td></tr>`;
        return;
    }
    tb.innerHTML = list.slice(0, 6).map(p => `
        <tr>
            <td><code style="font-size:11px;background:var(--cream2);padding:2px 6px;border-radius:4px">${p.patient_id}</code></td>
            <td><strong>${p.patient_name}</strong></td>
            <td>${p.guardian_name || '—'}</td>
            <td>${p.guardian_contact || '—'}</td>
        </tr>`).join('');
}

function filterPatientsByPrefix(prefix) {
    const filtered = patients.filter(p =>
        p.patient_name.toLowerCase().startsWith(prefix.toLowerCase())
    );
    renderDashTbl(filtered);
}

// ── Dashboard Vitals Overview ─────────────────────────────────────────────────
// Combo chart: grouped bars for Pulse / O2 / Glucose + overlaid line for total
// (matches Image 1 style — dual Y-axis, bars + line overlay)
async function loadVitalsOverview(patientList) {
    const canvas = document.getElementById('dashVitalsChart');
    const placeholder = document.getElementById('dash-vitals-placeholder');
    if (!canvas) return;
    if (typeof Chart === 'undefined') { console.warn('loadVitalsOverview: Chart.js not available yet'); return; }

    if (!patientList || !patientList.length) {
        if (placeholder) placeholder.style.display = 'flex';
        if (canvas) canvas.style.display = 'none';
        return;
    }

    const subset = patientList.slice(0, 6);
    const results = await Promise.all(
        subset.map(p =>
            fetch(`/api/vitals/${p.patient_id}`)
                .then(r => { if (!r.ok) return []; return r.json().catch(() => []); })
                .catch(() => [])
        )
    );

    const labels = [], pulseData = [], o2Data = [], glucData = [];
    subset.forEach((p, i) => {
        const vitals = results[i];
        if (vitals && vitals.length > 0) {
            const latest = vitals[0];
            const firstName = (p.patient_name || 'Patient').split(' ')[0];
            labels.push(firstName);
            pulseData.push(latest.pulse_rate != null ? Number(latest.pulse_rate) : null);
            o2Data.push(latest.oxygen_sat != null ? Number(latest.oxygen_sat) : null);
            glucData.push(latest.blood_glucose != null ? Number(latest.blood_glucose) : null);
        }
    });

    if (!labels.length) {
        if (placeholder) placeholder.style.display = 'flex';
        if (canvas) canvas.style.display = 'none';
        return;
    }

    if (placeholder) placeholder.style.display = 'none';
    canvas.style.display = 'block';

    if (dashVitalsChart) dashVitalsChart.destroy();

    // Compute "total" line values (sum of non-null readings per patient)
    const totalLine = labels.map((_, i) => {
        const vals = [pulseData[i], o2Data[i], glucData[i]].filter(v => v != null);
        return vals.length ? vals.reduce((a, b) => a + b, 0) : null;
    });

    dashVitalsChart = new Chart(canvas, {
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
                    backgroundColor: '#231942',   // navy
                    borderRadius: 4,
                    borderSkipped: false,
                    yAxisID: 'yLeft',
                    order: 2
                },
                {
                    type: 'bar',
                    label: 'Blood Glucose',
                    data: glucData,
                    backgroundColor: '#b96ac9',   // purple-mid
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
                        padding: 18
                    }
                },
                tooltip: {
                    backgroundColor: '#231942',
                    titleFont: { family: 'Playfair Display', size: 13 },
                    bodyFont: { family: 'Outfit', size: 12 },
                    padding: 12, cornerRadius: 10,
                    callbacks: {
                        title: ctx => ctx[0].label + ' — Latest Reading',
                        footer: () => 'Navigate to Vitals for full history'
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
                        text: 'Total Amount',
                        font: { family: 'Outfit', size: 11 },
                        color: '#5a4d5e'
                    },
                    grid: { drawOnChartArea: false },
                    ticks: { font: { family: 'Outfit' }, color: '#5a4d5e' }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Outfit', size: 12 }, color: '#5a4d5e' }
                }
            }
        }
    });
}