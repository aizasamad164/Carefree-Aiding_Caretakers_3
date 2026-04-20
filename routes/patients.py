import random, string
from fastapi import APIRouter, HTTPException, Depends
from database import get_db, row_to_dict
from models import PatientCreate, PatientUpdate, CommentBody, BalanceBody

router = APIRouter()


# ── ID generators ─────────────────────────────────────────────────────────────
def gen_id(prefix, table, col, db):
    cur = db.cursor()
    try:
        while True:
            nid = f"{prefix}-{random.randint(10000,99999)}"
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col}=:1", (nid,))
            if cur.fetchone()[0] == 0:
                return nid
    finally:
        cur.close()

def gen_pw(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


# ── Get all patients for a caretaker ──────────────────────────────────────────
@router.get("/api/patients/{cid}")
def get_patients(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT p.PatientID, p.Patient_Name,
                   g.Guardian_Name, g.Guardian_Contact,
                   g.Guardian_Comment, p.Balance, p.Charges
            FROM   Patient p
            LEFT JOIN Guardian g ON g.PatientID = p.PatientID
            WHERE  p.CaretakerID = :1
            ORDER BY p.Patient_Name
        """, (cid,))
        rows = cur.fetchall()
        keys = ["patient_id", "patient_name", "guardian_name",
                "guardian_contact", "guardian_comment", "balance", "charges"]
        return [{keys[i]: r[i] for i in range(len(keys))} for r in rows]
    finally:
        cur.close()


# ── Get single patient ────────────────────────────────────────────────────────
@router.get("/api/patient/{pid}")
def get_patient(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT p.*, g.GuardianID, g.Guardian_Name, g.Guardian_Password,
                   g.Guardian_Contact, g.Guardian_Comment, g.Relation_with_patient
            FROM   Patient p
            LEFT JOIN Guardian g ON g.PatientID = p.PatientID
            WHERE  p.PatientID = :1
        """, (pid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Patient not found")
        return row_to_dict(cur, row)
    finally:
        cur.close()


# ── Create patient + guardian ─────────────────────────────────────────────────
@router.post("/api/patient")
def create_patient(p: PatientCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        pid = gen_id("P", "Patient",  "PatientID",  db)
        gid = gen_id("G", "Guardian", "GuardianID", db)
        pw  = gen_pw()

        cur.execute("""
            INSERT INTO Patient (PatientID, Patient_Name, Age, Gender,
                                 Height, Weight, Smoker, Children,
                                 Region, CaretakerID)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10)
        """, (pid, p.name, p.age, p.gender,
              p.height, p.weight, p.smoker, p.children,
              p.region, p.caretaker_id))

        cur.execute("""
            INSERT INTO Guardian (GuardianID, Guardian_Name, Guardian_Password,
                                  Guardian_Contact, Relation_with_patient, PatientID)
            VALUES (:1,:2,:3,:4,:5,:6)
        """, (gid, p.guardian_name, pw,
              p.guardian_contact, p.relation_with_patient, pid))

        db.commit()
        return {"patient_id": pid, "guardian_id": gid, "guardian_password": pw}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating patient: {str(e)}")
    finally:
        cur.close()


# ── Update patient + guardian ─────────────────────────────────────────────────
@router.put("/api/patient/{pid}")
def update_patient(pid: str, p: PatientUpdate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE Patient
            SET    Patient_Name=:1, Age=:2, Gender=:3,
                   Height=:4, Weight=:5, Smoker=:6,
                   Children=:7, Region=:8
            WHERE  PatientID=:9
        """, (p.name, p.age, p.gender,
              p.height, p.weight, p.smoker,
              p.children, p.region, pid))

        cur.execute("""
            UPDATE Guardian
            SET    Guardian_Name=:1, Guardian_Contact=:2,
                   Relation_with_patient=:3
            WHERE  PatientID=:4
        """, (p.guardian_name, p.guardian_contact,
              p.relation_with_patient, pid))

        db.commit()
        return {"message": "Updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error updating patient: {str(e)}")
    finally:
        cur.close()


# ── Delete patient ────────────────────────────────────────────────────────────
@router.delete("/api/patient/{pid}")
def delete_patient(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM Guardian     WHERE PatientID  = :1", (pid,))
        cur.execute("""DELETE FROM Notification WHERE CaretakerID =
                       (SELECT CaretakerID FROM Patient WHERE PatientID = :1)""", (pid,))
        cur.execute("DELETE FROM Task         WHERE PatientID  = :1", (pid,))
        cur.execute("DELETE FROM Appointment  WHERE PatientID  = :1", (pid,))
        cur.execute("DELETE FROM Expense      WHERE PatientID  = :1", (pid,))
        cur.execute("DELETE FROM Patient      WHERE PatientID  = :1", (pid,))
        db.commit()
        return {"message": "Patient deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error deleting patient: {str(e)}")
    finally:
        cur.close()


# ── Update guardian comment ───────────────────────────────────────────────────
@router.put("/api/patient/{pid}/comment")
def update_comment(pid: str, b: CommentBody, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE Guardian
            SET    Guardian_Comment = :1
            WHERE  PatientID = :2
        """, (b.comment, pid))
        db.commit()
        return {"message": "Comment saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error saving comment: {str(e)}")
    finally:
        cur.close()


# ── Add balance ───────────────────────────────────────────────────────────────
@router.put("/api/patient/{pid}/balance/add")
def add_balance(pid: str, b: BalanceBody, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("UPDATE Patient SET Balance=Balance+:1 WHERE PatientID=:2",
                    (b.amount, pid))
        db.commit()
        cur.execute("SELECT Balance FROM Patient WHERE PatientID=:1", (pid,))
        row = cur.fetchone()
        return {"balance": float(row[0])}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error adding balance: {str(e)}")
    finally:
        cur.close()


# ── Remove balance ────────────────────────────────────────────────────────────
@router.put("/api/patient/{pid}/balance/remove")
def remove_balance(pid: str, b: BalanceBody, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT Balance FROM Patient WHERE PatientID=:1", (pid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Patient not found")
        if float(row[0]) < b.amount:
            raise HTTPException(400, "Insufficient balance")
        cur.execute("UPDATE Patient SET Balance=Balance-:1 WHERE PatientID=:2",
                    (b.amount, pid))
        db.commit()
        cur.execute("SELECT Balance FROM Patient WHERE PatientID=:1", (pid,))
        row = cur.fetchone()
        return {"balance": float(row[0])}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error removing balance: {str(e)}")
    finally:
        cur.close()


# ── Get guardian password ─────────────────────────────────────────────────────
@router.get("/api/patient/{pid}/password")
def get_guardian_password(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT Guardian_Password FROM Guardian WHERE PatientID=:1", (pid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Guardian not found for this patient")
        return {"password": row[0]}
    finally:
        cur.close()