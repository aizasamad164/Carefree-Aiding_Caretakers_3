from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import PatientSymptomCreate, CustomSymptomCreate
from datetime import datetime

router = APIRouter()


# ── Get master list (for dropdown) — MUST be before /{pid} ───────────────────
@router.get("/api/symptoms/master")
def get_master_symptoms(db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT SymptomID, Name, Type, Description, Severity
            FROM   Symptom
            ORDER BY Type, Name
        """)
        keys = ["symptom_id", "name", "type", "description", "severity"]
        return [{keys[i]: r[i] for i in range(len(keys))} for r in cur.fetchall()]
    finally:
        cur.close()


# ── Get all symptoms for a patient (linked + custom) ─────────────────────────
@router.get("/api/symptoms/{pid}")
def get_symptoms(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        keys = ["symptom_id", "name", "type", "description",
                "severity", "recorded_date", "source"]

        def read_row(row):
            """Convert an Oracle row to a plain dict, reading any LOB values."""
            d = {}
            for i, val in enumerate(row):
                # Oracle LOB objects must be .read() before the cursor closes
                if hasattr(val, 'read'):
                    val = val.read()
                d[keys[i]] = val
            if isinstance(d.get("recorded_date"), datetime):
                d["recorded_date"] = d["recorded_date"].strftime("%Y-%m-%d %H:%M")
            return d

        # Predefined — joined from master via bridge table
        cur.execute("""
            SELECT sm.SymptomID, sm.Name, sm.Type, sm.Description,
                   sm.Severity, ps.Recorded_Date, 'predefined' AS source
            FROM   PatientSymptom ps
            JOIN   Symptom sm ON sm.SymptomID = ps.SymptomID
            WHERE  ps.PatientID = :1
            ORDER BY sm.Name
        """, (pid,))
        predefined = [read_row(r) for r in cur.fetchall()]

        # Custom — freeform per patient
        cur.execute("""
            SELECT CustomSymptomID, Name, Type, Description,
                   Severity, Recorded_Date, 'custom' AS source
            FROM   CustomSymptom
            WHERE  PatientID = :1
            ORDER BY Recorded_Date DESC
        """, (pid,))
        custom = [read_row(r) for r in cur.fetchall()]

        return {"predefined": predefined, "custom": custom}
    finally:
        cur.close()


# ── Link master symptom to patient ───────────────────────────────────────────
@router.post("/api/symptom/predefined")
def add_patient_symptom(s: PatientSymptomCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM Patient WHERE PatientID=:1", (s.patient_id,))
        if cur.fetchone()[0] == 0:
            raise HTTPException(404, "Patient not found")

        cur.execute("SELECT COUNT(*) FROM Symptom WHERE SymptomID=:1", (s.symptom_id,))
        if cur.fetchone()[0] == 0:
            raise HTTPException(404, "Symptom not found in master list")

        cur.execute("""
            INSERT INTO PatientSymptom (PatientID, SymptomID, Recorded_Date)
            VALUES (:1, :2, CURRENT_TIMESTAMP)
        """, (s.patient_id, s.symptom_id))

        db.commit()
        return {"message": "Symptom linked to patient"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()


# ── Add custom symptom ────────────────────────────────────────────────────────
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


# ── Unlink predefined symptom from patient ────────────────────────────────────
@router.delete("/api/symptom/predefined/{pid}/{sid}")
def remove_patient_symptom(pid: str, sid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            DELETE FROM PatientSymptom
            WHERE PatientID=:1 AND SymptomID=:2
        """, (pid, sid))
        if cur.rowcount == 0:
            raise HTTPException(404, "Symptom link not found")
        db.commit()
        return {"message": "Symptom unlinked"}
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