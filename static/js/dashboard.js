// ── Dashboard ─────────────────────────────────────────────────────────────────
// Loads patient count stat and mini patient table on the dashboard panel.
// Balance column removed — it no longer exists on the Patient table.

async function loadDash() {
    const r = await fetch(`/api/patients/${CF.id}`);
    patients = await r.json();

    // Update stats
    document.getElementById('st-pats').textContent = patients.length;
    document.getElementById('sb-pats').style.width = Math.min(patients.length * 10, 100) + '%';

    // Mini patient table — shows up to 6 patients
    // Columns: ID, Name, Guardian Name, Guardian Contact
    // Balance removed since it no longer exists on Patient table
    const tb = document.querySelector('#dash-tbl tbody');
    if (!patients.length) {
        tb.innerHTML = `<tr><td colspan="4"><div class="empty">
            <div class="empty-icon">👥</div>
            <p>No patients yet.</p>
        </div></td></tr>`;
    } else {
        tb.innerHTML = patients.slice(0, 6).map(p => `
            <tr>
                <td><code style="font-size:11px;background:var(--cream2);padding:2px 6px;border-radius:4px">${p.patient_id}</code></td>
                <td><strong>${p.patient_name}</strong></td>
                <td>${p.guardian_name || '—'}</td>
                <td>${p.guardian_contact || '—'}</td>
            </tr>`).join('');
        // guardian_name and guardian_contact come via JOIN in GET /api/patients/{cid}
    }

    fillPatSelects(patients);
}