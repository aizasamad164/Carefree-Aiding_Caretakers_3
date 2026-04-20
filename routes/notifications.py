from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import NotifCreate
from datetime import datetime, timedelta

router = APIRouter()


# ── Shared helper ─────────────────────────────────────────────────────────────
def send_notification(db, caretaker_id: str, name: str, description: str,
                      task_id=None, appointment_id=None, scheduled_time=None,
                      message: str = None):
    cur = db.cursor()
    try:
        if scheduled_time:
            notif_time = scheduled_time.isoformat() if isinstance(scheduled_time, datetime) else scheduled_time
        else:
            notif_time = datetime.now().isoformat()

        cur.execute("""
            INSERT INTO Notification (
                Notif_Time, Notif_Name, Message, Notif_Description,
                Is_Sent, CaretakerID, TaskID, AppointmentID
            )
            VALUES (
                TO_TIMESTAMP(:1, 'YYYY-MM-DD"T"HH24:MI:SS.FF'),
                :2, :3, :4, 0, :5, :6, :7
            )
        """, (notif_time, name, message or name, description,
              caretaker_id, task_id, appointment_id))
    finally:
        cur.close()


# ── Get notifications (due, unsent) ──────────────────────────────────────────
@router.get("/api/notifications/{cid}")
def get_notifications(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT NotificationID, Notif_Time, Notif_Name,
                   Notif_Description, CaretakerID, TaskID, AppointmentID
            FROM   Notification
            WHERE  CaretakerID = :1
              AND  Notif_Time <= CURRENT_TIMESTAMP
              AND  Is_Sent     = 0
            ORDER BY Notif_Time DESC
        """, (cid,))
        rows = cur.fetchall()
        keys = ["notification_id", "notif_time", "notif_name",
                "notif_description", "caretaker_id", "task_id", "appointment_id"]
        result = []
        for r in rows:
            d = {}
            for i, val in enumerate(r):
                if hasattr(val, 'read'):
                    val = val.read()
                d[keys[i]] = val
            if isinstance(d["notif_time"], datetime):
                d["notif_time"] = d["notif_time"].strftime("%Y-%m-%d %H:%M")
            result.append(d)
        return result
    finally:
        cur.close()


# ── Dismiss notification + reschedule recurring tasks ────────────────────────
@router.post("/api/notification/dismiss/{nid}")
def dismiss_notification(nid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT TaskID, AppointmentID, CaretakerID,
                   Notif_Name, Notif_Description, Notif_Time
            FROM   Notification WHERE NotificationID = :1
        """, (nid,))
        row = cur.fetchone()
        if not row:
            return {"message": "Not found"}

        task_id, appt_id, cid, name, desc, notif_time = row
        cur.execute("UPDATE Notification SET Is_Sent = 1 WHERE NotificationID = :1", (nid,))

        if task_id:
            cur.execute("""
                SELECT Task_Time, Task_Frequency, Task_Name
                FROM   Task WHERE TaskID = :1
            """, (task_id,))
            task_row = cur.fetchone()
            if task_row:
                task_time, frequency, task_name = task_row
                now = datetime.now()
                next_time = None

                if frequency == "Daily":
                    next_time = task_time
                    while next_time <= now:
                        next_time += timedelta(days=1)
                elif frequency == "Alternate":
                    next_time = task_time
                    while next_time <= now:
                        next_time += timedelta(days=2)
                elif frequency == "Weekly":
                    next_time = task_time
                    while next_time <= now:
                        next_time += timedelta(weeks=1)
                elif frequency == "Monthly":
                    next_time = task_time
                    while next_time <= now:
                        month = next_time.month + 1
                        year  = next_time.year + (month - 1) // 12
                        month = (month - 1) % 12 + 1
                        next_time = next_time.replace(year=year, month=month)

                if next_time:
                    send_notification(db, cid,
                        f"Task Reminder: {task_name}", desc,
                        task_id=task_id, scheduled_time=next_time)

        db.commit()
        return {"message": "Dismissed"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Dismiss error: {str(e)}")
    finally:
        cur.close()


# ── Create notification manually ──────────────────────────────────────────────
@router.post("/api/notification")
def create_notification(n: NotifCreate, db=Depends(get_db)):
    send_notification(db, n.caretaker_id, n.name, n.description)
    db.commit()
    return {"message": "Notification added"}


# ── Delete notification ───────────────────────────────────────────────────────
@router.delete("/api/notification/{nid}")
def delete_notification(nid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM Notification WHERE NotificationID = :1", (nid,))
        db.commit()
        return {"message": "Notification deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Delete error: {str(e)}")
    finally:
        cur.close()