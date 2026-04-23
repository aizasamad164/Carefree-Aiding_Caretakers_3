import oracledb
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import VitalsCreate, VitalsUpdate
from datetime import datetime

router = APIRouter()


# ── Get all vitals for a patient ──────────────────────────────────────────────
@router.get("/api/vitals/{pid}")
def get_vitals(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT v.VitalsID, v.Recorded_Time, v.VitalsCategory,
                   c.Pulse_Rate, c.Blood_Pressure,
                   r.Respiratory_Rate, r.Oxygen_Sat,
                   o.Blood_Glucose
            FROM   Vitals v
            LEFT JOIN CardiacVitals     c ON c.VitalsID = v.VitalsID
            LEFT JOIN RespiratoryVitals r ON r.VitalsID = v.VitalsID
            LEFT JOIN OtherVitals       o ON o.VitalsID = v.VitalsID
            WHERE  v.PatientID = :1
            ORDER BY v.Recorded_Time DESC
        """, (pid,))
        keys = ["vitals_id", "recorded_time", "vitals_category",
                "pulse_rate", "blood_pressure",
                "respiratory_rate", "oxygen_sat",
                "blood_glucose"]
        result = []
        for row in cur.fetchall():
            d = {keys[i]: row[i] for i in range(len(keys))}
            if isinstance(d["recorded_time"], datetime):
                d["recorded_time"] = d["recorded_time"].strftime("%Y-%m-%d %H:%M")
            result.append(d)
        return result
    finally:
        cur.close()


# ── Create vitals ─────────────────────────────────────────────────────────────
@router.post("/api/vitals")
def create_vitals(v: VitalsCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        # Accept category from either field name the frontend may send
        category = v.vitals_category or v.category or "General"

        vid_var = cur.var(oracledb.DB_TYPE_NUMBER)
        cur.execute("""
            INSERT INTO Vitals (Recorded_Time, VitalsCategory, PatientID)
            VALUES (CURRENT_TIMESTAMP, :1, :2)
            RETURNING VitalsID INTO :3
        """, (category, v.patient_id, vid_var))

        raw = vid_var.getvalue()
        vid = int(raw[0] if isinstance(raw, list) else raw)

        # Only insert cardiac row if at least one cardiac value is present —
        # inserting an all-NULL row creates an orphan that breaks the JOIN on read.
        if v.pulse_rate is not None or v.blood_pressure is not None:
            cur.execute("""
                INSERT INTO CardiacVitals (VitalsID, Pulse_Rate, Blood_Pressure)
                VALUES (:1, :2, :3)
            """, (vid, v.pulse_rate, v.blood_pressure))

        # Only insert respiratory row if at least one respiratory value is present
        if v.respiratory_rate is not None or v.oxygen_sat is not None:
            cur.execute("""
                INSERT INTO RespiratoryVitals (VitalsID, Respiratory_Rate, Oxygen_Sat)
                VALUES (:1, :2, :3)
            """, (vid, v.respiratory_rate, v.oxygen_sat))

        # Only insert other row if blood glucose is present
        if v.blood_glucose is not None:
            cur.execute("""
                INSERT INTO OtherVitals (VitalsID, Blood_Glucose)
                VALUES (:1, :2)
            """, (vid, v.blood_glucose))

        db.commit()
        return {"message": "Vitals recorded", "vitals_id": vid}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()


# ── Update vitals ─────────────────────────────────────────────────────────────
@router.put("/api/vitals/{vid}")
def update_vitals(vid: int, v: VitalsUpdate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM Vitals WHERE VitalsID=:1", (vid,))
        if cur.fetchone()[0] == 0:
            raise HTTPException(404, "Vitals record not found")

        cur.execute("""
            UPDATE CardiacVitals
            SET Pulse_Rate=:1, Blood_Pressure=:2
            WHERE VitalsID=:3
        """, (v.pulse_rate, v.blood_pressure, vid))

        cur.execute("""
            UPDATE RespiratoryVitals
            SET Respiratory_Rate=:1, Oxygen_Sat=:2
            WHERE VitalsID=:3
        """, (v.respiratory_rate, v.oxygen_sat, vid))

        cur.execute("""
            UPDATE OtherVitals
            SET Blood_Glucose=:1
            WHERE VitalsID=:2
        """, (v.blood_glucose, vid))

        db.commit()
        return {"message": "Vitals updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()


# ── Delete vitals ─────────────────────────────────────────────────────────────
@router.delete("/api/vitals/{vid}")
def delete_vitals(vid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM OtherVitals       WHERE VitalsID=:1", (vid,))
        cur.execute("DELETE FROM RespiratoryVitals WHERE VitalsID=:1", (vid,))
        cur.execute("DELETE FROM CardiacVitals      WHERE VitalsID=:1", (vid,))
        cur.execute("DELETE FROM Vitals             WHERE VitalsID=:1", (vid,))
        db.commit()
        return {"message": "Vitals deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cur.close()