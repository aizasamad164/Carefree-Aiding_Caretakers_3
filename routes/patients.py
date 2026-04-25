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
            LEFT JOIN Guardian g ON g.GuardianID = p.GuardianID
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
            LEFT JOIN Guardian g ON g.GuardianID = p.GuardianID
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
    validate_patient(p);

    cur = db.cursor()
    try:
        # 1. SIMPLE CHECK: Does this contact exist anywhere in the Guardian table?
        cur.execute("SELECT GuardianID FROM Guardian WHERE Guardian_Contact = :1", (p.guardian_contact,))
        
        duplicate_contact = cur.fetchone()
        if duplicate_contact:
            raise HTTPException(status_code=400, detail="This contact number is already assigned to another guardian.")

        pid = gen_id("P", "Patient",  "PatientID",  db)
        gid = gen_id("G", "Guardian", "GuardianID", db)
        pw  = gen_pw()

        # 1. Insert into Guardian FIRST (since Patient now depends on GuardianID)
        cur.execute("""
            INSERT INTO Guardian (GuardianID, Guardian_Name, Guardian_Password,
                                  Guardian_Contact, Relation_with_patient)
            VALUES (:1,:2,:3,:4,:5)
        """, (gid, p.guardian_name, pw, p.guardian_contact, p.relation_with_patient))

        # 2. Insert into Patient SECOND (including the GuardianID foreign key)
        cur.execute("""
            INSERT INTO Patient (PatientID, Patient_Name, Age, Gender,
                                 Height, Weight, Smoker, Children,
                                 Region, CaretakerID, GuardianID)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11)
        """, (pid, p.name, p.age, p.gender,
              p.height, p.weight, p.smoker, p.children,
              p.region, p.caretaker_id, gid)) # <-- Added gid here

        db.commit()
        return {"patient_id": pid, "guardian_id": gid, "guardian_password": pw}
    except HTTPException as he:
        # 1. This catches the 400 error you raised for the duplicate contact
        # It lets it "pass through" to the frontend exactly as it is.
        raise he 

    except Exception as e:
        # 2. This catches unexpected stuff (like database connection issues)
        db.rollback()
        raise HTTPException(500, f"System Error: {str(e)}")

    finally:
        cur.close()

# ── Update patient + guardian ─────────────────────────────────────────────────
@router.put("/api/patient/{pid}")
def update_patient(pid: str, p: PatientUpdate, db=Depends(get_db)):
    validate_patient(p)
    cur = db.cursor()
    try:
        # Get current guardian ID for this patient
        cur.execute("SELECT GuardianID FROM Patient WHERE PatientID=:1", (pid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Patient not found")
        current_gid = row[0]

        # Check if new contact is used by a DIFFERENT guardian
        cur.execute("""
            SELECT GuardianID FROM Guardian
            WHERE  Guardian_Contact = :1
              AND  GuardianID != :2
        """, (p.guardian_contact, current_gid))

        if cur.fetchone():
            raise HTTPException(400, "This contact number is already assigned to another guardian.")

        # Update patient
        cur.execute("""
            UPDATE Patient
            SET    Patient_Name=:1, Age=:2, Gender=:3,
                   Height=:4, Weight=:5, Smoker=:6,
                   Children=:7, Region=:8
            WHERE  PatientID=:9
        """, (p.name, p.age, p.gender,
              p.height, p.weight, p.smoker,
              p.children, p.region, pid))

        # Update guardian — name AND contact both updated
        cur.execute("""
            UPDATE Guardian
            SET    Guardian_Name=:1,
                   Guardian_Contact=:2,
                   Relation_with_patient=:3
            WHERE  GuardianID=:4
        """, (p.guardian_name, p.guardian_contact,
              p.relation_with_patient, current_gid))

        db.commit()
        return {"message": "Updated"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"System Error: {str(e)}")
    finally:
        cur.close()


# ── Delete patient ────────────────────────────────────────────────────────────
@router.delete("/api/patient/{pid}")
def delete_patient(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        # Get guardian ID before deleting patient so we can clean up the orphan
        cur.execute("SELECT GuardianID FROM Patient WHERE PatientID=:1", (pid,))
        row = cur.fetchone()
        gid = row[0] if row else None

        # Delete patient — cascades to Task, Appointment, Expense, Notification etc.
        cur.execute("DELETE FROM Patient WHERE PatientID=:1", (pid,))

        # Delete the linked Guardian record (FK is ON DELETE SET NULL so it won't auto-delete)
        if gid:
            cur.execute("DELETE FROM Guardian WHERE GuardianID=:1", (gid,))

        db.commit()
        return {"message": "Patient and all related records deleted successfully"}
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
        # We target Guardian table because that's where the column is in your DDL
        # But we filter by looking up which Guardian belongs to this Patient
        cur.execute("""
            UPDATE Guardian
            SET    Guardian_Comment = :1
            WHERE  GuardianID = (SELECT GuardianID FROM Patient WHERE PatientID = :2)
        """, (b.comment, pid))
        
        if cur.rowcount == 0:
            raise HTTPException(404, "Patient or Guardian not found")

        db.commit()
        return {"message": "Comment saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
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
        # We now join Patient and Guardian to find the password via PatientID
        cur.execute("""
            SELECT g.Guardian_Password 
            FROM Guardian g
            JOIN Patient p ON p.GuardianID = g.GuardianID
            WHERE p.PatientID = :1
        """, (pid,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Guardian not found for this patient")
        return {"password": row[0]}
    finally:
        cur.close()


def validate_patient(p):
    # Age → positive integer
    if not isinstance(p.age, int) or p.age <= 0:
        raise HTTPException(400, "Age must be a positive integer")

    # Children → integer ≥ 0
    if not isinstance(p.children, int) or p.children < 0:
        raise HTTPException(400, "Children must be 0 or a positive integer")

    # Height → positive number (allow float)
    try:
        if float(p.height) <= 0:
            raise HTTPException(400, "Height must be a positive number")
    except:
        raise HTTPException(400, "Height must be numeric")

    # Weight → positive number (allow float)
    try:
        if float(p.weight) <= 0:
            raise HTTPException(400, "Weight must be a positive number")
    except:
        raise HTTPException(400, "Weight must be numeric")

    # Contact → exactly 11 digits
    if not (isinstance(p.guardian_contact, str) and 
            p.guardian_contact.isdigit() and 
            len(p.guardian_contact) == 11):
        raise HTTPException(400, "Guardian contact must be exactly 11 digits")
