import random, secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from database import get_db, row_to_dict
from models import CaretakerCreate, CaretakerUpdate

router = APIRouter()


# -- ID + password generators --------------------------------------------------
def gen_id(db):
    cur = db.cursor()
    try:
        while True:
            cid = f"C-{secrets.randbelow(90000) + 10000}"
            cur.execute("SELECT COUNT(*) FROM Caretaker WHERE CaretakerID=:1", (cid,))
            if cur.fetchone()[0] == 0:
                return cid
    finally:
        cur.close()

def gen_pw(n=8):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))


# -- Signup (create caretaker) -------------------------------------------------
@router.post("/api/caretaker")
def create_caretaker(c: CaretakerCreate, db=Depends(get_db)):
    if c.contact and not c.contact.isdigit():
        raise HTTPException(status_code=400, detail="Contact number must contain only digits.")

    cur = db.cursor()
    try:
        cid = gen_id(db)
        pw  = gen_pw()

        cur.execute("""
            INSERT INTO Caretaker (CaretakerID, Caretaker_Name, Caretaker_Age,
                                   Caretaker_Password, Caretaker_Gender,
                                   Caretaker_Contact, Experience_Years, Qualification)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8)
        """, (cid, c.name, c.age, pw, c.gender,
              c.contact, c.experience_years, c.qualification))

        if c.skills:
            for skill in c.skills:
                cur.execute("""
                    INSERT INTO CaretakerSkill (CaretakerID, Skill)
                    VALUES (:1,:2)
                """, (cid, skill.strip()))

        db.commit()
        return {"caretaker_id": cid, "password": pw}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating caretaker: {str(e)}")
    finally:
        cur.close()


# -- Get caretaker profile -----------------------------------------------------
@router.get("/api/caretaker/{cid}")
def get_caretaker(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT * FROM Caretaker WHERE CaretakerID=:1", (cid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Caretaker not found")

        caretaker = row_to_dict(cur, row)

        cur.execute("SELECT Skill FROM CaretakerSkill WHERE CaretakerID=:1", (cid,))
        caretaker["skills"] = [r[0] for r in cur.fetchall()]

        return caretaker
    finally:
        cur.close()


# -- Update caretaker profile --------------------------------------------------
@router.put("/api/caretaker/{cid}")
def update_caretaker(cid: str, c: CaretakerUpdate, db=Depends(get_db)):
    if c.contact and not c.contact.isdigit():
        raise HTTPException(status_code=400, detail="Contact number must contain only digits.")

    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE Caretaker
            SET    Caretaker_Name=:1, Caretaker_Age=:2, Caretaker_Gender=:3,
                   Caretaker_Contact=:4, Experience_Years=:5, Qualification=:6
            WHERE  CaretakerID=:7
        """, (c.name, c.age, c.gender,
              c.contact, c.experience_years, c.qualification, cid))

        if c.skills is not None:
            cur.execute("DELETE FROM CaretakerSkill WHERE CaretakerID=:1", (cid,))
            for skill in c.skills:
                cur.execute("""
                    INSERT INTO CaretakerSkill (CaretakerID, Skill)
                    VALUES (:1,:2)
                """, (cid, skill.strip()))

        db.commit()
        return {"message": "Caretaker updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error updating caretaker: {str(e)}")
    finally:
        cur.close()


# -- Delete caretaker ----------------------------------------------------------
@router.delete("/api/caretaker/{cid}")
def delete_caretaker(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM CaretakerSkill  WHERE CaretakerID=:1", (cid,))
        cur.execute("DELETE FROM Notification    WHERE CaretakerID=:1", (cid,))
        cur.execute("DELETE FROM Task            WHERE CaretakerID=:1", (cid,))
        cur.execute("DELETE FROM Patient         WHERE CaretakerID=:1", (cid,))
        cur.execute("DELETE FROM Caretaker       WHERE CaretakerID=:1", (cid,))
        db.commit()
        return {"message": "Caretaker deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error deleting caretaker: {str(e)}")
    finally:
        cur.close()
