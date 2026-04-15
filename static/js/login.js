let currentRole = '';

function show(id) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}
function pickRole(role, el) {
    currentRole = role;
    document.querySelectorAll('.role-card').forEach(c => c.classList.remove('sel'));
    el.classList.add('sel');

    if (role === 'caretaker') {
        document.getElementById('si-title').textContent = 'Caretaker Sign In';
        document.getElementById('si-sub').textContent = 'Access your patient dashboard';
        document.getElementById('si-user-label').textContent = 'Username';
        document.getElementById('si-user').placeholder = 'Your caretaker name';
        // Show signup link for caretakers only
        document.getElementById('si-signup-link').style.display = 'block';
    } else {
        document.getElementById('si-title').textContent = 'Guardian Sign In';
        document.getElementById('si-sub').textContent = 'Enter your guardian name and password';
        document.getElementById('si-user-label').textContent = 'Guardian Name';
        document.getElementById('si-user').placeholder = 'Your guardian name';
        // Hide signup link for guardians
        document.getElementById('si-signup-link').style.display = 'none';
    }
    setTimeout(() => show('v-signin'), 120);
}

async function doSignIn() {
    const u = document.getElementById('si-user').value.trim();
    const p = document.getElementById('si-pass').value.trim();
    const err = document.getElementById('si-err');
    err.classList.remove('show');

    if (!u || !p) { err.textContent = 'Please fill in all fields.'; err.classList.add('show'); return }
    if (!currentRole) { err.textContent = 'Please select a role first.'; err.classList.add('show'); return }

    try {
        const r = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p, role: currentRole })
        });
        const d = await r.json();
        if (!r.ok) { err.textContent = d.detail; err.classList.add('show'); return }

        if (d.role === 'caretaker') {
            sessionStorage.setItem('cf_role', 'caretaker');
            sessionStorage.setItem('cf_id', d.id);
            sessionStorage.setItem('cf_name', d.name);
            window.location.href = '/caretaker';
        } else {
            sessionStorage.setItem('cf_role', 'guardian');
            sessionStorage.setItem('cf_pid', d.patient_id);
            sessionStorage.setItem('cf_name', d.name);
            window.location.href = '/guardian';
        }
    } catch {
        err.textContent = 'Cannot connect to server.';
        err.classList.add('show');
    }
}

async function doSignUp() {
    const err = document.getElementById('su-err');
    const ok = document.getElementById('su-ok');
    err.classList.remove('show');
    ok.classList.remove('show');

    const name = document.getElementById('su-name').value.trim();
    const age = document.getElementById('su-age').value;
    const gen = document.getElementById('su-gender').value;
    const con = document.getElementById('su-contact').value.trim();
    const exp = document.getElementById('su-exp').value;
    const qual = document.getElementById('su-qual').value.trim();
    const skiRaw = document.getElementById('su-skills').value.trim();

    if (!name || !age || !gen || !con || !exp || !qual || !skiRaw) {
        err.textContent = 'Please fill in all fields.';
        err.classList.add('show');
        return;
    }

    // Split comma-separated skills into array
    const skills = skiRaw.split(',').map(s => s.trim()).filter(s => s.length > 0);

    try {
        const r = await fetch('/api/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                age: parseInt(age),
                gender: gen,
                contact: con,
                experience_years: parseInt(exp),
                qualification: qual,
                skills
            })
        });
        const d = await r.json();
        if (!r.ok) { err.textContent = d.detail; err.classList.add('show'); return }

        ok.innerHTML = `
      <strong>✓ Account Created!</strong>
      <div class="cred-box">
        Caretaker ID: <b>${d.caretaker_id}</b><br>
        Password: <b>${d.password}</b>
        <small>⚠ Save these credentials — they won't be shown again.</small>
      </div>`;
        ok.classList.add('show');

        // Clear form
        ['su-name', 'su-age', 'su-gender', 'su-contact', 'su-exp', 'su-qual', 'su-skills']
            .forEach(id => { document.getElementById(id).value = ''; });

    } catch {
        err.textContent = 'Cannot connect to server.';
        err.classList.add('show');
    }
}

document.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    const a = document.querySelector('.view.active');
    if (a.id === 'v-signin') doSignIn();
    if (a.id === 'v-signup') doSignUp();
});