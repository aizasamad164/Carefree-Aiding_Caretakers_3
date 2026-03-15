from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import random, string
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
import cx_Oracle

# ── Load config ────────────────────────────────────────────────────────────────
from config import DB_HOST, DB_PORT, DB_SERVICE, DB_USER, DB_PASSWORD, DB_MODE

# ── ML Models ──────────────────────────────────────────────────────────────────
def train_stress_model():
    try:
        df = pd.read_csv("Sleep_health_and_lifestyle_dataset.csv")
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df.dropna(inplace=True)
        def split_bp(bp):
            if isinstance(bp, str) and "/" in bp:
                s, d = bp.split("/")
                return pd.Series([float(s), float(d)])
            return pd.Series([np.nan, np.nan])
        df[['systolic_bp','diastolic_bp']] = df['blood_pressure'].apply(split_bp)
        df.drop(columns=['blood_pressure'], inplace=True)
        def cat_stress(x):
            if x <= 4: return "Low"
            elif x <= 6: return "Moderate"
            else: return "High"
        df['cat_stress'] = df['stress_level'].apply(cat_stress)
        df['sleep_eff'] = df['sleep_duration'] * df['quality_of_sleep']
        bmi_map = {'Obese':0,'Normal':1,'Normal Weight':1,'Overweight':2}
        df['bmi_category'] = df['bmi_category'].str.strip().map(bmi_map).fillna(1).astype(int)
        feats = ['age','sleep_eff','bmi_category','physical_activity_level',
                 'heart_rate','daily_steps','systolic_bp','diastolic_bp']
        X, y = df[feats], df['cat_stress']
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        m = DecisionTreeClassifier(random_state=42, max_depth=3,
                                   min_samples_split=5, min_samples_leaf=2)
        m.fit(X_tr, y_tr)
        print(f"Stress model accuracy: {m.score(X_te, y_te):.2%}")
        return m
    except Exception as e:
        print(f"Stress model failed: {e}"); return None

def train_cost_model():
    try:
        df = pd.read_csv("insurance.csv")
        X, y = df[["age","sex","bmi","children","smoker","region"]], df["charges"]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        cat_feats = ["sex","smoker","region"]
        pre = ColumnTransformer(
            [('cat', OneHotEncoder(handle_unknown='ignore'), cat_feats)],
            remainder='passthrough'
        )
        pipe = Pipeline([('pre', pre),
                         ('reg', GradientBoostingRegressor(learning_rate=0.04, random_state=42))])
        pipe.fit(X_tr, y_tr)
        print(f"Cost model R²: {pipe.score(X_te, y_te):.3f}")
        return pipe
    except Exception as e:
        print(f"Cost model failed: {e}"); return None

stress_model = train_stress_model()
cost_model   = train_cost_model()

# ── Oracle Connection ──────────────────────────────────────────────────────────
def get_dsn():
    if DB_MODE == "SID":
        return cx_Oracle.makedsn(DB_HOST, DB_PORT, sid=DB_SERVICE)
    else:
        return cx_Oracle.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)

def get_db():
    conn = cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=get_dsn())
    try:
        yield conn
    finally:
        conn.close()

def row_to_dict(cursor, row):
    """Convert Oracle row to dictionary using cursor description."""
    return {cursor.description[i][0].lower(): row[i] for i in range(len(row))}

def rows_to_list(cursor, rows):
    """Convert list of Oracle rows to list of dicts."""
    return [row_to_dict(cursor, r) for r in rows]

# ── Database Init ──────────────────────────────────────────────────────────────
def table_exists(cursor, name):
    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :1", (name.upper(),))
    return cursor.fetchone()[0] > 0

def init_db():
    conn = cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=get_dsn())
    cur  = conn.cursor()

    # Caretaker table
    if not table_exists(cur, 'Caretaker'):
        cur.execute("""
            CREATE TABLE Caretaker (
                Caretaker_ID       VARCHAR2(20)  PRIMARY KEY,
                Caretaker_Name     VARCHAR2(100) NOT NULL UNIQUE,
                Caretaker_Age      NUMBER(3),
                Caretaker_Password VARCHAR2(100) NOT NULL,
                Caretaker_Gender   VARCHAR2(10),
                Caretaker_Contact  VARCHAR2(20),
                Caretaker_Skills   VARCHAR2(300)
            )
        """)

    # Patient table
    if not table_exists(cur, 'Patient'):
        cur.execute("""
            CREATE TABLE Patient (
                Patient_ID        VARCHAR2(20)  PRIMARY KEY,
                Patient_Name      VARCHAR2(100) NOT NULL,
                Guardian_Password VARCHAR2(100),
                Patient_Gender    VARCHAR2(10),
                Age               NUMBER(3),
                Patient_Smoker    VARCHAR2(5),
                Patient_Children  NUMBER(2),
                Patient_Weight    NUMBER(6,2),
                Patient_Height    NUMBER(6,2),
                Guardian_Name     VARCHAR2(100),
                Guardian_Contact  VARCHAR2(20),
                C_ID              VARCHAR2(20)  REFERENCES Caretaker(Caretaker_ID),
                Guardian_Comment  VARCHAR2(1000),
                Patient_Region    VARCHAR2(20),
                Charges           NUMBER(10,2)  DEFAULT 0,
                Balance           NUMBER(10,2)  DEFAULT 0
            )
        """)

    # Task table
    if not table_exists(cur, 'Task'):
        cur.execute("""
            CREATE TABLE Task (
                Task_ID          NUMBER        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                Task_Name        VARCHAR2(200) NOT NULL,
                Task_Time        VARCHAR2(50),
                Task_Frequency   VARCHAR2(50),
                Task_Priority    NUMBER(1),
                Task_Description VARCHAR2(500),
                P_ID             VARCHAR2(20)  REFERENCES Patient(Patient_ID)
            )
        """)

    # Appointment table
    if not table_exists(cur, 'Appointment'):
        cur.execute("""
            CREATE TABLE Appointment (
                Appointment_ID          NUMBER        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                Client_Name             VARCHAR2(100),
                Appointment_Category    VARCHAR2(50),
                Appointment_DateTime    VARCHAR2(50),
                P_ID                    VARCHAR2(20)  REFERENCES Patient(Patient_ID),
                Appointment_Description VARCHAR2(500)
            )
        """)

    # Expenses table
    if not table_exists(cur, 'Expenses'):
        cur.execute("""
            CREATE TABLE Expenses (
                Expense_ID       VARCHAR2(20)  PRIMARY KEY,
                Expense_Name     VARCHAR2(200),
                Expense_Category VARCHAR2(100),
                Expense_Amount   NUMBER(10,2),
                Expense_Time     VARCHAR2(50),
                P_ID             VARCHAR2(20)  REFERENCES Patient(Patient_ID)
            )
        """)

    # Seed default admin caretaker
    cur.execute("SELECT COUNT(*) FROM Caretaker WHERE Caretaker_ID = 'C-00001'")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO Caretaker VALUES
            ('C-00001','admin',30,'admin123','Male','03001234567','General Care')
        """)

    conn.commit()
    cur.close()
    conn.close()
    print("Oracle DB initialized successfully.")

# ── Helpers ────────────────────────────────────────────────────────────────────
def gen_id(prefix, table, col, db):
    cur = db.cursor()
    while True:
        nid = f"{prefix}-{random.randint(10000,99999)}"
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col}=:1", (nid,))
        if cur.fetchone()[0] == 0:
            cur.close()
            return nid

def gen_pw(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

# ── Pydantic Schemas ───────────────────────────────────────────────────────────
class LoginReq(BaseModel):
    username: str; password: str; role: str

class SignupReq(BaseModel):
    name: str; age: int; gender: str; contact: str; skills: str

class PatientCreate(BaseModel):
    name: str; gender: str; age: int; smoker: str; children: int
    weight: float; height: float; guardian_name: str
    guardian_contact: str; region: str; caretaker_id: str

class PatientUpdate(BaseModel):
    name: str; gender: str; age: int; smoker: str; children: int
    weight: float; height: float; guardian_name: str
    guardian_contact: str; region: str

class TaskCreate(BaseModel):
    name: str; time: str; frequency: str; priority: int
    description: str; patient_id: str

class ApptCreate(BaseModel):
    client_name: str; category: str; datetime_val: str
    patient_id: str; description: str

class ExpCreate(BaseModel):
    name: str; category: str; amount: float; patient_id: str

class CommentBody(BaseModel):
    patient_id: str; comment: str

class BalanceBody(BaseModel):
    patient_id: str; amount: float

class StressReq(BaseModel):
    age: int; sleep_duration: int; quality_of_sleep: int
    bmi_category: str; physical_activity: int; heart_rate: float
    daily_steps: int; systolic: int; diastolic: int

class CostReq(BaseModel):
    age: int; sex: str; bmi: float; children: int; smoker: str; region: str

# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(title="Carefree API", version="3.0 — Oracle Edition")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup():
    init_db()

# ── Pages ──────────────────────────────────────────────────────────────────────
@app.get("/")
def login_page(): return FileResponse("templates/login.html")

@app.get("/caretaker")
def caretaker_page(): return FileResponse("templates/caretaker.html")

@app.get("/guardian")
def guardian_page(): return FileResponse("templates/guardian.html")

# ── Auth ───────────────────────────────────────────────────────────────────────
@app.post("/api/login")
def login(r: LoginReq, db=Depends(get_db)):
    cur = db.cursor()
    if r.role == "caretaker":
        cur.execute("""SELECT Caretaker_ID, Caretaker_Name FROM Caretaker
                       WHERE Caretaker_Name=:1 AND Caretaker_Password=:2""",
                    (r.username, r.password))
        row = cur.fetchone()
        if not row: raise HTTPException(401, "Invalid credentials")
        return {"role":"caretaker","id":row[0],"name":row[1]}
    elif r.role == "guardian":
        cur.execute("""SELECT Patient_ID, Guardian_Name FROM Patient
                       WHERE Guardian_Name=:1 AND Guardian_Password=:2""",
                    (r.username, r.password))
        row = cur.fetchone()
        if not row: raise HTTPException(401, "Invalid credentials")
        return {"role":"guardian","patient_id":row[0],"name":row[1]}
    raise HTTPException(400, "Invalid role")

@app.post("/api/signup")
def signup(r: SignupReq, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM Caretaker WHERE Caretaker_Name=:1", (r.name,))
    if cur.fetchone()[0]: raise HTTPException(400, "Username already taken")
    cid = gen_id("C","Caretaker","Caretaker_ID",db)
    pw  = gen_pw()
    cur.execute("""INSERT INTO Caretaker VALUES (:1,:2,:3,:4,:5,:6,:7)""",
                (cid,r.name,r.age,pw,r.gender,r.contact,r.skills))
    db.commit()
    return {"caretaker_id":cid,"password":pw,"message":"Account created"}

# ── Patients ───────────────────────────────────────────────────────────────────
@app.get("/api/patients/{cid}")
def get_patients(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Patient_ID, Patient_Name, Guardian_Name, Guardian_Contact,
                          Guardian_Comment, Balance, Charges
                   FROM Patient WHERE C_ID=:1 ORDER BY Patient_Name""", (cid,))
    rows = cur.fetchall()
    keys = ["patient_id","patient_name","guardian_name","guardian_contact",
            "guardian_comment","balance","charges"]
    return [{keys[i]:r[i] for i in range(len(keys))} for r in rows]

@app.get("/api/patient/{pid}")
def get_patient(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM Patient WHERE Patient_ID=:1", (pid,))
    row = cur.fetchone()
    if not row: raise HTTPException(404, "Patient not found")
    return row_to_dict(cur, row)

@app.post("/api/patient")
def create_patient(p: PatientCreate, db=Depends(get_db)):
    cur = db.cursor()
    pid = gen_id("P","Patient","Patient_ID",db)
    pw  = gen_pw()
    cur.execute("""INSERT INTO Patient (Patient_ID,Patient_Name,Guardian_Password,
                   Patient_Gender,Age,Patient_Smoker,Patient_Children,Patient_Weight,
                   Patient_Height,Guardian_Name,Guardian_Contact,C_ID,Patient_Region)
                   VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13)""",
                (pid,p.name,pw,p.gender,p.age,p.smoker,p.children,
                 p.weight,p.height,p.guardian_name,p.guardian_contact,
                 p.caretaker_id,p.region))
    db.commit()
    return {"patient_id":pid,"guardian_password":pw}

@app.put("/api/patient/{pid}")
def update_patient(pid: str, p: PatientUpdate, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""UPDATE Patient SET Patient_Name=:1,Patient_Gender=:2,Age=:3,
                   Patient_Smoker=:4,Patient_Children=:5,Patient_Weight=:6,
                   Patient_Height=:7,Guardian_Name=:8,Guardian_Contact=:9,
                   Patient_Region=:10 WHERE Patient_ID=:11""",
                (p.name,p.gender,p.age,p.smoker,p.children,p.weight,p.height,
                 p.guardian_name,p.guardian_contact,p.region,pid))
    db.commit()
    return {"message":"Updated"}

@app.delete("/api/patient/{pid}")
def delete_patient(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    # Delete related records first (foreign key constraint)
    cur.execute("DELETE FROM Task        WHERE P_ID=:1", (pid,))
    cur.execute("DELETE FROM Appointment WHERE P_ID=:1", (pid,))
    cur.execute("DELETE FROM Expenses    WHERE P_ID=:1", (pid,))
    cur.execute("DELETE FROM Patient     WHERE Patient_ID=:1", (pid,))
    db.commit()
    return {"message":"Patient deleted"}

@app.put("/api/patient/{pid}/comment")
def update_comment(pid: str, b: CommentBody, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("UPDATE Patient SET Guardian_Comment=:1 WHERE Patient_ID=:2",
                (b.comment, pid))
    db.commit()
    return {"message":"Comment saved"}

@app.put("/api/patient/{pid}/balance")
def add_balance(pid: str, b: BalanceBody, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("UPDATE Patient SET Balance=Balance+:1 WHERE Patient_ID=:2",
                (b.amount, pid))
    db.commit()
    cur.execute("SELECT Balance FROM Patient WHERE Patient_ID=:1", (pid,))
    row = cur.fetchone()
    return {"balance": float(row[0])}

# ── Tasks ──────────────────────────────────────────────────────────────────────
@app.get("/api/tasks/{pid}")
def get_tasks(pid: str, filter: str="All", db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Task_ID,Task_Name,Task_Time,Task_Frequency,
                          Task_Priority,Task_Description,P_ID
                   FROM Task WHERE P_ID=:1
                   ORDER BY Task_Priority DESC, Task_Time""", (pid,))
    rows = cur.fetchall()
    keys = ["task_id","task_name","task_time","task_frequency",
            "task_priority","task_description","p_id"]
    now = datetime.now(); result = []
    for r in rows:
        d = {keys[i]:r[i] for i in range(len(keys))}
        try:
            dt = datetime.fromisoformat(str(d["task_time"]))
            if filter=="Today"   and dt.date()!=now.date(): continue
            if filter=="Weekly"  and not (0<=(dt.date()-now.date()).days<7): continue
            if filter=="Monthly" and (dt.year!=now.year or dt.month!=now.month): continue
        except: pass
        result.append(d)
    return result

@app.post("/api/task")
def create_task(t: TaskCreate, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""INSERT INTO Task (Task_Name,Task_Time,Task_Frequency,
                   Task_Priority,Task_Description,P_ID)
                   VALUES (:1,:2,:3,:4,:5,:6)""",
                (t.name,t.time,t.frequency,t.priority,t.description,t.patient_id))
    db.commit()
    return {"message":"Task added"}

@app.delete("/api/task/{tid}")
def delete_task(tid: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM Task WHERE Task_ID=:1", (tid,))
    db.commit()
    return {"message":"Task deleted"}

# ── Appointments ───────────────────────────────────────────────────────────────
@app.get("/api/appointments/{pid}")
def get_appts(pid: str, filter: str="All", db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Appointment_ID,Client_Name,Appointment_Category,
                          Appointment_DateTime,P_ID,Appointment_Description
                   FROM Appointment WHERE P_ID=:1
                   ORDER BY Appointment_DateTime""", (pid,))
    rows = cur.fetchall()
    keys = ["appointment_id","client_name","appointment_category",
            "appointment_datetime","p_id","appointment_description"]
    now = datetime.now(); result = []
    for r in rows:
        d = {keys[i]:r[i] for i in range(len(keys))}
        try:
            dt = datetime.fromisoformat(str(d["appointment_datetime"]))
            if filter=="Today"   and dt.date()!=now.date(): continue
            if filter=="Weekly"  and not (0<=(dt.date()-now.date()).days<7): continue
            if filter=="Monthly" and (dt.year!=now.year or dt.month!=now.month): continue
        except: pass
        result.append(d)
    return result

@app.post("/api/appointment")
def create_appt(a: ApptCreate, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""INSERT INTO Appointment (Client_Name,Appointment_Category,
                   Appointment_DateTime,P_ID,Appointment_Description)
                   VALUES (:1,:2,:3,:4,:5)""",
                (a.client_name,a.category,a.datetime_val,a.patient_id,a.description))
    db.commit()
    return {"message":"Appointment added"}

@app.delete("/api/appointment/{aid}")
def delete_appt(aid: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM Appointment WHERE Appointment_ID=:1", (aid,))
    db.commit()
    return {"message":"Appointment deleted"}

# ── Expenses ───────────────────────────────────────────────────────────────────
@app.get("/api/expenses/{pid}")
def get_expenses(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Expense_ID,Expense_Name,Expense_Category,
                          Expense_Amount,Expense_Time,P_ID
                   FROM Expenses WHERE P_ID=:1
                   ORDER BY Expense_Time DESC""", (pid,))
    rows = cur.fetchall()
    keys = ["expense_id","expense_name","expense_category",
            "expense_amount","expense_time","p_id"]
    return [{keys[i]:r[i] for i in range(len(keys))} for r in rows]

@app.post("/api/expense")
def create_expense(e: ExpCreate, db=Depends(get_db)):
    cur = db.cursor()
    eid = f"E-{random.randint(1,99999)}"
    now = datetime.now().isoformat()
    cur.execute("INSERT INTO Expenses VALUES (:1,:2,:3,:4,:5,:6)",
                (eid,e.name,e.category,e.amount,now,e.patient_id))
    # Update total charges
    cur.execute("""UPDATE Patient SET Charges=(
                   SELECT NVL(SUM(Expense_Amount),0) FROM Expenses WHERE P_ID=:1)
                   WHERE Patient_ID=:2""", (e.patient_id,e.patient_id))
    db.commit()
    return {"message":"Expense added","expense_id":eid}

@app.delete("/api/expense/{eid}")
def delete_expense(eid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT P_ID FROM Expenses WHERE Expense_ID=:1", (eid,))
    row = cur.fetchone()
    if row:
        pid = row[0]
        cur.execute("DELETE FROM Expenses WHERE Expense_ID=:1", (eid,))
        cur.execute("""UPDATE Patient SET Charges=(
                       SELECT NVL(SUM(Expense_Amount),0) FROM Expenses WHERE P_ID=:1)
                       WHERE Patient_ID=:2""", (pid,pid))
        db.commit()
    return {"message":"Expense deleted"}

# ── ML Predictions ─────────────────────────────────────────────────────────────
@app.post("/api/predict/stress")
def predict_stress(d: StressReq):
    if not stress_model: raise HTTPException(503, "Stress model unavailable")
    bmi = {"Obese":0,"Normal":1,"Overweight":2}.get(d.bmi_category,1)
    inp = np.array([[d.age, d.sleep_duration*d.quality_of_sleep, bmi,
                     d.physical_activity, d.heart_rate, d.daily_steps,
                     d.systolic, d.diastolic]])
    return {"stress_level": str(stress_model.predict(inp)[0])}

@app.post("/api/predict/cost")
def predict_cost(d: CostReq, patient_id: Optional[str]=None, db=Depends(get_db)):
    if not cost_model: raise HTTPException(503, "Cost model unavailable")
    df = pd.DataFrame([{"age":d.age,"sex":d.sex.lower(),"bmi":d.bmi,
                         "children":d.children,"smoker":d.smoker.lower(),
                         "region":d.region.lower()}])
    pred = float(cost_model.predict(df)[0])
    if patient_id:
        cur = db.cursor()
        cur.execute("UPDATE Patient SET Charges=:1 WHERE Patient_ID=:2",
                    (pred, patient_id))
        db.commit()
    return {"predicted_cost": round(pred,2)}