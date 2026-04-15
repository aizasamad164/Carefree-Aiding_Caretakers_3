import random
import string
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import CaretakerCreate, CaretakerUpdate

router = APIRouter()

# ── Create tables if not exist ────────────────────────────────────────────────
def create_caretaker_tables(db):
    cur = db.cursor()

    # Caretaker table
    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Caretaker (
                    CaretakerID         VARCHAR2(20)    PRIMARY KEY,
                    Caretaker_Name      VARCHAR2(100)   NOT NULL,
                    Caretaker_Age       NUMBER(3),
                    Caretaker_Password  VARCHAR2(50)    NOT NULL,
                    Caretaker_Gender    VARCHAR2(10),
                    Caretaker_Contact   VARCHAR2(20),
                    Experience_Years    NUMBER(2),
                    Qualification       VARCHAR2(100)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    # CaretakerSkill table (1NF — one skill per row)
    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE CaretakerSkill (
                    CaretakerID     VARCHAR2(20)    REFERENCES Caretaker(CaretakerID),
                    Skill           VARCHAR2(100)   NOT NULL,
                    CONSTRAINT pk_caretaker_skill PRIMARY KEY (CaretakerID, Skill)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    db.commit()
    cur.close()


# ── ID + password generators ──────────────────────────────────────────────────
def gen_id(db):
    cur = db.cursor()
    while True:
        cid = f"C-{random.randint(10000,99999)}"
        cur.execute("SELECT COUNT(*) FROM Caretaker WHERE CaretakerID=:1", (cid,))
        if cur.fetchone()[0] == 0:
            cur.close()
            return cid

def gen_pw(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


# ── Signup (create caretaker) ─────────────────────────────────────────────────
@router.post("/api/caretaker")
def create_caretaker(c: CaretakerCreate, db=Depends(get_db)):
    cur = db.cursor()
    cid = gen_id(db)
    pw  = gen_pw()

    cur.execute("""
        INSERT INTO Caretaker (CaretakerID, Caretaker_Name, Caretaker_Age,
                               Caretaker_Password, Caretaker_Gender,
                               Caretaker_Contact, Experience_Years, Qualification)
        VALUES (:1,:2,:3,:4,:5,:6,:7,:8)
    """, (cid, c.name, c.age, pw, c.gender,
          c.contact, c.experience_years, c.qualification))

    # Insert skills — one row per skill (1NF)
    if c.skills:
        for skill in c.skills:
            cur.execute("""
                INSERT INTO CaretakerSkill (CaretakerID, Skill)
                VALUES (:1,:2)
            """, (cid, skill.strip()))

    db.commit()
    return {"caretaker_id": cid, "password": pw}


# ── Get caretaker profile ─────────────────────────────────────────────────────
@router.get("/api/caretaker/{cid}")
def get_caretaker(cid: str, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT * FROM Caretaker WHERE CaretakerID=:1", (cid,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Caretaker not found")

    from database import row_to_dict
    caretaker = row_to_dict(cur, row)

    # Fetch skills as a list
    cur.execute("SELECT Skill FROM CaretakerSkill WHERE CaretakerID=:1", (cid,))
    caretaker["skills"] = [r[0] for r in cur.fetchall()]

    return caretaker


# ── Update caretaker profile ──────────────────────────────────────────────────
@router.put("/api/caretaker/{cid}")
def update_caretaker(cid: str, c: CaretakerUpdate, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("""
        UPDATE Caretaker
        SET    Caretaker_Name=:1, Caretaker_Age=:2, Caretaker_Gender=:3,
               Caretaker_Contact=:4, Experience_Years=:5, Qualification=:6
        WHERE  CaretakerID=:7
    """, (c.name, c.age, c.gender,
          c.contact, c.experience_years, c.qualification, cid))

    # Replace skills — delete old, insert new (composite PK ensures no dupes)
    if c.skills is not None:
        cur.execute("DELETE FROM CaretakerSkill WHERE CaretakerID=:1", (cid,))
        for skill in c.skills:
            cur.execute("""
                INSERT INTO CaretakerSkill (CaretakerID, Skill)
                VALUES (:1,:2)
            """, (cid, skill.strip()))

    db.commit()
    return {"message": "Caretaker updated"}


# ── Delete caretaker ──────────────────────────────────────────────────────────
@router.delete("/api/caretaker/{cid}")
def delete_caretaker(cid: str, db=Depends(get_db)):
    cur = db.cursor()

    # Delete in FK-safe order
    cur.execute("DELETE FROM CaretakerSkill  WHERE CaretakerID=:1", (cid,))
    cur.execute("DELETE FROM Notification    WHERE CaretakerID=:1", (cid,))
    cur.execute("DELETE FROM Task            WHERE CaretakerID=:1", (cid,))
    cur.execute("DELETE FROM Patient         WHERE CaretakerID=:1", (cid,))
    cur.execute("DELETE FROM Caretaker       WHERE CaretakerID=:1", (cid,))

    db.commit()
    return {"message": "Caretaker deleted"}
