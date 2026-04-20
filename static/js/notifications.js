// ── Notifications ─────────────────────────────────────────────────────────────
// Changes from old version:
// - Field names lowercased: notification_id, notif_name, notif_description, notif_time
// - task_id and appointment_id now shown as context badges when present
//   so caretaker knows whether a notification came from a task or appointment

async function loadNotifs() {
    const r = await fetch(`/api/notifications/${CF.id}`);
    const notifs = await r.json();

    // Update bell counter
    const count = document.getElementById('notif-count');
    if (notifs.length > 0) {
        count.textContent = notifs.length;
        count.style.display = 'grid';
    } else {
        count.style.display = 'none';
    }

    const body = document.getElementById('notif-body');
    if (!notifs.length) {
        body.innerHTML = `<div class="empty">
            <div class="empty-icon">🔔</div>
            <p>No notifications yet.</p>
        </div>`;
        return;
    }

    body.innerHTML = notifs.map(n => {
        // Show context badge if notification came from a task or appointment
        let context = '';
        if (n.task_id) context = `<span class="badge b-tag" style="margin-bottom:6px;display:inline-flex">📋 Task #${n.task_id}</span>`;
        if (n.appointment_id) context = `<span class="badge b-tag" style="margin-bottom:6px;display:inline-flex">📅 Appointment #${n.appointment_id}</span>`;

        return `
        <div class="notif-item">
            <button class="notif-del" onclick="dismissNotif('${n.notification_id}')">✕</button>
            ${context}
            <div class="notif-name">${n.notif_name}</div>
            <div class="notif-desc">${n.notif_description || '—'}</div>
            <div class="notif-time">${fdt(n.notif_time)}</div>
        </div>`;
    }).join('');
}

async function addNotif() {
    const name = document.getElementById('notif-name').value.trim();
    const desc = document.getElementById('notif-desc').value.trim();
    if (!name) { toast('Enter a title', 'err'); return }

    const r = await fetch('/api/notification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ caretaker_id: CF.id, name, description: desc })
        // task_id and appointment_id are null for manual notifications
    });

    if (r.ok) {
        document.getElementById('notif-name').value = '';
        document.getElementById('notif-desc').value = '';
        toast('Notification added');
        loadNotifs();
    }
}

async function delNotif(id) {
    const r = await fetch(`/api/notification/${id}`, { method: 'DELETE' });
    if (r.ok) { toast('Removed'); loadNotifs(); }
}

// ── Dismiss notification (marks sent + auto-reschedules recurring tasks) ──
async function dismissNotif(id) {
    await fetch(`/api/notification/dismiss/${id}`, { method: 'POST' });
    loadNotifs();
}

function toggleNotif() {
    document.getElementById('notif-panel').classList.toggle('open');
    document.getElementById('notif-overlay').classList.toggle('open');
    // Reload notifications when panel opens so count is always fresh
    if (document.getElementById('notif-panel').classList.contains('open')) {
        loadNotifs();
    }
}