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

# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/api/login")
def login(r: LoginReq, db=Depends(get_db)):
    cur = db.cursor()

    if r.role == "caretaker":
        cur.execute("""
            SELECT CaretakerID, Caretaker_Name
            FROM   Caretaker
            WHERE  Caretaker_Name=:1 AND Caretaker_Password=:2
        """, (r.username, r.password))
        row = cur.fetchone()
        if not row:
            raise HTTPException(401, "Invalid credentials")
        return {"role": "caretaker", "id": row[0], "name": row[1]}

    elif r.role == "guardian":
        # Guardian_Name and Guardian_Password now live on Guardian table
        cur.execute("""
            SELECT g.PatientID, g.Guardian_Name
            FROM   Guardian g
            WHERE  g.Guardian_Name=:1 AND g.Guardian_Password=:2
        """, (r.username, r.password))
        row = cur.fetchone()
        if not row:
            raise HTTPException(401, "Invalid credentials")
        return {"role": "guardian", "patient_id": row[0], "name": row[1]}

    raise HTTPException(400, "Invalid role")

# ── Signup ────────────────────────────────────────────────────────────────────
@router.post("/api/signup")
def signup(r: SignupReq, db=Depends(get_db)):
    cur = db.cursor()

    # Check username uniqueness
    cur.execute("SELECT COUNT(*) FROM Caretaker WHERE Caretaker_Name=:1", (r.name,))
    if cur.fetchone()[0]:
        raise HTTPException(400, "Username already taken")

    cid = gen_id("C", "Caretaker", "CaretakerID", db)
    pw  = gen_pw()

    # Insert caretaker core info
    cur.execute("""
        INSERT INTO Caretaker (CaretakerID, Caretaker_Name, Caretaker_Age,
                               Caretaker_Password, Caretaker_Gender,
                               Caretaker_Contact, Experience_Years, Qualification)
        VALUES (:1,:2,:3,:4,:5,:6,:7,:8)
    """, (cid, r.name, r.age, pw, r.gender,
          r.contact, r.experience_years, r.qualification))

    # Insert skills — one row per skill (1NF)
    if r.skills:
        for skill in r.skills:
            cur.execute("""
                INSERT INTO CaretakerSkill (CaretakerID, Skill)
                VALUES (:1,:2)
            """, (cid, skill.strip()))

    db.commit()
    return {"caretaker_id": cid, "password": pw, "message": "Account created"}