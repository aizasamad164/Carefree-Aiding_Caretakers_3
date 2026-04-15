from pydantic import BaseModel
from typing import Optional, List

# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginReq(BaseModel):
    username: str
    password: str
    role: str

class SignupReq(BaseModel):
    name: str
    age: int
    gender: str
    contact: str
    experience_years: int
    qualification: str
    skills: List[str] = []

# ── Patient ───────────────────────────────────────────────────────────────────
class PatientCreate(BaseModel):
    name: str
    gender: str
    age: int
    smoker: str
    children: int
    weight: float
    height: float
    region: str
    caretaker_id: str
    # Guardian fields — inserted into Guardian table
    guardian_name: str
    guardian_contact: str
    relation_with_patient: str

class PatientUpdate(BaseModel):
    name: str
    gender: str
    age: int
    smoker: str
    children: int
    weight: float
    height: float
    region: str
    # Guardian fields — updated on Guardian table
    guardian_name: str
    guardian_contact: str
    relation_with_patient: str

class CommentBody(BaseModel):
    comment: str

# ── Task ──────────────────────────────────────────────────────────────────────
class TaskCreate(BaseModel):
    name: str
    time: str
    frequency: str
    priority: str
    description: str
    patient_id: str
    # CaretakerID resolved server-side from PatientID, not needed here

# ── Appointment ───────────────────────────────────────────────────────────────
class ApptCreate(BaseModel):
    doctor_name: str
    specialization: str
    category: str
    datetime_val: str
    patient_id: str
    description: str
    status: Optional[str] = "Scheduled"

# ── Expense ───────────────────────────────────────────────────────────────────
class ExpCreate(BaseModel):
    name: str
    category: str       # atomic string — no separate CategoryID needed
    amount: float
    patient_id: str

# ── Vitals ────────────────────────────────────────────────────────────────────
class VitalsCreate(BaseModel):
    patient_id: str
    # Cardiac
    pulse_rate: float
    bp_systolic: float
    bp_diastolic: float
    # Respiratory
    respiratory_rate: float
    oxygen_saturation: float
    # OtherVitals
    gfr: float
    serum_creatinine: float
    temperature: float
    blood_sugar: float
    metabolic: float

class VitalsUpdate(BaseModel):
    # No patient_id or recorded_time — supertype fields don't change
    # Cardiac
    pulse_rate: float
    bp_systolic: float
    bp_diastolic: float
    # Respiratory
    respiratory_rate: float
    oxygen_saturation: float
    # OtherVitals
    gfr: float
    serum_creatinine: float
    temperature: float
    blood_sugar: float
    metabolic: float

# ── Caretaker ─────────────────────────────────────────────────────────────────
class CaretakerCreate(BaseModel):
    name: str
    age: int
    gender: str
    contact: str
    experience_years: int
    qualification: str
    skills: List[str] = []

class CaretakerUpdate(BaseModel):
    name: str
    age: int
    gender: str
    contact: str
    experience_years: int
    qualification: str
    skills: Optional[List[str]] = None

# ── Notification ──────────────────────────────────────────────────────────────
class NotifCreate(BaseModel):
    caretaker_id: str
    name: str
    description: str
    task_id: Optional[int] = None
    appointment_id: Optional[int] = None

# ── Balance ───────────────────────────────────────────────────────────────────
class BalanceBody(BaseModel):
    amount: float

# ── ML Predictions ────────────────────────────────────────────────────────────
class StressReq(BaseModel):
    age: int
    sleep_duration: int
    quality_of_sleep: int
    bmi_category: str
    physical_activity: int
    heart_rate: float
    daily_steps: int
    systolic: int
    diastolic: int

class CostReq(BaseModel):
    age: int
    sex: str
    bmi: float
    children: int
    smoker: str
    region: str

# ── Vitals ────────────────────────────────────────────────────────────
class VitalsCreate(BaseModel):
    patient_id: str
    # Cardiac
    pulse_rate: float
    bp_systolic: float
    bp_diastolic: float
    # Respiratory
    respiratory_rate: float
    oxygen_saturation: float
    # OtherVitals
    gfr: float
    serum_creatinine: float
    temperature: float
    blood_sugar: float
    metabolic: float

class VitalsUpdate(BaseModel):
    # No patient_id or recorded_time — supertype fields don't change
    # Cardiac
    pulse_rate: float
    bp_systolic: float
    bp_diastolic: float
    # Respiratory
    respiratory_rate: float
    oxygen_saturation: float
    # OtherVitals
    gfr: float
    serum_creatinine: float
    temperature: float
    blood_sugar: float
    metabolic: float

# ── Symptoms ────────────────────────────────────────────────────────────
class PatientSymptomCreate(BaseModel):
    patient_id: str
    symptom_id: str

class CustomSymptomCreate(BaseModel):
    patient_id: str
    name: str
    type: str
    description: str
    severity: str

# ── Dietary Plan ──────────────────────────────────────────────────────────────
class DietaryPlanCreate(BaseModel):
    duration: str
    patient_id: str
    goals: List[str] = []
    restrictions: List[str] = []

class DietaryPlanUpdate(BaseModel):
    duration: str
    goals: Optional[List[str]] = None
    restrictions: Optional[List[str]] = None

# ── Meal ─────────────────────────────────────────────────────────────────────-
class MealCreate(BaseModel):
    name: str
    flag: Optional[str] = "OK"
    plan_id: str
    ingredients: List[str] = []
    nutrition: dict = {}        # e.g. {"calories": 350, "protein": 20}

class MealUpdate(BaseModel):
    name: str
    flag: Optional[str] = None
    ingredients: Optional[List[str]] = None
    nutrition: Optional[dict] = None