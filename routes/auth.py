import random, string
from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from models import LoginReq, SignupReq

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

# ── Login ──────────────────────────────────────────────────────────────────────
@router.post("/api/login")
def login(r: LoginReq, db=Depends(get_db)):
    cur = db.cursor()
    if r.role == "caretaker":
        cur.execute("""SELECT Caretaker_ID, Caretaker_Name FROM Caretaker
                       WHERE Caretaker_Name=:1 AND Caretaker_Password=:2""",
                    (r.username, r.password))
        row = cur.fetchone()
        if not row: raise HTTPException(401, "Invalid credentials")
        return {"role":"caretaker","id":row[0],"name":row[1]}

    elif r.role == "guardian":
        cur.execute("""SELECT Patient_ID, Guardian_Name FROM Patient
                       WHERE Guardian_Name=:1 AND Guardian_Password=:2""",
                    (r.username, r.password))
        row = cur.fetchone()
        if not row: raise HTTPException(401, "Invalid credentials")
        return {"role":"guardian","patient_id":row[0],"name":row[1]}

    raise HTTPException(400, "Invalid role")

# ── Signup ─────────────────────────────────────────────────────────────────────
@router.post("/api/signup")
def signup(r: SignupReq, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM Caretaker WHERE Caretaker_Name=:1", (r.name,))
    if cur.fetchone()[0]:
        raise HTTPException(400, "Username already taken")
    cid = gen_id("C","Caretaker","Caretaker_ID",db)
    pw  = gen_pw()
    cur.execute("INSERT INTO Caretaker VALUES (:1,:2,:3,:4,:5,:6,:7)",
                (cid,r.name,r.age,pw,r.gender,r.contact,r.skills))
    db.commit()
    return {"caretaker_id":cid,"password":pw,"message":"Account created"}
