// ── Vitals Management ────────────────────────────────────────────────────────
// Logic: Load history -> Toggle form (moves grid to bottom) -> Validate date -> Save

async function loadVitals() {
    const pid = document.getElementById('v-patsel').value; // Main selector
    const tb = document.querySelector('#vitals-tbl tbody');
    const addBtn = document.getElementById('btn-new-vital'); // The "New Vital" button

    if (!pid) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty">
            <div class="empty-icon">❤️</div>
            <p>Select a patient to view vitals.</p>
        </div></td></tr>`;
        return;
    }

    const r = await fetch(`/api/vitals/${pid}`);
    const vitals = await r.json();

    // Enforce "Once per Day" rule
    const today = new Date().toLocaleDateString('en-CA');
    const hasEntryToday = vitals.some(v => v.recorded_time.startsWith(today));

    if (addBtn) {
        addBtn.disabled = hasEntryToday;
        addBtn.innerHTML = hasEntryToday ? '<span>Logged Today</span>' : '<span>+ New Vital</span>';
    }

    if (!vitals.length) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty"><p>No vitals history.</p></div></td></tr>`;
        return;
    }

    // Grid displays Vitals Category, Time, and specific metrics
    tb.innerHTML = vitals.map(v => `
        <tr>
            <td><strong>${v.vitals_category}</strong></td>
            <td>${v.recorded_time}</td>
            <td>${v.pulse_rate || '--'} / ${v.blood_pressure || '--'}</td>
            <td>${v.oxygen_sat || '--'}%</td>
            <td>${v.blood_glucose || '--'}</td>
            <td><button class="btn btn-danger btn-sm" onclick="delVitals('${v.vitals_id}')">Remove</button></td>
        </tr>`).join('');
}

/**
 * Prepares the form interface. 
 * Per your request: Interface shows empty fields, patient can be selected again.
 */
function openVitalsForm() {
    // Clear all fields
    const fields = ['vf-pulse', 'vf-bp', 'vf-resp', 'vf-spo2', 'vf-glucose'];
    fields.forEach(id => document.getElementById(id).value = '');

    // Ensure the patient selector in the form matches the main selector
    const mainPid = document.getElementById('v-patsel').value;
    document.getElementById('vf-patsel').value = mainPid;

    // Show form section (This should be styled to push the grid to the bottom)
    toggleSec('vitals-form');
}

async function saveVitals() {
    // We get the ID from the form's specific selector (vf-patsel) as requested
    const pid = document.getElementById('vf-patsel').value;
    if (!pid) { toast('Select a patient', 'err'); return; }

    const body = {
        patient_id: pid,
        vitals_category: document.getElementById('vf-cat').value,
        pulse_rate: parseFloat(document.getElementById('vf-pulse').value) || 0,
        blood_pressure: parseFloat(document.getElementById('vf-bp').value) || 0,
        respiratory_rate: parseFloat(document.getElementById('vf-resp').value) || 0,
        oxygen_sat: parseFloat(document.getElementById('vf-spo2').value) || 0,
        blood_glucose: parseFloat(document.getElementById('vf-glucose').value) || 0
    };

    // Final check: Fetch vitals for the selected patient to ensure "once-a-day" 
    const checkReq = await fetch(`/api/vitals/${pid}`);
    const history = await checkReq.json();
    const today = new Date().toLocaleDateString('en-CA');

    if (history.some(v => v.recorded_time.startsWith(today))) {
        toast('Vitals already recorded for this patient today', 'err');
        return;
    }

    const r = await fetch('/api/vitals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    if (r.ok) {
        toast('Vitals saved successfully');
        toggleSec('vitals-form'); // Hide form
        loadVitals(); // Refresh the grid at the bottom
    }
}

async function delVitals(id) {
    if (!confirm('Remove this vital record?')) return;
    const r = await fetch(`/api/vitals/${id}`, { method: 'DELETE' });
    if (r.ok) {
        toast('Record removed');
        loadVitals();
    }
}