import random
from fastapi import APIRouter, Depends
from database import get_db
from models import ApptCreate
from datetime import datetime

router = APIRouter()

# ── Get appointments for a patient ───────────────────────────────────────────
@router.get("/api/appointments/{pid}")
def get_appts(pid: str, filter: str="All", db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Appointment_ID, Client_Name, Appointment_Category,
                          Appointment_DateTime, P_ID, Appointment_Description
                   FROM Appointment WHERE P_ID=:1
                   ORDER BY Appointment_DateTime""", (pid,))
    rows = cur.fetchall()
    keys = ["appointment_id","client_name","appointment_category",
            "appointment_datetime","p_id","appointment_description"]
    now = datetime.now()
    result = []
    for r in rows:
        d = {keys[i]:r[i] for i in range(len(keys))}
        try:
            dt = datetime.fromisoformat(str(d["appointment_datetime"]))
            if filter=="Today"   and dt.date()!=now.date(): continue
            if filter=="Weekly"  and not (0<=(dt.date()-now.date()).days<7): continue
            if filter=="Monthly" and (dt.year!=now.year or dt.month!=now.month): continue
        except: pass
        result.append(d)
    return result

# ── Create appointment ────────────────────────────────────────────────────────
@router.post("/api/appointment")
def create_appt(a: ApptCreate, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""INSERT INTO Appointment (Client_Name,Appointment_Category,
                   Appointment_DateTime,P_ID,Appointment_Description)
                   VALUES (:1,:2,:3,:4,:5)""",
                (a.client_name,a.category,a.datetime_val,a.patient_id,a.description))

    # ── Auto notification ──────────────────────────────────────────────────────
    cur.execute("SELECT C_ID, Patient_Name FROM Patient WHERE Patient_ID=:1", (a.patient_id,))
    row = cur.fetchone()
    if row:
        cid, pname = row[0], row[1]
        nid = f"N-{random.randint(10000,99999)}"
        now = datetime.now().isoformat()
        cur.execute("INSERT INTO Notification VALUES (:1,:2,:3,:4,:5)",
                    (nid, cid, now,
                     f"New Appointment: {a.client_name}",
                     f"{a.category} for {pname} on {a.datetime_val}"))
    # ──────────────────────────────────────────────────────────────────────────

    db.commit()
    return {"message":"Appointment added"}

# ── Delete appointment ────────────────────────────────────────────────────────
@router.delete("/api/appointment/{aid}")
def delete_appt(aid: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM Appointment WHERE Appointment_ID=:1", (aid,))
    db.commit()
    return {"message":"Appointment deleted"}
