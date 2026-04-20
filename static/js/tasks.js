// ── Tasks ─────────────────────────────────────────────────────────────────────
// Changes from old version:
// - All field names lowercased: task_id, task_name, task_time etc.
// - Priority changed from int (1/2/3) to string ("High"/"Medium"/"Low")
//   because Task_Priority is now VARCHAR2(10) in the DB
// - Badge mapping updated to use string keys instead of numeric keys
// - refresh endpoint called on panel load to update recurring task times
//   and fire notifications for tasks due today

async function loadTasks() {
    const pid = document.getElementById('t-patsel').value;
    const tb = document.querySelector('#task-tbl tbody');

    // Clear immediately — fixes stale data bug
    tb.innerHTML = '';

    if (!pid) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty">
            <div class="empty-icon">✅</div>
            <p>Select a patient to view their tasks.</p>
        </div></td></tr>`;
        return;
    }

    // Refresh recurring task times before fetching
    await fetch(`/api/tasks/refresh/${CF.id}`, { method: 'POST' });

    const r = await fetch(`/api/tasks/${pid}?filter=${filters.tasks}`);
    const tasks = await r.json();

    if (!tasks.length) {
        tb.innerHTML = `<tr><td colspan="6"><div class="empty">
            <div class="empty-icon">✅</div>
            <p>No tasks found.</p>
        </div></td></tr>`;
        return;
    }

    const pm = { 'High': 'high', 'Medium': 'medium', 'Low': 'low' };
    tb.innerHTML = tasks.map(t => `
        <tr>
            <td><strong>${t.task_name}</strong></td>
            <td>${fdt(t.task_time)}</td>
            <td>${t.task_frequency}</td>
            <td><span class="badge b-${pm[t.task_priority] || 'low'}">${t.task_priority}</span></td>
            <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                ${t.task_description || '—'}
            </td>
            <td><button class="btn btn-danger btn-sm" onclick="delTask(${t.task_id})">Remove</button></td>
        </tr>`).join('');
}

async function addTask() {
    const pid = document.getElementById('t-patsel').value;
    if (!pid) { toast('Select a patient first', 'err'); return }

    const body = {
        name: document.getElementById('tf-name').value.trim(),
        time: document.getElementById('tf-time').value,
        frequency: document.getElementById('tf-freq').value,
        priority: document.getElementById('tf-pri').value,  // now a string: "High"/"Medium"/"Low"
        description: document.getElementById('tf-desc').value.trim(),
        patient_id: pid,
        // caretaker_id resolved server-side from PatientID — not sent from frontend
    };

    if (!body.name || !body.time) { toast('Name and time are required', 'err'); return }

    const r = await fetch('/api/task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    if (r.ok) {
        toast('Task added');
        toggleSec('task-form');
        loadTasks();
    }
}

async function delTask(id) {
    if (!confirm('Remove this task?')) return;
    const r = await fetch(`/api/task/${id}`, { method: 'DELETE' });
    if (r.ok) { toast('Task removed'); loadTasks(); }
}

