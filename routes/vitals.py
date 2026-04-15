from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import VitalsCreate, VitalsUpdate

router = APIRouter()

# ── Create tables if not exist ────────────────────────────────────────────────
def create_vitals_tables(db):
    cur = db.cursor()

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Vitals (
                    VitalsID        NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    Recorded_Time   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
                    PatientID       VARCHAR2(20)    REFERENCES Patient(PatientID)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Cardiac (
                    VitalsID        NUMBER          PRIMARY KEY
                                    REFERENCES Vitals(VitalsID),
                    Pulse_Rate      NUMBER(5,2),
                    BP_Systolic     NUMBER(5,2),
                    BP_Diastolic    NUMBER(5,2)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Respiratory (
                    VitalsID                NUMBER      PRIMARY KEY
                                            REFERENCES Vitals(VitalsID),
                    Respiratory_Rate        NUMBER(5,2),
                    Oxygen_Saturation       NUMBER(5,2)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE OtherVitals (
                    VitalsID            NUMBER          PRIMARY KEY
                                        REFERENCES Vitals(VitalsID),
                    GFR                 NUMBER(6,2),
                    Serum_Creatinine    NUMBER(5,2),
                    Temperature         NUMBER(5,2),
                    Blood_Sugar         NUMBER(6,2),
                    Metabolic           NUMBER(6,2)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    db.commit()
    cur.close()


# ── Get all vitals for a patient (list view) ──────────────────────────────────
@router.get("/api/vitals/{pid}")
def get_vitals(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT VitalsID, Recorded_Time, PatientID
        FROM   Vitals
        WHERE  PatientID = :1
        ORDER BY Recorded_Time DESC
    """, (pid,))
    rows = cur.fetchall()
    keys = ["vitals_id", "recorded_time", "patient_id"]
    return [{keys[i]: r[i] for i in range(len(keys))} for r in rows]


# ── Get single vitals record with all subtype details ─────────────────────────
@router.get("/api/vitals/detail/{vid}")
def get_vitals_detail(vid: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT v.VitalsID, v.Recorded_Time, v.PatientID,
               c.Pulse_Rate, c.BP_Systolic, c.BP_Diastolic,
               r.Respiratory_Rate, r.Oxygen_Saturation,
               o.GFR, o.Serum_Creatinine, o.Temperature,
               o.Blood_Sugar, o.Metabolic
        FROM   Vitals v
        JOIN   Cardiac      c ON c.VitalsID = v.VitalsID
        JOIN   Respiratory  r ON r.VitalsID = v.VitalsID
        JOIN   OtherVitals  o ON o.VitalsID = v.VitalsID
        WHERE  v.VitalsID = :1
    """, (vid,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Vitals record not found")
    keys = ["vitals_id", "recorded_time", "patient_id",
            "pulse_rate", "bp_systolic", "bp_diastolic",
            "respiratory_rate", "oxygen_saturation",
            "gfr", "serum_creatinine", "temperature",
            "blood_sugar", "metabolic"]
    return {keys[i]: row[i] for i in range(len(keys))}


# ── Insert vitals ─────────────────────────────────────────────────────────────
@router.post("/api/vitals")
def create_vitals(v: VitalsCreate, db=Depends(get_db)):
    cur = db.cursor()

    vid_var = cur.var(__import__('cx_Oracle').NUMBER)
    cur.execute("""
        INSERT INTO Vitals (Recorded_Time, PatientID)
        VALUES (CURRENT_TIMESTAMP, :1)
        RETURNING VitalsID INTO :2
    """, (v.patient_id, vid_var))
    vid = int(vid_var.getvalue())

    cur.execute("""
        INSERT INTO Cardiac (VitalsID, Pulse_Rate, BP_Systolic, BP_Diastolic)
        VALUES (:1,:2,:3,:4)
    """, (vid, v.pulse_rate, v.bp_systolic, v.bp_diastolic))

    cur.execute("""
        INSERT INTO Respiratory (VitalsID, Respiratory_Rate, Oxygen_Saturation)
        VALUES (:1,:2,:3)
    """, (vid, v.respiratory_rate, v.oxygen_saturation))

    cur.execute("""
        INSERT INTO OtherVitals (VitalsID, GFR, Serum_Creatinine,
                                 Temperature, Blood_Sugar, Metabolic)
        VALUES (:1,:2,:3,:4,:5,:6)
    """, (vid, v.gfr, v.serum_creatinine,
          v.temperature, v.blood_sugar, v.metabolic))

    db.commit()
    return {"message": "Vitals recorded", "vitals_id": vid}


# ── Update vitals ─────────────────────────────────────────────────────────────
@router.put("/api/vitals/{vid}")
def update_vitals(vid: int, v: VitalsUpdate, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM Vitals WHERE VitalsID=:1", (vid,))
    if cur.fetchone()[0] == 0:
        raise HTTPException(404, "Vitals record not found")

    cur.execute("""
        UPDATE Cardiac
        SET    Pulse_Rate=:1, BP_Systolic=:2, BP_Diastolic=:3
        WHERE  VitalsID=:4
    """, (v.pulse_rate, v.bp_systolic, v.bp_diastolic, vid))

    cur.execute("""
        UPDATE Respiratory
        SET    Respiratory_Rate=:1, Oxygen_Saturation=:2
        WHERE  VitalsID=:3
    """, (v.respiratory_rate, v.oxygen_saturation, vid))

    cur.execute("""
        UPDATE OtherVitals
        SET    GFR=:1, Serum_Creatinine=:2, Temperature=:3,
               Blood_Sugar=:4, Metabolic=:5
        WHERE  VitalsID=:6
    """, (v.gfr, v.serum_creatinine, v.temperature,
          v.blood_sugar, v.metabolic, vid))

    db.commit()
    return {"message": "Vitals updated"}


# ── Delete vitals ─────────────────────────────────────────────────────────────
@router.delete("/api/vitals/{vid}")
def delete_vitals(vid: int, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM Vitals WHERE VitalsID=:1", (vid,))
    if cur.fetchone()[0] == 0:
        raise HTTPException(404, "Vitals record not found")

    # Delete subtypes first, then supertype
    cur.execute("DELETE FROM OtherVitals  WHERE VitalsID=:1", (vid,))
    cur.execute("DELETE FROM Respiratory  WHERE VitalsID=:1", (vid,))
    cur.execute("DELETE FROM Cardiac      WHERE VitalsID=:1", (vid,))
    cur.execute("DELETE FROM Vitals       WHERE VitalsID=:1", (vid,))

    db.commit()
    return {"message": "Vitals deleted"}
