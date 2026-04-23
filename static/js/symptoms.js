// ── Symptoms ──────────────────────────────────────────────────────────────────
let currentSymptomPid = null;
let symptomsBarChart = null;

async function loadSymptoms() {
    const pid = document.getElementById('sym-patsel').value;
    currentSymptomPid = pid;
    const listDiv = document.getElementById('sym-list');

    if (!pid) {
        listDiv.innerHTML = `<div class="empty">
            <div class="empty-icon">🩺</div>
            <p>Select a patient to view their symptoms.</p>
        </div>`;
        renderSymptomsChart([], []);
        return;
    }

    let predefined = [], custom = [];
    try {
        const r = await fetch(`/api/symptoms/${pid}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();

        if (Array.isArray(data)) {
            data.forEach(s => {
                if (s.source === 'custom' || s.is_custom || s.custom_id) {
                    custom.push(s);
                } else {
                    predefined.push(s);
                }
            });
        } else {
            predefined = data.predefined || data.predefined_symptoms || [];
            custom = data.custom || data.custom_symptoms || [];
        }
    } catch (err) {
        console.error('loadSymptoms error:', err);
        listDiv.innerHTML = `<div class="empty">
            <div class="empty-icon">🩺</div>
            <p>Could not load symptoms.</p>
        </div>`;
        renderSymptomsChart([], []);
        return;
    }

    if (!predefined.length && !custom.length) {
        listDiv.innerHTML = `<div class="empty">
            <div class="empty-icon">🩺</div>
            <p>No symptoms recorded yet.</p>
        </div>`;
        renderSymptomsChart([], []);
        return;
    }

    const severityClass = { 'High': 'high', 'Moderate': 'medium', 'Mild': 'low' };

    function normSym(s) {
        return {
            symptom_id: s.symptom_id || s.id || s.patient_symptom_id || '',
            name: s.name || s.symptom_name || '—',
            type: s.type || s.symptom_type || s.category || '—',
            severity: s.severity || s.severity_level || 'Mild',
            description: s.description || s.symptom_description || '',
            recorded_date: s.recorded_date || s.date_recorded || s.created_at || '—',
        };
    }

    predefined = predefined.map(normSym);
    custom = custom.map(normSym);

    let html = '';

    if (predefined.length) {
        html += `<div style="font-size:11px;font-weight:600;margin-bottom:8px;color:var(--muted);letter-spacing:.6px;text-transform:uppercase">Predefined Symptoms</div>`;
        html += predefined.map(s => `
            <div class="sym-item">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                        <strong style="font-size:14px">${s.name}</strong>
                        <span class="badge b-tag">${s.type}</span>
                        <span class="badge b-${severityClass[s.severity] || 'low'}">${s.severity}</span>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="delPredefinedSymptom('${pid}','${s.symptom_id}')">Remove</button>
                </div>
                <div style="font-size:12px;color:var(--muted);margin-top:6px;line-height:1.5">${s.description || 'No description available.'}</div>
                <div style="font-size:10px;color:var(--muted);margin-top:4px;opacity:.7">Recorded: ${s.recorded_date}</div>
            </div>`).join('');
    }

    if (custom.length) {
        html += `<div style="font-size:11px;font-weight:600;margin:16px 0 8px;color:var(--muted);letter-spacing:.6px;text-transform:uppercase">Custom Symptoms</div>`;
        html += custom.map(s => `
            <div class="sym-item" style="border-left:3px solid var(--purple)">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                        <strong style="font-size:14px">${s.name}</strong>
                        <span class="badge b-tag">${s.type}</span>
                        <span class="badge b-${severityClass[s.severity] || 'low'}">${s.severity}</span>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="delCustomSymptom(${s.symptom_id})">Remove</button>
                </div>
                <div style="font-size:12px;color:var(--muted);margin-top:6px;line-height:1.5">${s.description || 'No description available.'}</div>
                <div style="font-size:10px;color:var(--muted);margin-top:4px;opacity:.7">Recorded: ${s.recorded_date}</div>
            </div>`).join('');
    }

    listDiv.innerHTML = html;
    renderSymptomsChart(predefined, custom);
}

function toggleSymptomForm() {
    const form = document.getElementById('sym-form');
    form.classList.toggle('open');
    if (form.classList.contains('open')) {
        if (!currentSymptomPid) {
            toast('Select a patient first', 'err');
            form.classList.remove('open');
            return;
        }
        loadMasterSymptoms();
        showSymptomTab('predefined');
    }
}

async function loadMasterSymptoms() {
    const sel = document.getElementById('sym-master-sel');
    sel.innerHTML = '<option value="">— Loading… —</option>';
    try {
        const r = await fetch('/api/symptoms/master');
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const masters = await r.json();

        sel.innerHTML = '<option value="">— Select a symptom —</option>';
        if (!masters.length) { sel.innerHTML = '<option value="">No symptoms in master list</option>'; return; }

        masters.forEach(m => {
            const opt = document.createElement('option');
            const sid = m.symptom_id || m.id || '';
            const sname = m.name || m.symptom_name || '—';
            const stype = m.type || m.symptom_type || 'General';
            const ssev = m.severity || m.severity_level || '';
            const sdesc = m.description || '';
            opt.value = sid;
            opt.textContent = `${sname} (${stype}) — ${ssev}`;
            opt.dataset.name = sname; opt.dataset.type = stype;
            opt.dataset.desc = sdesc; opt.dataset.severity = ssev;
            sel.appendChild(opt);
        });
    } catch (err) {
        console.error('loadMasterSymptoms error:', err);
        toast('Could not load master symptom list', 'err');
        sel.innerHTML = '<option value="">— Failed to load —</option>';
    }
}

function showSymptomTab(tab) {
    document.getElementById('sym-tab-predefined').classList.toggle('active', tab === 'predefined');
    document.getElementById('sym-tab-custom').classList.toggle('active', tab === 'custom');
    document.getElementById('sym-predefined-form').style.display = tab === 'predefined' ? 'block' : 'none';
    document.getElementById('sym-custom-form').style.display = tab === 'custom' ? 'block' : 'none';
}

async function addPredefinedSymptom() {
    if (!currentSymptomPid) { toast('Select a patient first', 'err'); return; }
    const sid = document.getElementById('sym-master-sel').value;
    if (!sid) { toast('Select a symptom from the list', 'err'); return; }

    try {
        const r = await fetch('/api/symptom/predefined', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: currentSymptomPid, symptom_id: sid })
        });
        if (r.ok) {
            toast('Symptom added ✓');
            document.getElementById('sym-master-sel').value = '';
            document.getElementById('sym-form').classList.remove('open');
            loadSymptoms();
        } else {
            let errMsg = 'Error adding symptom';
            try { const e = await r.json(); errMsg = e.detail || e.message || errMsg; }
            catch { try { errMsg = await r.text(); } catch { } }
            toast(errMsg, 'err');
        }
    } catch (err) { console.error('addPredefinedSymptom network error:', err); toast('Network error', 'err'); }
}

async function addCustomSymptom() {
    if (!currentSymptomPid) { toast('Select a patient first', 'err'); return; }
    const name = document.getElementById('sym-name').value.trim();
    if (!name) { toast('Symptom name is required', 'err'); return; }

    const body = {
        patient_id: currentSymptomPid,
        name,
        type: document.getElementById('sym-type').value.trim(),
        description: document.getElementById('sym-desc').value.trim(),
        severity: document.getElementById('sym-severity').value
    };

    console.log('Adding custom symptom:', body);

    try {
        const r = await fetch('/api/symptom/custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (r.ok) {
            toast('Custom symptom added ✓');
            ['sym-name', 'sym-type', 'sym-desc'].forEach(id => document.getElementById(id).value = '');
            document.getElementById('sym-form').classList.remove('open');
            loadSymptoms();
        } else {
            let errMsg = 'Error adding symptom';
            try { const e = await r.json(); errMsg = e.detail || e.message || errMsg; }
            catch { try { errMsg = await r.text(); } catch { } }
            toast(errMsg, 'err');
        }
    } catch (err) { console.error('addCustomSymptom network error:', err); toast('Network error', 'err'); }
}

async function delPredefinedSymptom(pid, sid) {
    if (!confirm('Remove this symptom?')) return;
    try {
        const r = await fetch(`/api/symptom/predefined/${pid}/${sid}`, { method: 'DELETE' });
        if (r.ok) { toast('Symptom removed'); loadSymptoms(); }
        else { toast('Error removing symptom', 'err'); }
    } catch { toast('Network error', 'err'); }
}

async function delCustomSymptom(cid) {
    if (!confirm('Remove this symptom?')) return;
    try {
        const r = await fetch(`/api/symptom/custom/${cid}`, { method: 'DELETE' });
        if (r.ok) { toast('Symptom removed'); loadSymptoms(); }
        else { toast('Error removing symptom', 'err'); }
    } catch { toast('Network error', 'err'); }
}

// ── Symptoms Chart ────────────────────────────────────────────────────────────
// Multi-line chart (no fill, sharp points, clean grid) — matching Image 2
// X-axis = severity levels, one line per symptom type tracked over time
// Since symptoms don't have a natural time series we plot count-per-severity
// for Predefined vs Custom as two clean lines — mirrors the Image 2 style.
function renderSymptomsChart(predefined, custom, retries = 20) {
    const canvas = document.getElementById('symptomsChart');
    const placeholder = document.getElementById('sym-chart-placeholder');
    if (!canvas) return;

    if (typeof Chart === 'undefined') {
        if (retries > 0) {
            setTimeout(() => renderSymptomsChart(predefined, custom, retries - 1), 100);
        } else {
            console.warn('Chart.js did not load — symptoms chart skipped');
        }
        return;
    }

    const total = (predefined ? predefined.length : 0) + (custom ? custom.length : 0);
    if (!total) {
        if (placeholder) placeholder.style.display = 'flex';
        canvas.style.display = 'none';
        if (symptomsBarChart) { symptomsBarChart.destroy(); symptomsBarChart = null; }
        return;
    }

    if (placeholder) placeholder.style.display = 'none';
    canvas.style.display = 'block';

    const severities = ['High', 'Moderate', 'Mild'];
    const predCounts = severities.map(s => predefined.filter(x => x.severity === s).length);
    const custCounts = severities.map(s => custom.filter(x => x.severity === s).length);

    const predNames = severities.map(s => predefined.filter(x => x.severity === s).map(x => x.name));
    const custNames = severities.map(s => custom.filter(x => x.severity === s).map(x => x.name));
    const predDescs = severities.map(s => predefined.filter(x => x.severity === s).map(x => x.description || 'No description'));
    const custDescs = severities.map(s => custom.filter(x => x.severity === s).map(x => x.description || 'No description'));

    if (symptomsBarChart) symptomsBarChart.destroy();

    // ── Doughnut chart — severity breakdown across all symptoms ──────────────
    // Combines predefined + custom counts per severity level into a single
    // ring. Much more readable than a line/bar for this 3-bucket data shape:
    // you instantly see whether the patient leans High/Moderate/Mild.
    // Tooltips list the actual symptom names per slice for full detail.
    const allCounts = severities.map((s, i) => predCounts[i] + custCounts[i]);
    const allNames = severities.map((s, i) => [...predNames[i], ...custNames[i]]);

    symptomsBarChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['High', 'Moderate', 'Mild'],
            datasets: [{
                data: allCounts,
                backgroundColor: ['#231942', '#b96ac9', '#a8f0e0'],
                borderColor: ['#fff', '#fff', '#fff'],
                borderWidth: 3,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            cutout: '62%',   // thicker ring than default for better legibility
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { family: 'Outfit', size: 13 },
                        color: '#5a4d5e',
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 22,
                        generateLabels: chart => {
                            const data = chart.data;
                            return data.labels.map((label, i) => ({
                                text: `${label}  (${data.datasets[0].data[i]})`,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                strokeStyle: '#fff',
                                lineWidth: 2,
                                index: i
                            }));
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#231942',
                    titleFont: { family: 'Playfair Display', size: 13 },
                    bodyFont: { family: 'Outfit', size: 11 },
                    padding: 14, cornerRadius: 10,
                    callbacks: {
                        title: ctx => ctx[0].label + ' Severity',
                        label: ctx => {
                            const count = ctx.raw;
                            const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                            return `  ${count} symptom${count !== 1 ? 's' : ''}  (${pct}%)`;
                        },
                        afterLabel: ctx => {
                            const names = allNames[ctx.dataIndex];
                            if (!names.length) return '';
                            return ['', ...names.map(n => `  • ${n}`)];
                        }
                    }
                }
            }
        }
    });
}