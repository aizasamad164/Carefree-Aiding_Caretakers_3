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

        // Update the card number immediately
        document.getElementById('st-tasks').textContent = td.count ?? '0';
        // 3.33 means 30 tasks will fill the bar exactly to 100%
        document.querySelectorAll('.stat-bar-fill')[1].style.width = Math.min(td.count * 3.33, 100) + '%';

        // Fix: Wait for Chart.js before calling the pie
        waitForChartJs(() => {
            loadTaskPie(td);
        });

    } catch (err) {
        console.error('Task fetch failed', err);
        document.getElementById('st-tasks').textContent = '—';
    }

    try {
        const ra = await fetch(`/api/appointments/stats/${CF.id}`);
        const ad = await ra.json();
        document.getElementById('st-appts').textContent = ad.count ?? '—';
        document.querySelectorAll('.stat-bar-fill')[2].style.width = Math.min(ad.count * 10, 100) + '%';

    } catch { document.getElementById('st-appts').textContent = '—'; }

    try {
        const re = await fetch(`/api/expenses/stats/${CF.id}`);
        const ed = await re.json();
        document.getElementById('st-exps').textContent = ed.count ?? '—';
        document.querySelectorAll('.stat-bar-fill')[3].style.width = Math.min(ed.count * 3.33, 100) + '%';

    } catch { document.getElementById('st-exps').textContent = '—'; }

    renderDashTbl(patients);
    fillPatSelects(patients);
    await loadVitalsOverview(patients);
}



/* ─── Donut — Task Completion ───────────────────────────────────────── */
let taskDonutChart = null;

function loadTaskPie(taskData) {
    const canvas = document.getElementById('donutChart');
    const pctText = document.getElementById('donutPct');
    if (!canvas) return;

    // 1. Get numbers and FORCE them to be numbers
    // pending = the count on your card
    // completed = the number that should be ADDED to the total
    const pending = Number(taskData.count || 0);
    const completed = Number(taskData.completed || 0);

    // 2. The Logic: Grand Total = Pending + Completed
    const grandTotal = pending + completed;
    const percentage = grandTotal > 0 ? Math.round((completed / grandTotal) * 100) : 0;

    // Debugging: Check these numbers in your F12 console
    console.log(`Donut Math: ${completed} done + ${pending} pending = ${grandTotal} total. (${percentage}%)`);

    if (pctText) pctText.textContent = percentage + '%';

    if (taskDonutChart) taskDonutChart.destroy();

    taskDonutChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Pending'],
            datasets: [{
                // Data[0] is Navy (Completed), Data[1] is Mint (Pending)
                data: grandTotal > 0 ? [completed, pending] : [0, 1],
                backgroundColor: ['#231942', '#a8f0e0'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '80%',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            }
        }
    });
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
/** Logic: Fetches latest vitals for top 6 patients and renders a combo bar/line chart. */

async function loadVitalsOverview(patientList) {
    const canvas = document.getElementById('dashVitalsChart');
    const placeholder = document.getElementById('dash-vitals-placeholder');
    if (!canvas || !patientList?.length) return;

    // Retry if Chart.js isn't loaded yet
    if (typeof Chart === 'undefined') {
        setTimeout(() => loadVitalsOverview(patientList), 200);
        return;
    }

    // Fetch latest vitals for the first 6 patients
    const subset = patientList.slice(0, 6);
    const results = await Promise.all(subset.map(p =>
        fetch(`/api/vitals/${p.patient_id}`)
            .then(r => r.ok ? r.json() : [])
            .catch(() => [])
    ));

    const labels = [], pulse = [], o2 = [], glucose = [];

    subset.forEach((p, i) => {
        const latest = results[i]?.[0];
        if (latest) {
            labels.push(p.patient_name.split(' ')[0]);

            // Fix: Oracle results are often UPPERCASE; check both cases
            const val = (k) => latest[k.toLowerCase()] ?? latest[k.toUpperCase()] ?? null;

            pulse.push(val('pulse_rate'));
            o2.push(val('oxygen_sat'));
            glucose.push(val('blood_glucose'));
        }
    });

    if (!labels.length) {
        if (placeholder) placeholder.style.display = 'flex';
        canvas.style.display = 'none';
        return;
    }

    // UI Toggle
    if (placeholder) placeholder.style.display = 'none';
    canvas.style.display = 'block';

    // Instance Management
    if (window.myDashVitalsChart instanceof Chart) window.myDashVitalsChart.destroy();

    // Compute Total Line
    const totalLine = labels.map((_, i) => {
        const v = [pulse[i], o2[i], glucose[i]].filter(n => n !== null).map(Number);
        return v.length ? v.reduce((a, b) => a + b, 0) : null;
    });

    window.myDashVitalsChart = new Chart(canvas, {
        data: {
            labels,
            datasets: [
                { type: 'bar', label: 'Pulse', data: pulse, backgroundColor: '#a8f0e0', yAxisID: 'yLeft', order: 2 },
                { type: 'bar', label: 'O2 Sat', data: o2, backgroundColor: '#231942', yAxisID: 'yLeft', order: 2 },
                { type: 'bar', label: 'Glucose', data: glucose, backgroundColor: '#b96ac9', yAxisID: 'yLeft', order: 2 },
                {
                    type: 'line', label: 'Total', data: totalLine,
                    borderColor: '#ffd2fc', yAxisID: 'yRight', order: 1, tension: 0.3, pointRadius: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }, // Keeping it clean for dashboard view
            scales: {
                yLeft: { position: 'left', beginAtZero: true, ticks: { font: { family: 'Outfit' } } },
                yRight: { position: 'right', grid: { display: false }, ticks: { font: { family: 'Outfit' } } },
                x: { grid: { display: false }, ticks: { font: { family: 'Outfit' } } }
            }
        }
    });
}