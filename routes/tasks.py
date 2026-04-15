import random
import cx_Oracle
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import TaskCreate
from routes.notifications import send_notification
from datetime import datetime, timedelta

router = APIRouter()

# ── Create Task table if not exists ──────────────────────────────────────────
def create_task_table(db):
    cur = db.cursor()
    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Task (
                    TaskID              NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    Task_Name           VARCHAR2(100)   NOT NULL,
                    Task_Time           TIMESTAMP,
                    Task_Frequency      VARCHAR2(20),
                    Task_Priority       VARCHAR2(10),
                    Task_Description    VARCHAR2(500),
                    Progress            VARCHAR2(20)    DEFAULT ''Pending'',
                    PatientID           VARCHAR2(20)    REFERENCES Patient(PatientID),
                    CaretakerID         VARCHAR2(20)    REFERENCES Caretaker(CaretakerID)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)
    db.commit()
    cur.close()

# ── Get tasks for a patient ───────────────────────────────────────────────────
@router.get("/api/tasks/{pid}")
def get_tasks(pid: str, filter: str = "All", db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT TaskID, Task_Name, Task_Time, Task_Frequency,
               Task_Priority, Task_Description, PatientID, CaretakerID, Progress
        FROM   Task
        WHERE  PatientID = :1
        ORDER BY CASE Task_Priority 
                    WHEN 'High' THEN 1 
                    WHEN 'Medium' THEN 2 
                    ELSE 3 END, Task_Time
    """, (pid,))
    
    rows = cur.fetchall()
    keys = ["task_id", "task_name", "task_time", "task_frequency",
            "task_priority", "task_description", "patient_id", "caretaker_id", "progress"]
    
    now = datetime.now()
    result = []
    for r in rows:
        d = {keys[i]: r[i] for i in range(len(keys))}
        
        # Format the datetime for the frontend
        if isinstance(d["task_time"], datetime):
            dt = d["task_time"]
            # Filtering logic
            if filter == "Today" and dt.date() != now.date(): continue
            if filter == "Weekly" and not (0 <= (dt.date() - now.date()).days < 7): continue
            
            d["task_time"] = dt.strftime("%Y-%m-%d %H:%M")
        
        result.append(d)
    return result

# ── Get single task (For Editing) ─────────────────────────────────────────────
@router.get("/api/task/{tid}")
def get_task(tid: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT Task_Name, Task_Time, Task_Frequency, Task_Priority, Task_Description FROM Task WHERE TaskID = :1", (tid,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Task not found")
    
    return {
        "name": row[0],
        "time": row[1].strftime("%Y-%m-%dT%H:%M") if row[1] else "",
        "frequency": row[2],
        "priority": row[3],
        "description": row[4]
    }

# ── Create task ───────────────────────────────────────────────────────────────
@router.post("/api/task")
def create_task(t: TaskCreate, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT CaretakerID, Patient_Name FROM Patient WHERE PatientID=:1", (t.patient_id,))
    row = cur.fetchone()
    if not row: raise HTTPException(404, "Patient not found")
    cid, pname = row[0], row[1]

    vid_var = cur.var(cx_Oracle.NUMBER)
    task_time = datetime.fromisoformat(t.time.replace('Z', ''))

    cur.execute("""
        INSERT INTO Task (Task_Name, Task_Time, Task_Frequency,
                          Task_Priority, Task_Description, PatientID, CaretakerID)
        VALUES (:1,:2,:3,:4,:5,:6,:7)
        RETURNING TaskID INTO :8
    """, (t.name, task_time, t.frequency, t.priority, t.description, t.patient_id, cid, vid_var))

    task_id = int(vid_var.getvalue()[0])

    # Notify AT the task time
    send_notification(db, cid, f"New Task: {t.name}", 
                      f"Task for {pname} due at {task_time.strftime('%H:%M')}",
                      task_id=task_id, scheduled_time=task_time)

    db.commit()
    return {"message": "Task added", "task_id": task_id}

# ── Update task (The "Edit" functionality) ────────────────────────────────────
@router.put("/api/task/{tid}")
def update_task(tid: int, t: TaskCreate, db=Depends(get_db)):
    cur = db.cursor()
    task_time = datetime.fromisoformat(t.time.replace('Z', ''))

    cur.execute("""
        UPDATE Task 
        SET Task_Name=:1, Task_Time=:2, Task_Frequency=:3, 
            Task_Priority=:4, Task_Description=:5 
        WHERE TaskID=:6
    """, (t.name, task_time, t.frequency, t.priority, t.description, tid))
    
    db.commit()
    return {"message": "Task updated"}

# ── Delete task ───────────────────────────────────────────────────────────────
@router.delete("/api/task/{tid}")
def delete_task(tid: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM Notification WHERE TaskID=:1", (tid,))
    cur.execute("DELETE FROM Task WHERE TaskID=:1", (tid,))
    db.commit()
    return {"message": "Task deleted"}