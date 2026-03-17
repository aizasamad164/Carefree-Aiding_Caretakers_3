import random
from fastapi import APIRouter, Depends
from database import get_db
from models import TaskCreate
from datetime import datetime

router = APIRouter()

# ── Get tasks for a patient ───────────────────────────────────────────────────
@router.get("/api/tasks/{pid}")
def get_tasks(pid: str, filter: str="All", db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Task_ID, Task_Name, Task_Time, Task_Frequency,
                          Task_Priority, Task_Description, P_ID
                   FROM Task WHERE P_ID=:1
                   ORDER BY Task_Priority DESC, Task_Time""", (pid,))
    rows = cur.fetchall()
    keys = ["task_id","task_name","task_time","task_frequency",
            "task_priority","task_description","p_id"]
    now = datetime.now()
    result = []
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

# ── Create task ───────────────────────────────────────────────────────────────
@router.post("/api/task")
def create_task(t: TaskCreate, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""INSERT INTO Task (Task_Name,Task_Time,Task_Frequency,
                   Task_Priority,Task_Description,P_ID)
                   VALUES (:1,:2,:3,:4,:5,:6)""",
                (t.name,t.time,t.frequency,t.priority,t.description,t.patient_id))

    # ── Auto notification ──────────────────────────────────────────────────────
    cur.execute("SELECT C_ID, Patient_Name FROM Patient WHERE Patient_ID=:1", (t.patient_id,))
    row = cur.fetchone()
    if row:
        cid, pname = row[0], row[1]
        nid = f"N-{random.randint(10000,99999)}"
        now = datetime.now().isoformat()
        cur.execute("INSERT INTO Notification VALUES (:1,:2,:3,:4,:5)",
                    (nid, cid, now,
                     f"New Task: {t.name}",
                     f"Task '{t.name}' added for {pname} — due {t.time}"))
    # ──────────────────────────────────────────────────────────────────────────

    db.commit()
    return {"message":"Task added"}

# ── Delete task ───────────────────────────────────────────────────────────────
@router.delete("/api/task/{tid}")
def delete_task(tid: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM Task WHERE Task_ID=:1", (tid,))
    db.commit()
    return {"message":"Task deleted"}
