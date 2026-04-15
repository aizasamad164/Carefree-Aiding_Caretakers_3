// ── Patients ──────────────────────────────────────────────────────────────────
// Changes from old version:
// - All field names lowercased to match normalized DB (patient_id, patient_name etc.)
// - Guardian fields (guardian_name, guardian_contact) come via JOIN — field names updated
// - Balance column removed from table — no longer on Patient table
// - relation_with_patient field added to patient form (new Guardian table field)
// - CommentBody no longer takes patient_id in body — it's in the URL now
// - caretaker_id removed from PatientUpdate body — not needed on update

async function loadPats() {
    const res = await fetch(`/api/patients/${CF.id}`);
    patients = await res.json();
    renderPatTbl(patients);
    fillPatSelects(patients);
}

function renderPatTbl(list) {
    const tb = document.querySelector('#pat-tbl tbody');
    if (!list.length) {
        tb.innerHTML = `<tr><td colspan="5"><div class="empty">
            <div class="empty-icon">👥</div>
            <p>No patients yet. Click "+ Add Patient" to get started.</p>
        </div></td></tr>`;
        return;
    }
    // Balance column removed — table now has 5 cols: ID, Name, Guardian, Contact, Notes
    tb.innerHTML = list.map(p => `
        <tr onclick="selPat(this,'${p.patient_id}')" style="cursor:pointer">
            <td><code style="font-size:11px;background:var(--cream2);padding:2px 6px;border-radius:4px">${p.patient_id}</code></td>
            <td><strong>${p.patient_name}</strong></td>
            <td>${p.guardian_name || '—'}</td>
            <td>${p.guardian_contact || '—'}</td>
            <td style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted)">${p.guardian_comment || '—'}</td>
        </tr>`).join('');
}

function filterPats() {
    const q = document.getElementById('gsearch').value.toLowerCase();
    renderPatTbl(patients.filter(p =>
        p.patient_name.toLowerCase().includes(q) ||
        p.patient_id.toLowerCase().includes(q)
    ));
}

function selPat(row, pid) {
    document.querySelectorAll('#pat-tbl tbody tr').forEach(r => r.classList.remove('selected'));
    row.classList.add('selected');
    selPatId = pid;
}

function openAddPat() { nav('patinfo'); clearPatForm(); }

async function removeSelectedPat() {
    if (!selPatId) { toast('Select a patient row first', 'err'); return }
    if (!confirm('Delete this patient and all their data?')) return;
    const r = await fetch(`/api/patient/${selPatId}`, { method: 'DELETE' });
    if (r.ok) { toast('Patient removed'); selPatId = null; loadPats(); }
}


// ── Patient Information Form ──────────────────────────────────────────────────
function loadPatInfo() {
    loadPats();
    clearPatForm();
}

async function loadPatIntoForm() {
    const pid = document.getElementById('pi-sel').value;
    if (!pid) { clearPatForm(); return }

    const r = await fetch(`/api/patient/${pid}`);
    const p = await r.json();

    // Patient fields — normalized column names
    document.getElementById('pi-name').value = p.patient_name || '';
    document.getElementById('pi-age').value = p.age || '';
    document.getElementById('pi-height').value = p.height || '';
    document.getElementById('pi-weight').value = p.weight || '';
    document.getElementById('pi-children').value = p.children || '';
    document.getElementById('pi-region').value = (p.region || 'northeast').toLowerCase();

    // Guardian fields — come via JOIN from Guardian table
    document.getElementById('pi-gname').value = p.guardian_name || '';
    document.getElementById('pi-gcontact').value = p.guardian_contact || '';
    document.getElementById('pi-grelation').value = p.relation_with_patient || '';
    document.getElementById('pi-notes').value = p.guardian_comment || '';

    // Radio toggles
    radio.gender = p.gender || '';
    radio.smoker = p.smoker || '';
    document.querySelectorAll('.rtog-opt').forEach(o => {
        const t = o.textContent.trim();
        if (t === radio.gender || t === radio.smoker) o.classList.add('sel');
        else o.classList.remove('sel');
    });

    document.getElementById('pi-title').textContent = 'Edit: ' + p.patient_name;
}

function clearPatForm() {
    ['pi-name', 'pi-age', 'pi-height', 'pi-weight', 'pi-children',
        'pi-gname', 'pi-gcontact', 'pi-grelation', 'pi-notes'].forEach(id => {
            document.getElementById(id).value = '';
        });
    document.getElementById('pi-region').value = 'northeast';
    document.getElementById('pi-sel').value = '';
    document.getElementById('pi-title').textContent = 'Patient Information';
    radio.gender = ''; radio.smoker = '';
    document.querySelectorAll('.rtog-opt').forEach(o => o.classList.remove('sel'));
}

function setR(field, val, el) {
    radio[field] = val;
    el.closest('.rtog').querySelectorAll('.rtog-opt').forEach(o => o.classList.remove('sel'));
    el.classList.add('sel');
}

async function savePat() {
    const pid = document.getElementById('pi-sel').value;

    const body = {
        name: document.getElementById('pi-name').value.trim(),
        age: parseInt(document.getElementById('pi-age').value) || 0,
        gender: radio.gender,
        smoker: radio.smoker,
        height: parseFloat(document.getElementById('pi-height').value) || 0,
        weight: parseFloat(document.getElementById('pi-weight').value) || 0,
        children: parseInt(document.getElementById('pi-children').value) || 0,
        region: document.getElementById('pi-region').value,
        guardian_name: document.getElementById('pi-gname').value.trim(),
        guardian_contact: document.getElementById('pi-gcontact').value.trim(),
        relation_with_patient: document.getElementById('pi-grelation').value.trim(),
        // caretaker_id only needed on POST (create), not PUT (update)
        ...(pid ? {} : { caretaker_id: CF.id }),
    };

    if (!body.name) { toast('Patient name is required', 'err'); return }
    if (!body.gender) { toast('Please select a gender', 'err'); return }
    if (!body.smoker) { toast('Please select smoker status', 'err'); return }

    const url = pid ? `/api/patient/${pid}` : '/api/patient';
    const method = pid ? 'PUT' : 'POST';

    const r = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const d = await r.json();
    if (!r.ok) { toast(d.detail, 'err'); return }

    if (d.guardian_password) {
        toast(`✓ Patient added! Guardian PW: ${d.guardian_password}`, 'ok');
    } else {
        toast('✓ Patient updated');
    }

    // Save notes (guardian comment) separately via its own endpoint
    // CommentBody no longer takes patient_id in body — it's in the URL
    const notes = document.getElementById('pi-notes').value.trim();
    const finalPid = d.patient_id || pid;
    if (notes && finalPid) {
        await fetch(`/api/patient/${finalPid}/comment`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comment: notes })  // patient_id removed from body
        });
    }

    loadPats();
    clearPatForm();
}