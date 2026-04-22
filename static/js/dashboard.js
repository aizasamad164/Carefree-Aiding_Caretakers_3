async function loadDash() {
    const r = await fetch(`/api/patients/${CF.id}`);
    patients = await r.json();  // global patients set here

    document.getElementById('st-pats').textContent = patients.length;
    document.getElementById('sb-pats').style.width = Math.min(patients.length * 10, 100) + '%';

    // ── Tasks ──
    const rt = await fetch(`/api/tasks/stats/${CF.id}`);
    const td = await rt.json();
    document.getElementById('st-tasks').textContent = td.count ?? '—';

    // ── Appointments ──
    const ra = await fetch(`/api/appointments/stats/${CF.id}`);
    const ad = await ra.json();
    document.getElementById('st-appts').textContent = ad.count ?? '—';

    // ── Expenses ──
    const re = await fetch(`/api/expenses/stats/${CF.id}`);
    const ed = await re.json();
    document.getElementById('st-exps').textContent = ed.count ?? '—';

    // ── These MUST be after await — patients is now populated ──
    renderDashTbl(patients);
    fillPatSelects(patients);
}

function renderDashTbl(list) {
    const tb = document.querySelector('#dash-tbl tbody');
    if (!tb) return;
    if (!list.length) {
        tb.innerHTML = `<tr><td colspan="4"><div class="empty">
            <div class="empty-icon">👥</div>
            <p>No patients yet.</p>
        </div></td></tr>`;
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

    renderDashTbl(filtered);   // update dashboard table
    fillPatSelects(filtered);  // update dropdowns (optional)
}
