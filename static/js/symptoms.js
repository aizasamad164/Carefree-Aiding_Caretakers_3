// ── Symptoms ──────────────────────────────────────────────────────────────────

let currentSymptomPid = null;

// ── Load symptoms panel for a patient ────────────────────────────────────────
async function loadSymptoms() {
    const pid = document.getElementById('sym-patsel').value;
    currentSymptomPid = pid;

    const listDiv = document.getElementById('sym-list');

    if (!pid) {
        listDiv.innerHTML = `<div class="empty">
            <div class="empty-icon">🩺</div>
            <p>Select a patient to view their symptoms.</p>
        </div>`;
        return;
    }

    const r = await fetch(`/api/symptoms/${pid}`);
    const data = await r.json();

    const { predefined, custom } = data;

    if (!predefined.length && !custom.length) {
        listDiv.innerHTML = `<div class="empty">
            <div class="empty-icon">🩺</div>
            <p>No symptoms recorded yet.</p>
        </div>`;
        return;
    }

    const severityColor = { 'High': 'high', 'Moderate': 'medium', 'Mild': 'low' };

    let html = '';

    if (predefined.length) {
        html += `<div style="font-size:12px;font-weight:600;margin-bottom:8px;color:var(--muted)">PREDEFINED</div>`;
        html += predefined.map(s => `
            <div class="sym-item">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                        <strong>${s.name}</strong>
                        <span class="badge b-tag" style="margin-left:6px">${s.type || '—'}</span>
                        <span class="badge b-${severityColor[s.severity] || 'low'}" style="margin-left:4px">${s.severity || '—'}</span>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="delPredefinedSymptom('${pid}','${s.symptom_id}')">Remove</button>
                </div>
                <div style="font-size:12px;color:var(--muted);margin-top:4px">${s.description || '—'}</div>
                <div style="font-size:11px;color:var(--muted);margin-top:2px">${s.recorded_date || ''}</div>
            </div>`).join('');
    }

    if (custom.length) {
        html += `<div style="font-size:12px;font-weight:600;margin:14px 0 8px;color:var(--muted)">CUSTOM</div>`;
        html += custom.map(s => `
            <div class="sym-item">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                        <strong>${s.name}</strong>
                        <span class="badge b-tag" style="margin-left:6px">${s.type || '—'}</span>
                        <span class="badge b-${severityColor[s.severity] || 'low'}" style="margin-left:4px">${s.severity || '—'}</span>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="delCustomSymptom(${s.symptom_id})">Remove</button>
                </div>
                <div style="font-size:12px;color:var(--muted);margin-top:4px">${s.description || '—'}</div>
                <div style="font-size:11px;color:var(--muted);margin-top:2px">${s.recorded_date || ''}</div>
            </div>`).join('');
    }

    listDiv.innerHTML = html;
}


// ── Toggle add symptom form ───────────────────────────────────────────────────
function toggleSymptomForm() {
    const form = document.getElementById('sym-form');
    form.classList.toggle('open');
    if (form.classList.contains('open')) {
        loadMasterSymptoms();
        showSymptomTab('predefined');
    }
}


// ── Load master symptoms into dropdown ────────────────────────────────────────
async function loadMasterSymptoms() {
    const sel = document.getElementById('sym-master-sel');
    if (sel.options.length > 1) return; // already loaded
    const r = await fetch('/api/symptoms/master');
    const masters = await r.json();
    sel.innerHTML = '<option value="">— Select a symptom —</option>';
    masters.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.symptom_id;
        opt.textContent = `${m.name} (${m.type || 'General'}) — ${m.severity}`;
        opt.dataset.name = m.name;
        opt.dataset.type = m.type;
        opt.dataset.desc = m.description;
        opt.dataset.severity = m.severity;
        sel.appendChild(opt);
    });
}


// ── Switch between predefined / custom tabs ───────────────────────────────────
function showSymptomTab(tab) {
    document.getElementById('sym-tab-predefined').classList.toggle('active', tab === 'predefined');
    document.getElementById('sym-tab-custom').classList.toggle('active', tab === 'custom');
    document.getElementById('sym-predefined-form').style.display = tab === 'predefined' ? 'block' : 'none';
    document.getElementById('sym-custom-form').style.display = tab === 'custom' ? 'block' : 'none';
}


// ── Add predefined symptom ────────────────────────────────────────────────────
async function addPredefinedSymptom() {
    if (!currentSymptomPid) { toast('Select a patient first', 'err'); return; }
    const sid = document.getElementById('sym-master-sel').value;
    if (!sid) { toast('Select a symptom from the list', 'err'); return; }

    const r = await fetch('/api/symptom/predefined', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: currentSymptomPid, symptom_id: sid })
    });

    if (r.ok) {
        toast('Symptom added');
        document.getElementById('sym-master-sel').value = '';
        toggleSymptomForm();
        loadSymptoms();
    } else {
        const e = await r.json();
        toast(e.detail || 'Error', 'err');
    }
}


// ── Add custom symptom ────────────────────────────────────────────────────────
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

    const r = await fetch('/api/symptom/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    if (r.ok) {
        toast('Custom symptom added');
        document.getElementById('sym-name').value = '';
        document.getElementById('sym-type').value = '';
        document.getElementById('sym-desc').value = '';
        toggleSymptomForm();
        loadSymptoms();
    } else {
        const e = await r.json();
        toast(e.detail || 'Error', 'err');
    }
}


// ── Delete predefined symptom ─────────────────────────────────────────────────
async function delPredefinedSymptom(pid, sid) {
    if (!confirm('Remove this symptom?')) return;
    const r = await fetch(`/api/symptom/predefined/${pid}/${sid}`, { method: 'DELETE' });
    if (r.ok) { toast('Symptom removed'); loadSymptoms(); }
    else { toast('Error removing symptom', 'err'); }
}


// ── Delete custom symptom ─────────────────────────────────────────────────────
async function delCustomSymptom(cid) {
    if (!confirm('Remove this symptom?')) return;
    const r = await fetch(`/api/symptom/custom/${cid}`, { method: 'DELETE' });
    if (r.ok) { toast('Symptom removed'); loadSymptoms(); }
    else { toast('Error removing symptom', 'err'); }
}