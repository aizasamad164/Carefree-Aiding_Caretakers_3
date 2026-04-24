// ── Session ───────────────────────────────────────────────────────────────────
const PID = sessionStorage.getItem('cf_pid');
const NAME = sessionStorage.getItem('cf_name');
const ROLE = sessionStorage.getItem('cf_role');

if (!PID || ROLE !== 'guardian') window.location.href = '/';

document.getElementById('sb-name').textContent = NAME || 'Guardian';
document.getElementById('h-badge').textContent = NAME || 'Guardian';


// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type = 'ok') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `show ${type}`;
    clearTimeout(el._t);
    el._t = setTimeout(() => el.className = '', 3200);
}


// ── Date formatter ────────────────────────────────────────────────────────────
function fdt(s) {
    if (!s) return '—';
    try {
        return new Date(s).toLocaleString('en-PK', { dateStyle: 'medium', timeStyle: 'short' });
    } catch { return s }
}


// ── Navigation ────────────────────────────────────────────────────────────────
const titles = {
    info: 'Patient Information',
    appointments: 'Appointments',
    finances: 'Expenses & Finances',
    query: 'Send Query',
};

function nav(p) {
    document.querySelectorAll('.panel').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.sb-item').forEach(x => x.classList.remove('active'));
    document.getElementById('panel-' + p).classList.add('active');
    document.querySelector(`[data-p="${p}"]`)?.classList.add('active');
    document.getElementById('h-title').textContent = titles[p];

    if (p === 'appointments') loadAppts('All');
    if (p === 'finances') loadFinances();
}


// ── Patient Information ───────────────────────────────────────────────────────
// Field names updated to normalized lowercase from row_to_dict
async function loadPatInfo() {
    const r = await fetch(`/api/patient/${PID}`);
    const p = await r.json();

    document.getElementById('pi-name-hd').textContent = p.patient_name || 'Patient Profile';

    const fields = [      
        ['Name', p.patient_name],
        ['Age', p.age],
        ['Gender', p.gender],
        ['Height', p.height ? p.height + ' cm' : '—'],
        ['Weight', p.weight ? p.weight + ' kg' : '—'],
        ['Smoker', p.smoker],
        ['Children', p.children],
        ['Region', p.region],
    ];

    document.getElementById('info-grid').innerHTML = fields.map(([k, v]) => `
        <div class="info-item">
            <div class="info-lbl">${k}</div>
            <div class="info-val" style="font-size:${k === 'Notes' ? '13' : '15'}px">${v || '—'}</div>
        </div>`).join('');

    // Pre-fill query textarea with existing comment
    document.getElementById('query-txt').value = p.guardian_comment || '';
}


// ── Appointments ──────────────────────────────────────────────────────────────
// doctor_name replaces client_name — comes via JOIN with Doctor table
let curApptFilter = 'All';

async function loadAppts(filter) {
    curApptFilter = filter;
    const r = await fetch(`/api/appointments/${PID}?filter=${filter}`);
    const appts = await r.json();
    const tb = document.querySelector('#appt-tbl tbody');

    if (!appts.length) {
        tb.innerHTML = `<tr><td colspan="5"><div class="empty">
            <div class="empty-icon">📅</div>
            <p>No appointments found.</p>
        </div></td></tr>`;
        return;
    }

    // doctor_name + specialization replace old client_name
    // status field added
    tb.innerHTML = appts.map(a => `
        <tr>
            <td><strong>${a.doctor_name}</strong><br>
                <span style="font-size:11px;color:var(--muted)">${a.specialization || '—'}</span>
            </td>
            <td><span class="badge b-tag">${a.appointment_category}</span></td>
            <td>${fdt(a.appointment_datetime)}</td>
            <td><span class="badge b-tag">${a.status || 'Scheduled'}</span></td>
            <td>${a.appointment_description || '—'}</td>
        </tr>`).join('');
}

function apptF(f, btn) {
    document.querySelectorAll('.pills .pill').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    loadAppts(f);
}


// ── Finances ──────────────────────────────────────────────────────────────────
// Balance removed from Patient table — balance hero shows charges only
// Add/remove balance endpoints still exist for guardian use
async function loadFinances() {
    const r = await fetch(`/api/patient/${PID}`);
    const p = await r.json();

    // Balance still on Patient table — shown here for guardian
    document.getElementById('bal-amt').textContent = `Rs. ${(p.balance || 0).toFixed(2)}`;
    document.getElementById('bal-charges').textContent = `Rs. ${(p.charges || 0).toFixed(2)}`;

    const exr = await fetch(`/api/expenses/${PID}`);
    const exps = await exr.json();
    const tb = document.querySelector('#exp-tbl tbody');

    if (!exps.length) {
        tb.innerHTML = `<tr><td colspan="4"><div class="empty">
            <div class="empty-icon">💰</div>
            <p>No expenses recorded yet.</p>
        </div></td></tr>`;
        return;
    }

    // Normalized field names: expense_name, expense_category, expense_amount, expense_time
    tb.innerHTML = exps.map(e => `
        <tr>
            <td><strong>${e.expense_name}</strong></td>
            <td><span class="badge b-tag">${e.expense_category}</span></td>
            <td>Rs. ${parseFloat(e.expense_amount).toFixed(2)}</td>
            <td>${fdt(e.expense_time)}</td>
        </tr>`).join('');
}

async function sendBalance() {
    const amt = parseFloat(document.getElementById('funds-input').value);
    
    const r = await fetch(`/api/patient/${PID}/balance/add`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amt })
        // patient_id removed from body — it's in the URL
    });
    const d = await r.json();
    if (r.ok) {
        document.getElementById('bal-amt').textContent = `Rs. ${d.balance.toFixed(2)}`;
        document.getElementById('funds-input').value = '';
        toast(`✓ Rs. ${amt.toFixed(2)} sent successfully`);
    } else {
        toast('Failed to send balance', 'err');
    }
}


// ── Query (Guardian Comment) ──────────────────────────────────────────────────
async function sendQuery() {
    const msg = document.getElementById('query-txt').value.trim();
    if (!msg) { toast('Please write a message first', 'err'); return }

    const r = await fetch(`/api/patient/${PID}/comment`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment: msg })
        // patient_id removed from body — CommentBody only has comment now
    });

    if (r.ok) toast('✓ Query sent to caretaker');
    else toast('Failed to send query', 'err');
}


// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}


// ── Init ──────────────────────────────────────────────────────────────────────
loadPatInfo();