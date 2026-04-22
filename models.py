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
    guardian_name: str
    guardian_contact: str
    relation_with_patient: str

class CommentBody(BaseModel):
    comment: str

class BalanceBody(BaseModel):
    amount: float

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

# ── Task ──────────────────────────────────────────────────────────────────────
class TaskCreate(BaseModel):
    name: str
    time: str
    frequency: str
    priority: str
    description: str
    patient_id: str

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
    category: str
    amount: float
    patient_id: str

# ── Vitals ────────────────────────────────────────────────────────────────────
class VitalsCreate(BaseModel):
    patient_id: str
    vitals_category: Optional[str] = None
    # CardiacVitals
    pulse_rate: Optional[float] = None
    blood_pressure: Optional[float] = None
    # RespiratoryVitals
    respiratory_rate: Optional[float] = None
    oxygen_sat: Optional[float] = None
    # OtherVitals
    blood_glucose: Optional[float] = None

class VitalsUpdate(BaseModel):
    # CardiacVitals
    pulse_rate: Optional[float] = None
    blood_pressure: Optional[float] = None
    # RespiratoryVitals
    respiratory_rate: Optional[float] = None
    oxygen_sat: Optional[float] = None
    # OtherVitals
    blood_glucose: Optional[float] = None

# ── Symptoms ──────────────────────────────────────────────────────────────────
class PatientSymptomCreate(BaseModel):
    patient_id: str
    symptom_id: str  # must exist in SymptomMaster

class CustomSymptomCreate(BaseModel):
    patient_id: str
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None

# ── Notification ──────────────────────────────────────────────────────────────
class NotifCreate(BaseModel):
    caretaker_id: str
    name: str
    description: str
    task_id: Optional[int] = None
    appointment_id: Optional[int] = None

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
