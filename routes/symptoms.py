from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import SymptomCreate, CustomSymptomCreate
from datetime import datetime

router = APIRouter()


# ── Get master symptom list (for dropdown) ────────────────────────────────────
# MUST be before /api/symptoms/{pid} to avoid route clash
@router.get("/api/symptoms/master")
def get_master_symptoms(db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT SymptomID, Name, Type, Description, Severity
            FROM   SymptomMaster
            ORDER BY Type, Name
        """)
        keys = ["symptom_id", "name", "type", "description", "severity"]
        return [{keys[i]: r[i] for i in range(len(keys))} for r in cur.fetchall()]
    finally:
        cur.close()


# ── Get all symptoms for a patient (predefined + custom) ──────────────────────
@router.get("/api/symptoms/{pid}")
def get_symptoms(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        keys = ["symptom_id", "name", "type", "description",
                "severity", "recorded_date", "source"]

        # Predefined
        cur.execute("""
            SELECT SymptomID, Name, Type, Description, Severity,
                   NULL AS Recorded_Date, 'predefined' AS source
            FROM   Symptom
            WHERE  PatientID = :1
            ORDER BY Name
        """, (pid,))
        predefined = []
        for r in cur.fetchall():
            d = {}
            for i, val in enumerate(r):
                if hasattr(val, 'read'):
                    val = val.read()
                d[keys[i]] = val
            predefined.append(d)

        # Custom
        cur.execute("""
            SELECT CustomSymptomID, Name, Type, Description, Severity,
                   Recorded_Date, 'custom' AS source
            FROM   CustomSymptom
            WHERE  PatientID = :1
            ORDER BY Recorded_Date DESC
        """, (pid,))
        custom = []
        for r in cur.fetchall():
            d = {}
            for i, val in enumerate(r):
                if hasattr(val, 'read'):
                    val = val.read()
                d[keys[i]] = val
            if isinstance(d.get("recorded_date"), datetime):
                d["recorded_date"] = d["recorded_date"].strftime("%Y-%m-%d %H:%M")
            custom.append(d)

        return {"predefined": predefined, "custom": custom}
    finally:
        cur.close()


# ── Add predefined symptom to patient (picked from master) ────────────────────
@router.post("/api/symptom/predefined")
def add_predefined_symptom(s: SymptomCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM Patient WHERE PatientID=:1", (s.patient_id,))
        if cur.fetchone()[0] == 0:
            raise HTTPException(404, "Patient not found")

        # Check not already linked
        cur.execute("SELECT COUNT(*) FROM Symptom WHERE SymptomID=:1 AND PatientID=:2",
                    (s.symptom_id, s.patient_id))
        if cur.fetchone()[0] > 0:
            raise HTTPException(400, "Symptom already added for this patient")

        cur.execute("""
            INSERT INTO Symptom (SymptomID, Name, Type, Description, Severity, PatientID)
            VALUES (:1,:2,:3,:4,:5,:6)
        """, (s.symptom_id, s.name, s.type, s.description, s.severity, s.patient_id))

        db.commit()
        return {"message": "Symptom added"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()


# ── Add custom freeform symptom ───────────────────────────────────────────────
@router.post("/api/symptom/custom")
def add_custom_symptom(s: CustomSymptomCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM Patient WHERE PatientID=:1", (s.patient_id,))
        if cur.fetchone()[0] == 0:
            raise HTTPException(404, "Patient not found")

        cur.execute("""
            INSERT INTO CustomSymptom (Name, Type, Description,
                                       Severity, Recorded_Date, PatientID)
            VALUES (:1,:2,:3,:4, CURRENT_TIMESTAMP,:5)
        """, (s.name, s.type, s.description, s.severity, s.patient_id))

        db.commit()
        return {"message": "Custom symptom added"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()


# ── Delete predefined symptom from patient ────────────────────────────────────
@router.delete("/api/symptom/predefined/{sid}")
def delete_predefined_symptom(sid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM Symptom WHERE SymptomID=:1", (sid,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Symptom not found")
        db.commit()
        return {"message": "Symptom removed"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()


# ── Delete custom symptom ─────────────────────────────────────────────────────
@router.delete("/api/symptom/custom/{cid}")
def delete_custom_symptom(cid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM CustomSymptom WHERE CustomSymptomID=:1", (cid,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Custom symptom not found")
        db.commit()
        return {"message": "Custom symptom deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()