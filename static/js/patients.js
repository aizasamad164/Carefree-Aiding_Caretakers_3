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

    const filtered = patients.filter(p =>
        p.patient_name.toLowerCase().startsWith(q) ||
        p.patient_id.toLowerCase().startsWith(q)
    );

    // ── Filter patients panel table ──
    renderPatTbl(filtered);

    // ── Filter dashboard mini table too ──
    const dashTb = document.querySelector('#dash-tbl tbody');
    if (dashTb) {
        if (!filtered.length) {
            dashTb.innerHTML = `<tr><td colspan="4"><div class="empty">
                <div class="empty-icon">👥</div>
                <p>No patients match your search.</p>
            </div></td></tr>`;
        } else {
            dashTb.innerHTML = filtered.slice(0, 6).map(p => `
                <tr>
                    <td><code style="font-size:11px;background:var(--cream2);padding:2px 6px;border-radius:4px">${p.patient_id}</code></td>
                    <td><strong>${p.patient_name}</strong></td>
                    <td>${p.guardian_name || '—'}</td>
                    <td>${p.guardian_contact || '—'}</td>
                </tr>`).join('');
        }
    }
}

// ── Search wrapper — called from HTML oninput ────────────────────────────────
function filterPatientsByPrefix(val) {
    if (document.getElementById('gsearch')) {
        document.getElementById('gsearch').value = val;
    }
    filterPats();
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
    if (r.ok) { toast('Patient removed'); selPatId = null; loadPats(); loadDash(); }
}


// ── Patient Information Form ──────────────────────────────────────────────────
function loadPatInfo() {
    loadPats();
    clearPatForm();
}

async function loadPatIntoForm() {
    const pid = document.getElementById('pi-sel').value;
    const pwSection = document.getElementById('pi-pw-section');

    if (!pid) {
        clearPatForm();
        pwSection.style.display = 'none'; // Hide if no patient selected
        return;
    }

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
    document.getElementById('pi-pw-section').style.display = 'block';
    document.getElementById('pi-title').textContent = 'Edit: ' + p.patient_name;

    pwSection.style.display = 'block'; // Show only when data is loaded
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

    // 1. Properly capture values for validation
    const pName = document.getElementById('pi-name').value.trim();
    const gName = document.getElementById('pi-gname').value.trim();
    const age = document.getElementById('pi-age').value;
    const height = document.getElementById('pi-height').value;
    const weight = document.getElementById('pi-weight').value;
    const gContact = document.getElementById('pi-gcontact').value.trim();

    const isNumeric = /^\d+$/.test(gContact);

    if (!isNumeric && gContact !== "") {
        toast('Contact number must contain only digits (no letters or spaces)', 'err');
        return; // Stops the function here
    }

    // 2. STOPS the process if required fields are missing
    // Note: We check radio.gender and radio.smoker because they are stored in that global object
    if (!pName || !gName || !age || !height || !weight || !radio.gender || !radio.smoker || !gContact) {
        toast('Please fill in all required fields (Name, Age, Stats, and Guardian info)', 'err');
        return;
    }

    const body = {
        name: pName,
        age: parseInt(age) || 0,
        gender: radio.gender,
        smoker: radio.smoker,
        height: parseFloat(height) || 0,
        weight: parseFloat(weight) || 0,
        children: parseInt(document.getElementById('pi-children').value) || 0,
        region: document.getElementById('pi-region').value,
        guardian_name: gName,
        guardian_contact: gContact,
        relation_with_patient: document.getElementById('pi-grelation').value.trim(),
        ...(pid ? {} : { caretaker_id: CF.id }),
    };

    const url = pid ? `/api/patient/${pid}` : '/api/patient';
    const method = pid ? 'PUT' : 'POST';

    const r = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    const d = await r.json();
    if (!r.ok) { toast(d.detail || 'Save failed', 'err'); return; }

    // 3. Logic for Toast: Only show password if it's a new patient (POST)
    if (d.guardian_password) {
        toast(`✓ Patient added! Guardian PW: ${d.guardian_password}`, 'ok');
    } else {
        toast('✓ Patient information updated', 'ok');
    }

    // 4. Save notes (CommentBody)
    const notes = document.getElementById('pi-notes').value.trim();
    const finalPid = d.patient_id || pid;
    if (notes && finalPid) {
        await fetch(`/api/patient/${finalPid}/comment`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comment: notes })
        });
    }

    loadPats();
    clearPatForm();
}

async function showGuardianPassword() {
    const pid = document.getElementById('pi-sel').value;

    // DEBUG: Check if we actually have a Patient ID
    if (!pid) {
        console.error("No Patient ID selected in the dropdown.");
        toast('Please select a patient from the list first', 'err');
        return;
    }

    try {
        console.log(`Fetching password for: ${pid}`);
        const res = await fetch(`/api/patient/${pid}/password`);

        // Handle 404 or 500 errors
        if (!res.ok) {
            const errorData = await res.json();
            console.error("Server Error:", errorData);
            toast(errorData.detail || 'Could not retrieve password', 'err');
            return;
        }

        const data = await res.json();

        // Final check for the password string
        if (data && data.password) {
            alert(`Guardian Password for this patient:\n\n${data.password}`);
        } else {
            toast('Password field is empty in database', 'err');
        }
    } catch (err) {
        console.error("Network/JS Error:", err);
        toast('Connection error. Check console (F12)', 'err');
    }
}

// Add this at the very end of patients.js
window.showGuardianPassword = showGuardianPassword;

document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'show-pw-btn') {
        showGuardianPassword();
    }
});