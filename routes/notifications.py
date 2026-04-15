import random
from fastapi import APIRouter, Depends
from database import get_db
from models import NotifCreate
from datetime import datetime

router = APIRouter()

# ── Create Notification table if not exists ───────────────────────────────────
def create_notification_table(db):
    cur = db.cursor()
    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Notification (
                    NotificationID    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    Notif_Time        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    Notif_Name        VARCHAR2(100),
                    Notif_Description VARCHAR2(500),
                    CaretakerID       VARCHAR2(20) REFERENCES Caretaker(CaretakerID),
                    TaskID            NUMBER REFERENCES Task(TaskID) ON DELETE CASCADE,
                    AppointmentID     NUMBER REFERENCES Appointment(AppointmentID) ON DELETE CASCADE
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)
    db.commit()
    cur.close()

# ── Shared helper — used by tasks.py and appointments.py ─────────────────────
def send_notification(db, caretaker_id: str, name: str, description: str,
                      task_id=None, appointment_id=None, scheduled_time=None):
    cur = db.cursor()
    
    # Logic for custom timing
    if scheduled_time:
        # If it's a string from the frontend, ensure it's ISO format
        # If it's already a datetime object, convert to isoformat for Oracle
        if isinstance(scheduled_time, datetime):
            notif_time = scheduled_time.isoformat()
        else:
            notif_time = scheduled_time
    else:
        notif_time = datetime.now().isoformat()
    
    cur.execute("""
        INSERT INTO Notification (Notif_Time, Notif_Name,
                                  Notif_Description, CaretakerID,
                                  TaskID, AppointmentID)
        VALUES (TO_TIMESTAMP(:1, 'YYYY-MM-DD"T"HH24:MI:SS.FF'), :2, :3, :4, :5, :6)
    """, (notif_time, name, description, caretaker_id, task_id, appointment_id))

# ── Get notifications for a caretaker ────────────────────────────────────────
@router.get("/api/notifications/{cid}")
def get_notifications(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT NotificationID, Notif_Time, Notif_Name,
               Notif_Description, CaretakerID,
               TaskID, AppointmentID
        FROM   Notification
        WHERE  CaretakerID = :1
        ORDER BY Notif_Time DESC
    """, (cid,))
    
    rows = cur.fetchall()
    keys = ["notification_id", "notif_time", "notif_name",
            "notif_description", "caretaker_id",
            "task_id", "appointment_id"]
    
    # Manual formatting loop (No format_rows helper used)
    result = []
    for r in rows:
        d = {keys[i]: r[i] for i in range(len(keys))}
        
        # Convert Oracle TIMESTAMP object to string for JSON compatibility
        if isinstance(d["notif_time"], datetime):
            d["notif_time"] = d["notif_time"].strftime("%Y-%m-%d %H:%M")
            
        result.append(d)
        
    return result

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
    cur.execute("DELETE FROM Notification WHERE NotificationID=:1", (nid,))
    db.commit()
    return {"message": "Notification deleted"}