from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from database import get_db
from models import StressReq, CostReq
from ml_models import stress_model, cost_model
import numpy as np
import pandas as pd

router = APIRouter()

# ── Stress Prediction ─────────────────────────────────────────────────────────
@router.post("/api/predict/stress")
def predict_stress(d: StressReq):
    if not stress_model:
        raise HTTPException(503, "Stress model unavailable — check CSV file")

    validate_positive_numeric(d.age, "Age")
    validate_positive_numeric(d.sleep_duration, "Sleep duration")
    validate_positive_numeric(d.quality_of_sleep, "Quality of sleep")
    validate_positive_numeric(d.physical_activity, "Physical activity")
    validate_positive_numeric(d.heart_rate, "Heart rate")
    validate_positive_numeric(d.daily_steps, "Daily steps")
    validate_positive_numeric(d.systolic, "Systolic BP")
    validate_positive_numeric(d.diastolic, "Diastolic BP")

    bmi = {"Obese":0,"Normal":1,"Overweight":2}.get(d.bmi_category, 1)
    inp = np.array([[
        d.age,
        d.sleep_duration * d.quality_of_sleep,
        bmi,
        d.physical_activity,
        d.heart_rate,
        d.daily_steps,
        d.systolic,
        d.diastolic
    ]])
    return {"stress_level": str(stress_model.predict(inp)[0])}

# ── Cost Prediction ───────────────────────────────────────────────────────────
@router.post("/api/predict/cost")
def predict_cost(d: CostReq, patient_id: Optional[str]=None, db=Depends(get_db)):
    if not cost_model:
        raise HTTPException(503, "Cost model unavailable — check CSV file")

    validate_positive_numeric(d.age, "Age")
    validate_positive_numeric(d.bmi, "BMI")
    validate_positive_numeric(d.children, "Children")

    df = pd.DataFrame([{
        "age":      d.age,
        "sex":      d.sex.lower(),
        "bmi":      d.bmi,
        "children": d.children,
        "smoker":   d.smoker.lower(),
        "region":   d.region.lower()
    }])
    pred = float(cost_model.predict(df)[0])

    # Optionally save to patient record
    if patient_id:
        cur = db.cursor()
        cur.execute("UPDATE Patient SET Charges=:1 WHERE PatientID=:2",
                    (pred, patient_id))
        db.commit()

    return {"predicted_cost": round(pred, 2)}


def validate_positive_numeric(value, field_name):
    try:
        val = float(value)
    except:
        raise HTTPException(400, "Invalid value")

    if val < 0:
        raise HTTPException(400, "Invalid value")