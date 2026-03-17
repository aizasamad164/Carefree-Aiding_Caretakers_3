import random
from fastapi import APIRouter, Depends
from database import get_db
from models import NotifCreate
from datetime import datetime

router = APIRouter()

# ── Get notifications for a caretaker ────────────────────────────────────────
@router.get("/api/notifications/{cid}")
def get_notifications(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Notification_ID, Caretaker_ID, Notif_Time,
                          Notif_Name, Notif_Description
                   FROM Notification WHERE Caretaker_ID=:1
                   ORDER BY Notif_Time DESC""", (cid,))
    rows = cur.fetchall()
    keys = ["notification_id","caretaker_id","notif_time",
            "notif_name","notif_description"]
    return [{keys[i]:r[i] for i in range(len(keys))} for r in rows]

# ── Create notification manually ──────────────────────────────────────────────
@router.post("/api/notification")
def create_notification(n: NotifCreate, db=Depends(get_db)):
    cur = db.cursor()
    nid = f"N-{random.randint(10000,99999)}"
    now = datetime.now().isoformat()
    cur.execute("INSERT INTO Notification VALUES (:1,:2,:3,:4,:5)",
                (nid, n.caretaker_id, now, n.name, n.description))
    db.commit()
    return {"message":"Notification added","notification_id":nid}

# ── Delete notification ───────────────────────────────────────────────────────
@router.delete("/api/notification/{nid}")
def delete_notification(nid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM Notification WHERE Notification_ID=:1", (nid,))
    db.commit()
    return {"message":"Notification deleted"}
