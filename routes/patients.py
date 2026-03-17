import random, string
from fastapi import APIRouter, HTTPException, Depends
from database import get_db, row_to_dict
from models import PatientCreate, PatientUpdate, CommentBody, BalanceBody

router = APIRouter()

def gen_id(prefix, table, col, db):
    cur = db.cursor()
    while True:
        nid = f"{prefix}-{random.randint(10000,99999)}"
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col}=:1", (nid,))
        if cur.fetchone()[0] == 0:
            cur.close()
            return nid

def gen_pw(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

# ── Get all patients for a caretaker ──────────────────────────────────────────
@router.get("/api/patients/{cid}")
def get_patients(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Patient_ID, Patient_Name, Guardian_Name, Guardian_Contact,
                          Guardian_Comment, Balance, Charges
                   FROM Patient WHERE C_ID=:1 ORDER BY Patient_Name""", (cid,))
    rows = cur.fetchall()
    keys = ["patient_id","patient_name","guardian_name","guardian_contact",
            "guardian_comment","balance","charges"]
    return [{keys[i]:r[i] for i in range(len(keys))} for r in rows]

# ── Get single patient ────────────────────────────────────────────────────────
@router.get("/api/patient/{pid}")
def get_patient(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM Patient WHERE Patient_ID=:1", (pid,))
    row = cur.fetchone()
    if not row: raise HTTPException(404, "Patient not found")
    return row_to_dict(cur, row)

# ── Create patient ────────────────────────────────────────────────────────────
@router.post("/api/patient")
def create_patient(p: PatientCreate, db=Depends(get_db)):
    cur = db.cursor()
    pid = gen_id("P","Patient","Patient_ID",db)
    pw  = gen_pw()
    cur.execute("""INSERT INTO Patient (Patient_ID,Patient_Name,Guardian_Password,
                   Patient_Gender,Age,Patient_Smoker,Patient_Children,Patient_Weight,
                   Patient_Height,Guardian_Name,Guardian_Contact,C_ID,Patient_Region)
                   VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13)""",
                (pid,p.name,pw,p.gender,p.age,p.smoker,p.children,
                 p.weight,p.height,p.guardian_name,p.guardian_contact,
                 p.caretaker_id,p.region))
    db.commit()
    return {"patient_id":pid,"guardian_password":pw}

# ── Update patient ────────────────────────────────────────────────────────────
@router.put("/api/patient/{pid}")
def update_patient(pid: str, p: PatientUpdate, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""UPDATE Patient SET Patient_Name=:1,Patient_Gender=:2,Age=:3,
                   Patient_Smoker=:4,Patient_Children=:5,Patient_Weight=:6,
                   Patient_Height=:7,Guardian_Name=:8,Guardian_Contact=:9,
                   Patient_Region=:10 WHERE Patient_ID=:11""",
                (p.name,p.gender,p.age,p.smoker,p.children,p.weight,p.height,
                 p.guardian_name,p.guardian_contact,p.region,pid))
    db.commit()
    return {"message":"Updated"}

# ── Delete patient ────────────────────────────────────────────────────────────
@router.delete("/api/patient/{pid}")
def delete_patient(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    # Delete child records first (foreign key order)
    cur.execute("DELETE FROM Notification WHERE Caretaker_ID=(SELECT C_ID FROM Patient WHERE Patient_ID=:1)", (pid,))
    cur.execute("DELETE FROM Task        WHERE P_ID=:1", (pid,))
    cur.execute("DELETE FROM Appointment WHERE P_ID=:1", (pid,))
    cur.execute("DELETE FROM Expenses    WHERE P_ID=:1", (pid,))
    cur.execute("DELETE FROM Patient     WHERE Patient_ID=:1", (pid,))
    db.commit()
    return {"message":"Patient deleted"}

# ── Update guardian comment ───────────────────────────────────────────────────
@router.put("/api/patient/{pid}/comment")
def update_comment(pid: str, b: CommentBody, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("UPDATE Patient SET Guardian_Comment=:1 WHERE Patient_ID=:2",
                (b.comment, pid))
    db.commit()
    return {"message":"Comment saved"}

# ── Add balance ───────────────────────────────────────────────────────────────
@router.put("/api/patient/{pid}/balance")
def add_balance(pid: str, b: BalanceBody, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("UPDATE Patient SET Balance=Balance+:1 WHERE Patient_ID=:2",
                (b.amount, pid))
    db.commit()
    cur.execute("SELECT Balance FROM Patient WHERE Patient_ID=:1", (pid,))
    row = cur.fetchone()
    return {"balance": float(row[0])}
