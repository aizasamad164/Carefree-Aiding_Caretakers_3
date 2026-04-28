import secrets
import cx_Oracle as oracledb
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import ApptCreate
from datetime import datetime, timedelta
from routes.notifications import send_notification

router = APIRouter()


# ── Helper: get or create doctor ─────────────────────────────────────────────
def get_or_create_doctor(doctor_name: str, specialization: str, db):
    cur = db.cursor()
    try:
        cur.execute("SELECT DoctorID FROM Doctor WHERE Doctor_Name=:1", (doctor_name,))
        row = cur.fetchone()
        if row:
            return row[0]
        did = f"D-{secrets.randbelow(90000) + 10000}"
        cur.execute("INSERT INTO Doctor (DoctorID, Doctor_Name, Specialization) VALUES (:1,:2,:3)",
                    (did, doctor_name, specialization))
        return did
    finally:
        cur.close()


# ── Stats — MUST be before /api/appointments/{pid} ───────────────────────────
@router.get("/api/appointments/stats/{cid}")
def get_appt_stats(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        now = datetime.now()
        cur.execute("""
            SELECT COUNT(*) FROM Appointment a
            JOIN   Patient p ON p.PatientID = a.PatientID
            WHERE  p.CaretakerID = :1
              AND  a.Appointment_DateTime >= :2
        """, (cid, now))
        count = cur.fetchone()[0]
        return {"count": count}
    finally:
        cur.close()


# ── Get appointments for a patient ───────────────────────────────────────────
@router.get("/api/appointments/{pid}")
def get_appts(pid: str, filter: str = "All", db=Depends(get_db)):
    cur = db.cursor()
    try:
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
            d = {}
            for i, val in enumerate(r):
                if hasattr(val, 'read'):
                    val = val.read()
                d[keys[i]] = val

            raw_dt = d["appointment_datetime"]
            if isinstance(raw_dt, datetime):
                dt = raw_dt
            else:
                try:
                    dt = datetime.strptime(str(raw_dt), "%Y-%m-%d %H:%M:%S")
                except:
                    dt = None

            if dt:
                if filter == "Today"   and dt.date() != now.date():                        continue
                if filter == "Weekly"  and not (0 <= (dt.date() - now.date()).days < 7):   continue
                if filter == "Monthly" and (dt.year != now.year or dt.month != now.month): continue

            d["appointment_datetime"] = dt.strftime("%d-%b-%Y, %I:%M %p") if dt else "—"
            result.append(d)
        return result
    finally:
        cur.close()


# ── Create appointment ────────────────────────────────────────────────────────
@router.post("/api/appointment")
def create_appt(a: ApptCreate, db=Depends(get_db)):
    appt_dt = datetime.fromisoformat(a.datetime_val.replace('Z', ''))
    
    # 2. VALIDATION: Check if the time is in the past
    if appt_dt < datetime.now():
        raise HTTPException(
            status_code=400, 
            detail="Appointments cannot be scheduled in the past."
        )

    cur = db.cursor()
    try:
        cur.execute("SELECT CaretakerID, Patient_Name FROM Patient WHERE PatientID=:1", (a.patient_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Patient not found")
        cid, pname = row[0], row[1]

        clean_name = a.doctor_name.strip().upper()
        cur.execute("SELECT DoctorID FROM Doctor WHERE UPPER(Doctor_Name) = :1", (clean_name,))
        doc_row = cur.fetchone()
        if doc_row:
            doc_id = doc_row[0]
        else:
            doc_id = f"D-{secrets.randbelow(90000) + 10000}"
            cur.execute("INSERT INTO Doctor (DoctorID, Doctor_Name, Specialization) VALUES (:1,:2,:3)",
                        (doc_id, a.doctor_name.strip(), a.specialization))

        vid_var = cur.var(oracledb.DB_TYPE_NUMBER)
        cur.execute("""
            INSERT INTO Appointment (
                Appointment_Category, Appointment_DateTime,
                Appointment_Description, Status, PatientID, DoctorID
            )
            VALUES (:1, TO_TIMESTAMP(:2, 'YYYY-MM-DD"T"HH24:MI:SS.FF'), :3, :4, :5, :6)
            RETURNING AppointmentID INTO :7
        """, (a.category, a.datetime_val, a.description,
              a.status or "Scheduled", a.patient_id, doc_id, vid_var))

        appt_id = int(vid_var.getvalue()[0])

        appt_dt  = datetime.fromisoformat(a.datetime_val.replace('Z', ''))
        notif_dt = appt_dt - timedelta(days=1)

        if notif_dt > datetime.now():
            send_notification(db, cid,
                f"Appointment Reminder: {a.doctor_name}",
                f"Upcoming visit for {pname} tomorrow at {appt_dt.strftime('%H:%M')}",
                appointment_id=appt_id, scheduled_time=notif_dt)
        elif appt_dt > datetime.now():
            send_notification(db, cid,
                f"Appointment Reminder: {a.doctor_name}",
                f"Upcoming visit for {pname} today at {appt_dt.strftime('%H:%M')}",
                appointment_id=appt_id, scheduled_time=datetime.now())

        db.commit()
        return {"message": "Appointment added successfully", "appointment_id": appt_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    finally:
        cur.close()


# ── Delete appointment ─────────────────────────────────────────────
@router.delete("/api/appointment/{aid}")
def delete_appt(aid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        # This triggers the cascade to the Notification table automatically
        cur.execute("DELETE FROM Appointment WHERE AppointmentID = :1", (aid,))
        
        db.commit()
        return {"message": "Appointment and related notifications deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Delete error: {str(e)}")
    finally:
        cur.close()

# ── Get doctors for caretaker ─────────────────────────────────────────────────
@router.get("/api/doctors/{cid}")
def get_doctors(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT d.DoctorID, d.Doctor_Name, d.Specialization
            FROM   Doctor d
            JOIN   Appointment a ON a.DoctorID = d.DoctorID
            JOIN   Patient p     ON p.PatientID = a.PatientID
            WHERE  p.CaretakerID = :1
            ORDER BY d.Doctor_Name
        """, (cid,))
        rows = cur.fetchall()
        return [{"doctor_id": r[0], "doctor_name": r[1], "specialization": r[2]}
                for r in rows]
    finally:
        cur.close()

# get all appointments today
@router.get("/api/appointments/stats/{cid}")
def get_appt_stats(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        today = datetime.now().date()
        cur.execute("""
            SELECT COUNT(*) FROM Appointment a
            JOIN   Patient p ON p.PatientID = a.PatientID
            WHERE  p.CaretakerID = :1
              AND  TRUNC(a.Appointment_DateTime) = :2
        """, (cid, today))
        return {"count": cur.fetchone()[0]}
    finally:
        cur.close()
