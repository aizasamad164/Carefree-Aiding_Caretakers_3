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
    el._t = setTimeout(() => el.className = '', 3200);
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
// Called after patients are loaded so every select stays in sync
function fillPatSelects(list) {
    ['pi-sel', 't-patsel', 'a-patsel', 'e-patsel', 'c-patsel'].forEach(id => {
        const el = document.getElementById(id);
        const first = el.options[0].outerHTML;
        el.innerHTML = first + list.map(p =>
            `<option value="${p.patient_id}">${p.patient_name}</option>`
        ).join('');
        // patient_id and patient_name now use lowercase normalized field names
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
    stress: 'Stress Level Predictor',
    cost: 'Insurance Cost Predictor',
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

    // Add these three — reload data every time panel is opened
    if (p === 'tasks') {
        document.getElementById('t-patsel').value = '';
        loadTasks();
    }
    if (p === 'appointments') {
        document.getElementById('a-patsel').value = '';
        loadAppts();
    }
    if (p === 'expenses') {
        document.getElementById('e-patsel').value = '';
        loadExps();
    }
}

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}


// ── Init ──────────────────────────────────────────────────────────────────────
// On page load: load dashboard + notifications + start notif polling
loadDash();
loadNotifs();
setInterval(loadNotifs, 30000); // refresh notifications every 30s