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
        # 1. GENERATION STEP: Look for missing occurrences of recurring tasks
        cur.execute("""
            SELECT TaskID, Task_Frequency, Task_Name, Task_Description, Task_Time 
            FROM Task WHERE CaretakerID = :1
        """, (cid,))
        all_tasks = cur.fetchall()

        now = datetime.now()

        for tid, freq, name, desc, ori_time in all_tasks:
            if not freq:
                continue

            # Check for the latest notification created (sent or unsent)
            cur.execute("SELECT MAX(Notif_Time) FROM Notification WHERE TaskID = :1", (tid,))
            last_entry = cur.fetchone()[0]

            # Use the latest notification time as the base, or the original task time
            reference_time = last_entry if last_entry else ori_time
            
            # Calculate when the NEXT one should appear
            next_occurrence = None
            if freq == "Daily":
                next_occurrence = reference_time + timedelta(days=1)
            elif freq == "Alternate":
                next_occurrence = reference_time + timedelta(days=2)
            elif freq == "Weekly":
                next_occurrence = reference_time + timedelta(weeks=1)
            elif freq == "Monthly":
                month = reference_time.month + 1
                year = reference_time.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                next_occurrence = reference_time.replace(year=year, month=month)

            # If the clock has passed the next occurrence time...
            if next_occurrence and next_occurrence <= now:
                # SELECT CHECK: Double check this exact timestamp doesn't exist already
                cur.execute("""
                    SELECT COUNT(*) FROM Notification 
                    WHERE TaskID = :1 AND Notif_Time = :2
                """, (tid, next_occurrence))
                
                if cur.fetchone()[0] == 0:
                    # CREATE it (Default Is_Sent = 0)
                    send_notification(db, cid, f"Task Reminder: {name}", desc or "", 
                                      task_id=tid, scheduled_time=next_occurrence)
                    db.commit() # Commit each generation to ensure data is saved

        # 2. FETCH STEP: Return all that are due and not dismissed
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
                # Handle potential LOB types or byte streams
                if hasattr(val, 'read'):
                    val = val.read()
                d[keys[i]] = val
            
            # Format date for the frontend
            if isinstance(d["notif_time"], datetime):
                d["notif_time"] = d["notif_time"].strftime("%Y-%m-%d %H:%M")
            result.append(d)
            
        return result

    finally:
        cur.close()

# ── Dismiss notification + reschedule recurring tasks ────────────────────────
@router.post("/api/notification/dismiss/{nid}")
@router.post("/api/notification/dismiss/{nid}")
def dismiss_notification(nid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        # Just mark it as 1. The GET route handles the rest.
        cur.execute("UPDATE Notification SET Is_Sent = 1 WHERE NotificationID = :1", (nid,))
        db.commit()
        return {"message": "Dismissed"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        cur.close()


# ── Create notification manually ──────────────────────────────────────────────
@router.post("/api/notification")
def create_notification(n: NotifCreate, db=Depends(get_db)):
    send_notification(db, n.caretaker_id, n.name, n.description)
    db.commit()
    return {"message": "Notification added"}


# ── Get notifications for a specific patient (Guardian Portal) ───────────────
@router.get("/api/notifications/guardian/{pid}")
def get_guardian_notifications(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        # Join with Task and Appointment to find notifications belonging to THIS patient
        # We also check (CURRENT_TIMESTAMP + 1) to give that 24hr lead time
        cur.execute("""
            SELECT n.NotificationID, n.Notif_Time, n.Notif_Name, 
                   n.Notif_Description, n.AppointmentID, n.TaskID
            FROM   Notification n
            LEFT JOIN Task t ON n.TaskID = t.TaskID
            LEFT JOIN Appointment a ON n.AppointmentID = a.AppointmentID
            WHERE  (t.PatientID = :1 OR a.PatientID = :1)
              AND  n.Notif_Time <= (CURRENT_TIMESTAMP + INTERVAL '1' DAY)
              AND  n.Is_Sent = 0
            ORDER BY n.Notif_Time DESC
        """, (pid,))
        
        rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "notification_id": r[0],
                "notif_time": r[1].strftime("%Y-%m-%d %H:%M") if r[1] else "",
                "notif_name": r[2],
                "notif_description": r[3]
            })
        return result
    finally:
        cur.close()

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