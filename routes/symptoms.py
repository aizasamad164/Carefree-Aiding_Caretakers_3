from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import PatientSymptomCreate, CustomSymptomCreate
from datetime import datetime

router = APIRouter()

# ── Create tables if not exist ────────────────────────────────────────────────
def create_symptom_tables(db):
    cur = db.cursor()

    # Symptom master table
    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Symptom (
                    SymptomID       VARCHAR2(20)    PRIMARY KEY,
                    Name            VARCHAR2(100)   NOT NULL,
                    Type            VARCHAR2(50),
                    Description     VARCHAR2(500),
                    Severity        VARCHAR2(20)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    # Bridge table — predefined symptoms linked to patients
    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE PatientSymptom (
                    PatientID       VARCHAR2(20)    REFERENCES Patient(PatientID),
                    SymptomID       VARCHAR2(20)    REFERENCES Symptom(SymptomID),
                    Recorded_Date   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT pk_patient_symptom PRIMARY KEY (PatientID, SymptomID)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    # Freeform custom symptoms per patient
    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE PatientCustomSymptom (
                    CustomSymptomID NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    Name            VARCHAR2(100)   NOT NULL,
                    Type            VARCHAR2(50),
                    Description     VARCHAR2(500),
                    Severity        VARCHAR2(20),
                    Recorded_Date   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
                    PatientID       VARCHAR2(20)    REFERENCES Patient(PatientID)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    db.commit()
    cur.close()


# ── Get all symptoms for a patient (predefined + custom) ──────────────────────
@router.get("/api/symptoms/{pid}")
def get_symptoms(pid: str, db=Depends(get_db)):
    cur = db.cursor()

    # Predefined symptoms via bridge
    cur.execute("""
        SELECT s.SymptomID, s.Name, s.Type, s.Description,
               s.Severity, ps.Recorded_Date, 'predefined' AS source
        FROM   PatientSymptom ps
        JOIN   Symptom s ON s.SymptomID = ps.SymptomID
        WHERE  ps.PatientID = :1
        ORDER BY ps.Recorded_Date DESC
    """, (pid,))
    predefined_keys = ["symptom_id", "name", "type", "description",
                       "severity", "recorded_date", "source"]
    predefined = [{predefined_keys[i]: r[i] for i in range(len(predefined_keys))}
                  for r in cur.fetchall()]

    # Custom freeform symptoms
    cur.execute("""
        SELECT CustomSymptomID, Name, Type, Description,
               Severity, Recorded_Date, 'custom' AS source
        FROM   PatientCustomSymptom
        WHERE  PatientID = :1
        ORDER BY Recorded_Date DESC
    """, (pid,))
    custom_keys = ["symptom_id", "name", "type", "description",
                   "severity", "recorded_date", "source"]
    custom = [{custom_keys[i]: r[i] for i in range(len(custom_keys))}
              for r in cur.fetchall()]

    return {"predefined": predefined, "custom": custom}


# ── Get all master symptoms (for frontend dropdown) ───────────────────────────
@router.get("/api/symptoms/master")
def get_master_symptoms(db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT SymptomID, Name, Type, Description, Severity
        FROM   Symptom
        ORDER BY Type, Name
    """)
    keys = ["symptom_id", "name", "type", "description", "severity"]
    return [{keys[i]: r[i] for i in range(len(keys))} for r in cur.fetchall()]


# ── Link predefined symptom to patient ───────────────────────────────────────
@router.post("/api/symptom/predefined")
def add_patient_symptom(s: PatientSymptomCreate, db=Depends(get_db)):
    cur = db.cursor()

    # Verify patient exists
    cur.execute("SELECT COUNT(*) FROM Patient WHERE PatientID=:1", (s.patient_id,))
    if cur.fetchone()[0] == 0:
        raise HTTPException(404, "Patient not found")

    # Verify symptom exists
    cur.execute("SELECT COUNT(*) FROM Symptom WHERE SymptomID=:1", (s.symptom_id,))
    if cur.fetchone()[0] == 0:
        raise HTTPException(404, "Symptom not found")

    # Composite PK will reject duplicates automatically
    try:
        cur.execute("""
            INSERT INTO PatientSymptom (PatientID, SymptomID, Recorded_Date)
            VALUES (:1,:2, CURRENT_TIMESTAMP)
        """, (s.patient_id, s.symptom_id))
        db.commit()
    except Exception:
        raise HTTPException(400, "Symptom already linked to this patient")

    return {"message": "Symptom linked to patient"}


# ── Add custom freeform symptom ───────────────────────────────────────────────
@router.post("/api/symptom/custom")
def add_custom_symptom(s: CustomSymptomCreate, db=Depends(get_db)):
    cur = db.cursor()

    # Verify patient exists
    cur.execute("SELECT COUNT(*) FROM Patient WHERE PatientID=:1", (s.patient_id,))
    if cur.fetchone()[0] == 0:
        raise HTTPException(404, "Patient not found")

    cur.execute("""
        INSERT INTO PatientCustomSymptom (Name, Type, Description,
                                          Severity, Recorded_Date, PatientID)
        VALUES (:1,:2,:3,:4, CURRENT_TIMESTAMP,:5)
    """, (s.name, s.type, s.description, s.severity, s.patient_id))

    db.commit()
    return {"message": "Custom symptom added"}


# ── Unlink predefined symptom from patient ────────────────────────────────────
@router.delete("/api/symptom/predefined/{pid}/{sid}")
def remove_patient_symptom(pid: str, sid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        DELETE FROM PatientSymptom
        WHERE PatientID=:1 AND SymptomID=:2
    """, (pid, sid))
    if cur.rowcount == 0:
        raise HTTPException(404, "Symptom link not found")
    db.commit()
    return {"message": "Symptom unlinked from patient"}


# ── Delete custom symptom ─────────────────────────────────────────────────────
@router.delete("/api/symptom/custom/{cid}")
def delete_custom_symptom(cid: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM PatientCustomSymptom WHERE CustomSymptomID=:1", (cid,))
    if cur.rowcount == 0:
        raise HTTPException(404, "Custom symptom not found")
    db.commit()
    return {"message": "Custom symptom deleted"}