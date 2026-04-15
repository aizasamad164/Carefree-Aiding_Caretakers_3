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

    if (!pid) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty">
            <div class="empty-icon">📅</div>
            <p>Select a patient to view appointments.</p>
        </div></td></tr>`;
        return;
    }

    const r = await fetch(`/api/appointments/${pid}?filter=${filters.appts}`);
    const appts = await r.json();

    if (!appts.length) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty">
            <div class="empty-icon">📅</div>
            <p>No appointments found.</p>
        </div></td></tr>`;
        return;
    }

    // doctor_name replaces client_name — comes via JOIN with Doctor table
    // status is a new field added in normalization
    tb.innerHTML = appts.map(a => `
        <tr>
            <td><strong>${a.doctor_name}</strong><br>
                <span style="font-size:11px;color:var(--muted)">${a.specialization || '—'}</span>
            </td>
            <td><span class="badge b-tag">${a.appointment_category}</span></td>
            <td>${fdt(a.appointment_datetime)}</td>
            <td><span class="badge b-tag">${a.status || 'Scheduled'}</span></td>
            <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                ${a.appointment_description || '—'}
            </td>
            <td><button class="btn btn-danger btn-sm" onclick="delAppt(${a.appointment_id})">Remove</button></td>
        </tr>`).join('');
}

async function addAppt() {
    const pid = document.getElementById('a-patsel').value;
    if (!pid) { toast('Select a patient first', 'err'); return }

    const body = {
        doctor_name: document.getElementById('af-doctor').value.trim(),
        specialization: document.getElementById('af-spec').value.trim(),
        datetime_val: document.getElementById('af-time').value,
        category: document.getElementById('af-cat').value,
        description: document.getElementById('af-desc').value.trim(),
        status: 'Scheduled',
        patient_id: pid,
    };

    if (!body.doctor_name || !body.datetime_val) {
        toast('Doctor name and datetime required', 'err'); return
    }

    const r = await fetch('/api/appointment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    if (r.ok) {
        toast('Appointment added');
        toggleSec('appt-form');
        loadAppts();
    }
}

async function delAppt(id) {
    if (!confirm('Remove this appointment?')) return;
    const r = await fetch(`/api/appointment/${id}`, { method: 'DELETE' });
    if (r.ok) { toast('Appointment removed'); loadAppts(); }
}