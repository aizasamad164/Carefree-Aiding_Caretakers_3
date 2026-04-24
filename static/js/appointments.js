// ── Appointments ─────────────────────────────────────────────────────────────
// Changes from old version:
// - All field names lowercased: appointment_id, appointment_category etc.
// - client_name replaced by doctor_name + specialization
//   because Client_Name was removed and Doctor table was added in 3NF fix
// - Status field added to table display
// - doctor_name and specialization are now separate form fields

async function loadAppts() {
    const pid = document.getElementById('a-patsel').value;
    const tb = document.querySelector('#appt-tbl tbody');

    // 1. Check if a patient is selected
    if (!pid) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty">
            <div class="empty-icon">📅</div>
            <p>Select a patient to view appointments.</p>
        </div></td></tr>`;
        return;
    }

    loadDoctorsForDropdown();

    // 2. Fetch data using the filter criteria
    const r = await fetch(`/api/appointments/${pid}?filter=${filters.appts}`);
    const appts = await r.json();

    // 3. Handle empty states
    if (!appts.length) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty">
            <div class="empty-icon">📅</div>
            <p>No appointments found for this patient.</p>
        </div></td></tr>`;
        return;
    }

    // 4. Map the normalized data to the table
    // We display doctor_name and specialization (joined from Doctor table) 
    // and the status field (added in the normalization fix).
    tb.innerHTML = appts.map(a => `
        <tr>
            <td>
                <strong>${a.doctor_name}</strong><br>
                <span style="font-size:11px;color:var(--muted)">
                    ${a.specialization || 'General Practitioner'}
                </span>
            </td>
            <td><span class="badge b-tag">${a.appointment_category}</span></td>
            <td>${fdt(a.appointment_datetime)}</td>
            <td><span class="badge b-tag">${a.status || 'Scheduled'}</span></td>
            <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${a.appointment_description}">
                ${a.appointment_description || '—'}
            </td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="delAppt(${a.appointment_id})">
                    Remove
                </button>
            </td>
        </tr>`).join('');
}

async function addAppt() {
    const pid = document.getElementById('a-patsel').value;
    if (!pid) { toast('Select a patient first', 'err'); return; }

    const docName = document.getElementById('af-doctor').value.trim();
    const spec = document.getElementById('af-spec').value.trim();
    const dtVal = document.getElementById('af-time').value;

    if (!docName || !dtVal) {
        toast('Doctor name and date/time are required', 'err');
        return;
    }

    const body = {
        doctor_name: docName,
        specialization: spec || 'General',
        datetime_val: dtVal,
        category: document.getElementById('af-cat').value,
        description: document.getElementById('af-desc').value.trim(),
        status: 'Scheduled',
        patient_id: pid,
    };

    const r = await fetch('/api/appointment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    if (r.ok) {
        toast('Appointment scheduled');

        // ── RESET ALL FIELDS ──────────────────────────────────────────
        document.getElementById('af-doctor').value = '';
        document.getElementById('af-desc').value = '';
        document.getElementById('af-spec').value = '';
        document.getElementById('af-doc-select').value = 'NEW';

        // Clear the time to show mm/dd/yyyy placeholder
        document.getElementById('af-time').value = '';
        // ──────────────────────────────────────────────────────────────

        // RESET the readOnly state for the next appointment
        document.getElementById('af-doctor').readOnly = false;
        document.getElementById('af-doctor').style.backgroundColor = "#ffffff";

        await loadDoctorsForDropdown();
        toggleSec('appt-form');
        loadAppts();
    } else {
        const errorData = await r.json();
        toast(errorData.detail || 'Error', 'err');
    }
}
// Dictionary to keep track of doctor details for auto-fill
let doctorCache = {};

async function loadDoctorsForDropdown() {
    const sel = document.getElementById('af-doc-select');
    if (!sel || !CF.id) return;

    const r = await fetch(`/api/doctors/${CF.id}`);
    const docs = await r.json();

    sel.innerHTML = '<option value="NEW">-- Add New Doctor --</option>';
    doctorCache = {};

    docs.forEach(d => {
        if (!doctorCache[d.doctor_name]) {
            doctorCache[d.doctor_name] = d.specialization;
            const opt = document.createElement('option');
            opt.value = d.doctor_name;
            opt.textContent = d.doctor_name;
            sel.appendChild(opt);
        }
    });
}

// Function to call when the dropdown changes
function onDoctorSelect() {
    const selVal = document.getElementById('af-doc-select').value;
    const nameInput = document.getElementById('af-doctor');
    const specInput = document.getElementById('af-spec');

    if (selVal === "NEW") {
        nameInput.value = "";
        specInput.value = "";
        // ALLOW typing for a new doctor
        nameInput.readOnly = false;
        nameInput.style.backgroundColor = "#ffffff"; // Optional: white background
    } else {
        nameInput.value = selVal;
        specInput.value = doctorCache[selVal] || "";
        // LOCK the name so they don't accidentally create a duplicate
        nameInput.readOnly = true;
        nameInput.style.backgroundColor = "#f0f0f0"; // Optional: grey out to show it's locked
    }
}


async function delAppt(id) {
    if (!confirm('Remove this appointment?')) return;
    const r = await fetch(`/api/appointment/${id}`, { method: 'DELETE' });
    if (r.ok) { toast('Appointment removed'); loadAppts(); }
    else { toast('Error removing appointment', 'err'); }
}