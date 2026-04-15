// ── Expenses ──────────────────────────────────────────────────────────────────
// Changes from old version:
// - All field names lowercased: expense_id, expense_name, expense_category etc.
// - Table renamed from Expenses to Expense in DB — no JS change needed
//   since we only use API endpoints, not direct table names

async function loadExps() {
    const pid = document.getElementById('e-patsel').value;
    const tb = document.querySelector('#exp-tbl tbody');

    if (!pid) {
        tb.innerHTML = `<tr><td colspan="5"><div class="empty">
            <div class="empty-icon">💰</div>
            <p>Select a patient to view expenses.</p>
        </div></td></tr>`;
        return;
    }

    const r = await fetch(`/api/expenses/${pid}`);
    const exps = await r.json();

    if (!exps.length) {
        tb.innerHTML = `<tr><td colspan="5"><div class="empty">
            <div class="empty-icon">💰</div>
            <p>No expenses logged.</p>
        </div></td></tr>`;
        return;
    }

    tb.innerHTML = exps.map(e => `
        <tr>
            <td><strong>${e.expense_name}</strong></td>
            <td><span class="badge b-tag">${e.expense_category}</span></td>
            <td>Rs. ${parseFloat(e.expense_amount).toFixed(2)}</td>
            <td>${fdt(e.expense_time)}</td>
            <td><button class="btn btn-danger btn-sm" onclick="delExp('${e.expense_id}')">Remove</button></td>
        </tr>`).join('');
}

async function addExp() {
    const pid = document.getElementById('e-patsel').value;
    if (!pid) { toast('Select a patient first', 'err'); return }

    const body = {
        name: document.getElementById('ef-name').value.trim(),
        category: document.getElementById('ef-cat').value,
        amount: parseFloat(document.getElementById('ef-amt').value) || 0,
        patient_id: pid,
    };

    if (!body.name || !body.amount) { toast('Name and amount required', 'err'); return }

    const r = await fetch('/api/expense', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    if (r.ok) {
        toast('Expense added');
        toggleSec('exp-form');
        loadExps();
    }
}

async function delExp(id) {
    if (!confirm('Remove this expense?')) return;
    const r = await fetch(`/api/expense/${id}`, { method: 'DELETE' });
    if (r.ok) { toast('Expense removed'); loadExps(); }
}