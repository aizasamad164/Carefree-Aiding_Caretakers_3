from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import VitalsCreate, VitalsUpdate
from datetime import datetime

router = APIRouter()


@router.get("/api/vitals/{pid}")
def get_vitals(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT VitalsID, Recorded_Time, Pulse_Rate, BP_Systolic, BP_Diastolic,
                   Respiratory_Rate, Oxygen_Saturation, GFR, Serum_Creatinine,
                   Temperature, Blood_Sugar, Metabolic, PatientID
            FROM   Vitals
            WHERE  PatientID = :1
            ORDER BY Recorded_Time DESC
        """, (pid,))
        keys = ["vitals_id", "recorded_time", "pulse_rate", "bp_systolic", "bp_diastolic",
                "respiratory_rate", "oxygen_saturation", "gfr", "serum_creatinine",
                "temperature", "blood_sugar", "metabolic", "patient_id"]
        result = []
        for r in cur.fetchall():
            d = {keys[i]: r[i] for i in range(len(keys))}
            if isinstance(d["recorded_time"], datetime):
                d["recorded_time"] = d["recorded_time"].strftime("%Y-%m-%d %H:%M")
            result.append(d)
        return result
    finally:
        cur.close()


@router.post("/api/vitals")
def create_vitals(v: VitalsCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        vid_var = cur.var(__import__('cx_Oracle').NUMBER)
        cur.execute("""
            INSERT INTO Vitals (Recorded_Time, Pulse_Rate, BP_Systolic, BP_Diastolic,
                                Respiratory_Rate, Oxygen_Saturation, GFR, Serum_Creatinine,
                                Temperature, Blood_Sugar, Metabolic, PatientID)
            VALUES (CURRENT_TIMESTAMP, :1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11)
            RETURNING VitalsID INTO :12
        """, (v.pulse_rate, v.bp_systolic, v.bp_diastolic,
              v.respiratory_rate, v.oxygen_saturation,
              v.gfr, v.serum_creatinine, v.temperature,
              v.blood_sugar, v.metabolic, v.patient_id, vid_var))
        raw = vid_var.getvalue()
        vid = int(raw[0] if isinstance(raw, list) else raw)
        db.commit()
        return {"message": "Vitals recorded", "vitals_id": vid}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()


@router.put("/api/vitals/{vid}")
def update_vitals(vid: int, v: VitalsUpdate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM Vitals WHERE VitalsID=:1", (vid,))
        if cur.fetchone()[0] == 0:
            raise HTTPException(404, "Vitals record not found")
        cur.execute("""
            UPDATE Vitals
            SET    Pulse_Rate=:1, BP_Systolic=:2, BP_Diastolic=:3,
                   Respiratory_Rate=:4, Oxygen_Saturation=:5,
                   GFR=:6, Serum_Creatinine=:7, Temperature=:8,
                   Blood_Sugar=:9, Metabolic=:10
            WHERE  VitalsID=:11
        """, (v.pulse_rate, v.bp_systolic, v.bp_diastolic,
              v.respiratory_rate, v.oxygen_saturation,
              v.gfr, v.serum_creatinine, v.temperature,
              v.blood_sugar, v.metabolic, vid))
        db.commit()
        return {"message": "Vitals updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()


@router.delete("/api/vitals/{vid}")
def delete_vitals(vid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM Vitals WHERE VitalsID=:1", (vid,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Vitals record not found")
        db.commit()
        return {"message": "Vitals deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()