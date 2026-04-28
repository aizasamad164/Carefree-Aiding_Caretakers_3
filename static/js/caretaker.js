// ── Shared State ─────────────────────────────────────────────────────────────
// CF holds the logged-in caretaker's session data
const CF = {
    id: sessionStorage.getItem('cf_id'),
    name: sessionStorage.getItem('cf_name'),
    role: sessionStorage.getItem('cf_role'),
};

// Redirect to login if not authenticated as caretaker
if (!CF.id || CF.role !== 'caretaker') window.location.href = '/';

document.getElementById('sb-name').textContent = CF.name || 'Caretaker';

// patients list shared across all modules
let patients = [];

// radio toggle state for patient form (gender + smoker)
const radio = { gender: '', smoker: '' };

// current filter state for tasks and appointments
const filters = { tasks: 'All', appts: 'All' };

// currently selected patient ID in patients table
let selPatId = null;


// ── Toast ─────────────────────────────────────────────────────────────────────
// type: 'ok' | 'err' | 'info'
function toast(msg, type = 'ok') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `show ${type}`;
    clearTimeout(el._t);
    el._t = setTimeout(() => el.className = '', 10000);
}


// ── Date formatter ────────────────────────────────────────────────────────────
function fdt(s) {
    if (!s) return '—';
    try {
        return new Date(s).toLocaleString('en-PK', { dateStyle: 'medium', timeStyle: 'short' });
    } catch { return s }
}


// ── Toggle expand section (add forms) ────────────────────────────────────────
function toggleSec(id) {
    document.getElementById(id).classList.toggle('open');
}


// ── Pill filter ───────────────────────────────────────────────────────────────
function setPillFilter(type, val, el) {
    el.closest('.pills').querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    el.classList.add('active');
    filters[type] = val;
    if (type === 'tasks') loadTasks();
    if (type === 'appts') loadAppts();
}


// ── Fill all patient dropdowns across panels ──────────────────────────────────
// Called after patients are loaded so every select stays in sync.
// Always uses the full patients array so searching the dashboard table
// never clears the selects in vitals / symptoms / etc.
function fillPatSelects(list) {
    ['pi-sel', 't-patsel', 'a-patsel', 'e-patsel', 'c-patsel', 'v-patsel', 'vf-patsel', 'sym-patsel'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        const first = el.options[0].outerHTML;
        el.innerHTML = first + list.map(p =>
            `<option value="${p.patient_id}">${p.patient_name}</option>`
        ).join('');
    });
}


// ── Navigation ────────────────────────────────────────────────────────────────
const titles = {
    dashboard: 'Dashboard',
    patients: 'Patient Management',
    patinfo: 'Patient Information',
    tasks: 'Task Manager',
    appointments: 'Appointments',
    expenses: 'Expense Tracker',
    vitals: 'Vitals Monitoring',
    symptoms: 'Symptom Tracker',
    stress: 'Stress Level Predictor',
    cost: 'Medical Cost Predictor',
};

function nav(p) {
    document.querySelectorAll('.panel').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.sb-item').forEach(x => x.classList.remove('active'));
    document.getElementById('panel-' + p).classList.add('active');
    document.querySelector(`[data-p="${p}"]`)?.classList.add('active');
    document.getElementById('h-title').textContent = titles[p] || p;

    if (p === 'dashboard') loadDash();
    if (p === 'patients') loadPats();
    if (p === 'patinfo') loadPatInfo();

    if (p === 'tasks') {
        document.getElementById('t-patsel').value = '';
        loadTasks();
    }
    if (p === 'appointments') {
        document.getElementById('a-patsel').value = '';
        loadAppts();
        loadDoctorsForDropdown();
    }
    if (p === 'expenses') {
        document.getElementById('e-patsel').value = '';
        loadExps();
    }
    if (p === 'vitals') {
        document.getElementById('v-patsel').value = '';
        loadVitals();
    }
    if (p === 'symptoms') {
        document.getElementById('sym-patsel').value = '';
        loadSymptoms();
    }


    if (p === 'stress') {
        document.getElementById('s-sleep').value = '';
        document.getElementById('s-qual').value = '';
        document.getElementById('s-act').value = '';
        document.getElementById('s-hr').value = '';
        document.getElementById('s-steps').value = '';
        document.getElementById('s-sys').value = '';
        document.getElementById('s-dia').value = '';

        document.getElementById('stress-val').textContent = '';
        document.getElementById('stress-box').classList.remove('show');
    }

    if (p === 'cost') {
        document.getElementById('c-age').value = '';
        document.getElementById('c-bmi').value = '';
        document.getElementById('c-children').value = '';
        document.getElementById('c-sex').value = 'male';
        document.getElementById('c-smoker').value = 'no';
        document.getElementById('c-region').value = 'northeast';

        document.getElementById('cost-val').textContent = '';
        document.getElementById('cost-box').classList.remove('show');
    }
}

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}


// ── Init ──────────────────────────────────────────────────────────────────────
// DOMContentLoaded guarantees that every <script> tag in the HTML has been
// parsed and executed (including dashboard.js, notifications.js, and the
// Chart.js CDN bundle) before we call any function defined in those files.
// Calling loadDash() / loadNotifs() at the top-level of this file was the
// root cause of all broken panels: those functions didn't exist yet.
document.addEventListener('DOMContentLoaded', function () {
    loadDash();
    if (typeof loadNotifs === 'function') {
        loadNotifs();
        setInterval(loadNotifs, 30000); // refresh notifications every 30 s
    } else {
        console.warn('notifications.js not loaded — notification panel disabled');
    }
});
