from pydantic import BaseModel
from typing import Optional

# ── Auth ───────────────────────────────────────────────────────────────────────
class LoginReq(BaseModel):
    username: str
    password: str
    role: str

class SignupReq(BaseModel):
    name: str
    age: int
    gender: str
    contact: str
    skills: str

# ── Patient ────────────────────────────────────────────────────────────────────
class PatientCreate(BaseModel):
    name: str
    gender: str
    age: int
    smoker: str
    children: int
    weight: float
    height: float
    guardian_name: str
    guardian_contact: str
    region: str
    caretaker_id: str

class PatientUpdate(BaseModel):
    name: str
    gender: str
    age: int
    smoker: str
    children: int
    weight: float
    height: float
    guardian_name: str
    guardian_contact: str
    region: str

class CommentBody(BaseModel):
    patient_id: str
    comment: str

class BalanceBody(BaseModel):
    patient_id: str
    amount: float

# ── Task ───────────────────────────────────────────────────────────────────────
class TaskCreate(BaseModel):
    name: str
    time: str
    frequency: str
    priority: int
    description: str
    patient_id: str

# ── Appointment ────────────────────────────────────────────────────────────────
class ApptCreate(BaseModel):
    client_name: str
    category: str
    datetime_val: str
    patient_id: str
    description: str

# ── Expense ────────────────────────────────────────────────────────────────────
class ExpCreate(BaseModel):
    name: str
    category: str
    amount: float
    patient_id: str

# ── Notification ───────────────────────────────────────────────────────────────
class NotifCreate(BaseModel):
    caretaker_id: str
    name: str
    description: str

# ── ML Predictions ─────────────────────────────────────────────────────────────
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
