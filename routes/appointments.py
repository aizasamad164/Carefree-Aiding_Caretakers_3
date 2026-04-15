import random
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import ApptCreate
from datetime import datetime
from routes.notifications import send_notification
from datetime import timedelta

router = APIRouter()

# ── Create tables if not exist ────────────────────────────────────────────────
def create_appointment_tables(db):
    cur = db.cursor()

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Doctor (
                    DoctorID        VARCHAR2(20)    PRIMARY KEY,
                    Doctor_Name     VARCHAR2(100)   NOT NULL,
                    Specialization  VARCHAR2(100)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Appointment (
                    AppointmentID           NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    Appointment_Category    VARCHAR2(50),
                    Appointment_DateTime    TIMESTAMP,
                    Appointment_Description VARCHAR2(500),
                    Status                  VARCHAR2(20)    DEFAULT ''Scheduled'',
                    PatientID               VARCHAR2(20)    REFERENCES Patient(PatientID),
                    DoctorID                VARCHAR2(20)    REFERENCES Doctor(DoctorID)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    db.commit()
    cur.close()


# ── Helper: get or create doctor, return DoctorID ────────────────────────────
def get_or_create_doctor(doctor_name: str, specialization: str, db):
    cur = db.cursor()
    cur.execute("SELECT DoctorID FROM Doctor WHERE Doctor_Name=:1", (doctor_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    did = f"D-{random.randint(10000,99999)}"
    cur.execute("INSERT INTO Doctor (DoctorID, Doctor_Name, Specialization) VALUES (:1,:2,:3)",
                (did, doctor_name, specialization))
    return did


# ── Get appointments for a patient ───────────────────────────────────────────
@router.get("/api/appointments/{pid}")
def get_appts(pid: str, filter: str = "All", db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT a.AppointmentID, d.Doctor_Name, a.Appointment_Category,
               a.Appointment_DateTime, a.PatientID,
               a.Appointment_Description, a.Status, d.Specialization
        FROM   Appointment a
        JOIN   Doctor d ON d.DoctorID = a.DoctorID
        WHERE  a.PatientID = :1
        ORDER BY a.Appointment_DateTime
    """, (pid,))
    rows = cur.fetchall()
    keys = ["appointment_id", "doctor_name", "appointment_category",
            "appointment_datetime", "patient_id",
            "appointment_description", "status", "specialization"]
    now = datetime.now()
    result = []
    for r in rows:
        d = {keys[i]: r[i] for i in range(len(keys))}
        try:
            dt = datetime.fromisoformat(str(d["appointment_datetime"]))
            if filter == "Today"   and dt.date() != now.date(): continue
            if filter == "Weekly"  and not (0 <= (dt.date() - now.date()).days < 7): continue
            if filter == "Monthly" and (dt.year != now.year or dt.month != now.month): continue
        except:
            pass
        result.append(d)
    return result


# ── Create appointment ────────────────────────────────────────────────────────
@router.post("/api/appointment")
def create_appt(a: ApptCreate, db=Depends(get_db)):
    cur = db.cursor()

    # Fetch CaretakerID and Patient_Name upfront
    cur.execute("SELECT CaretakerID, Patient_Name FROM Patient WHERE PatientID=:1",
                (a.patient_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Patient not found")
    cid, pname = row[0], row[1]

    # Resolve doctor to ID (creates if new)
    doc_id = get_or_create_doctor(a.doctor_name, a.specialization, db)

    # Insert appointment and capture generated AppointmentID
    vid_var = cur.var(__import__('cx_Oracle').NUMBER)
    cur.execute("""
        INSERT INTO Appointment (Appointment_Category, Appointment_DateTime,
                                 Appointment_Description, Status, PatientID, DoctorID)
        VALUES (:1,TO_TIMESTAMP(:2, 'YYYY-MM-DD"T"HH24:MI:SS.FF'),:3,:4,:5,:6)
        RETURNING AppointmentID INTO :7
    """, (a.category, a.datetime_val, a.description,
          a.status or "Scheduled", a.patient_id, doc_id, vid_var))
   
    val = vid_var.getvalue()
    if isinstance(val, list):
        appt_id = int(val[0])
    else:
        appt_id = int(val)

    # Convert input string to datetime
    appt_dt = datetime.fromisoformat(a.datetime_val.replace('Z', ''))
    # Calculate notification time (24 hours before)
    notif_dt = appt_dt - timedelta(days=1)

    send_notification(
        db, 
        cid,
        f"Appointment Reminder: {a.doctor_name}",
        f"Upcoming visit for {pname} tomorrow at {appt_dt.strftime('%H:%M')}",
        appointment_id=appt_id,
        scheduled_time=notif_dt # Set notification for one day before
    )

    # ── Auto notification via shared helper ───────────────────────────────────
    send_notification(db, cid,
        f"New Appointment: {a.doctor_name}",
        f"{a.category} for {pname} on {a.datetime_val}",
        appointment_id=appt_id)
    # ─────────────────────────────────────────────────────────────────────────
    db.commit()
    return {"message": "Appointment added", "appointment_id": appt_id}


# ── Delete appointment ────────────────────────────────────────────────────────
@router.delete("/api/appointment/{aid}")
def delete_appt(aid: int, db=Depends(get_db)):
    cur = db.cursor()
    # Remove linked notifications first
    cur.execute("DELETE FROM Notification WHERE AppointmentID=:1", (aid,))
    cur.execute("DELETE FROM Appointment WHERE AppointmentID=:1", (aid,))
    db.commit()
    return {"message": "Appointment deleted"}