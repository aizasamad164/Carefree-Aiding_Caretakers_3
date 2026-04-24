// ── Expenses ──────────────────────────────────────────────────────────────────
// Changes from old version:
// - All field names lowercased: expense_id, expense_name, expense_category etc.
// - Table renamed from Expenses to Expense in DB — no JS change needed
//   since we only use API endpoints, not direct table names

async function loadExps() {
    const pid = document.getElementById('e-patsel').value;
    const tb = document.querySelector('#exp-tbl tbody');
    const balanceBox = document.getElementById('patient-balance-display');

    if (!pid) {
        tb.innerHTML = '<tr><td colspan="5">Select a patient.</td></tr>';
        balanceBox.innerText = "Rs. 0.00";
        return;
    }

    const r = await fetch(`/api/expenses/${pid}`);
    const data = await r.json();

    // Update the Balance Display using the calculated value from the API
    const currentBal = data.calculated_balance;
    balanceBox.innerText = `Rs. ${currentBal.toFixed(2)}`;

    // UI Feedback: Red if negative, green if positive
    balanceBox.style.color = currentBal < 0 ? "#e74c3c" : "#2ecc71";

    if (!data.expenses.length) {
        tb.innerHTML = '<tr><td colspan="5">No expenses logged.</td></tr>';
        return;
    }

    tb.innerHTML = data.expenses.map(e => `
        <tr>
            <td><strong>${e.expense_name}</strong></td>
            <td><span class="badge b-tag">${e.expense_category}</span></td>
            <td>Rs. ${parseFloat(e.expense_amount).toFixed(2)}</td>
            <td>${e.expense_time}</td>
            <td><button class="btn btn-danger btn-sm" onclick="delExp('${e.expense_id}')">Remove</button></td>
        </tr>`).join('');
}


async function addExp() {
    const pid = document.getElementById('e-patsel').value;
    if (!pid) { toast('Select a patient first', 'err'); return; }

    const name = document.getElementById('ef-name').value.trim();
    const amount = parseFloat(document.getElementById('ef-amt').value) || 0;
    const cat = document.getElementById('ef-cat').value;

    if (!name) { toast('Name is required', 'err'); return; }
    if (amount <= 0) { toast('Amount must be greater than zero', 'err'); return; }  // ← blocks negative/zero

    const body = { name, category: cat, amount, patient_id: pid };

    const r = await fetch('/api/expense', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    if (r.ok) {
        toast('Expense added');
        // ── Clear fields ──
        document.getElementById('ef-name').value = '';
        document.getElementById('ef-amt').value = '';
        document.getElementById('ef-cat').selectedIndex = 0;
        toggleSec('exp-form');
        loadExps();
    } else {
        const e = await r.json();
        toast(e.detail || 'Error adding expense', 'err');
    }
}

async function delExp(id) {
    if (!confirm('Remove this expense?')) return;
    const r = await fetch(`/api/expense/${id}`, { method: 'DELETE' });
    if (r.ok) { toast('Expense removed'); loadExps(); }
}