import random
import cx_Oracle
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import TaskCreate
from routes.notifications import send_notification
from datetime import datetime, timedelta

router = APIRouter()


# ── Helper: next fire time based on frequency ─────────────────────────────────
def get_next_notification_time(original_time: datetime, frequency: str):
    now = datetime.now()
    target = original_time

    if frequency == "Daily":
        while target <= now:
            target += timedelta(days=1)
    elif frequency == "Alternate":
        while target <= now:
            target += timedelta(days=2)
    elif frequency == "Weekly":
        while target <= now:
            target += timedelta(weeks=1)
    elif frequency == "Monthly":
        while target <= now:
            month = target.month + 1
            year  = target.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            target = target.replace(year=year, month=month)
    else:  # Once
        if target <= now:
            return None

    return target


# ── Stats — MUST be before /api/tasks/{pid} ───────────────────────────────────
@router.get("/api/tasks/stats/{cid}")
def get_task_stats(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        now = datetime.now()
        cur.execute("""
            SELECT t.TaskID, t.Task_Time, t.Task_Frequency
            FROM   Task t
            JOIN   Patient p ON p.PatientID = t.PatientID
            WHERE  p.CaretakerID = :1
        """, (cid,))
        rows = cur.fetchall()
        count = 0
        for task_id, task_time, frequency in rows:
            if not isinstance(task_time, datetime):
                continue
            next_time = get_next_notification_time(task_time, frequency) or task_time
            if next_time.date() == now.date():
                count += 1
        return {"count": count}
    finally:
        cur.close()


# ── Refresh — MUST be before /api/tasks/{pid} ────────────────────────────────
@router.post("/api/tasks/refresh/{cid}")
def refresh_tasks(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT t.TaskID, t.Task_Name, t.Task_Time, t.Task_Frequency,
                   t.PatientID, p.Patient_Name, p.CaretakerID
            FROM   Task t
            JOIN   Patient p ON p.PatientID = t.PatientID
            WHERE  p.CaretakerID = :1
              AND  t.Task_Frequency != 'Once'
        """, (cid,))
        rows = cur.fetchall()
        now  = datetime.now()

        for task_id, name, task_time, frequency, pid, pname, c_id in rows:
            if not isinstance(task_time, datetime):
                continue
            cur.execute("""
                SELECT COUNT(*) FROM Notification
                WHERE  TaskID     = :1
                  AND  Notif_Time > :2
                  AND  Is_Sent    = 0
            """, (task_id, now))
            if cur.fetchone()[0] == 0:
                next_time = get_next_notification_time(task_time, frequency)
                if next_time:
                    send_notification(db, c_id,
                        f"Task Reminder: {name}",
                        f"Task for {pname} due at {task_time.strftime('%H:%M')}",
                        task_id=task_id, scheduled_time=next_time)

        db.commit()
        return {"message": "Notifications refreshed"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Refresh error: {str(e)}")
    finally:
        cur.close()


# ── Get tasks for a patient ───────────────────────────────────────────────────
@router.get("/api/tasks/{pid}")
def get_tasks(pid: str, filter: str = "All", db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT TaskID, Task_Name, Task_Time, Task_Frequency,
                   Task_Priority, Task_Description, PatientID, CaretakerID, Progress
            FROM   Task
            WHERE  PatientID = :1
            ORDER BY CASE Task_Priority
                        WHEN 'High'   THEN 1
                        WHEN 'Medium' THEN 2
                        ELSE 3 END, Task_Time
        """, (pid,))
        rows = cur.fetchall()
        keys = ["task_id", "task_name", "task_time", "task_frequency",
                "task_priority", "task_description", "patient_id", "caretaker_id", "progress"]
        now = datetime.now()
        result = []
        for r in rows:
            d = {}
            for i, val in enumerate(r):
                if hasattr(val, 'read'):
                    val = val.read()
                d[keys[i]] = val
            if isinstance(d["task_time"], datetime):
                dt = d["task_time"]
                display_dt = get_next_notification_time(dt, d["task_frequency"]) or dt
                if filter == "Today"  and display_dt.date() != now.date(): continue
                if filter == "Weekly" and not (0 <= (display_dt.date() - now.date()).days < 7): continue
                d["task_time"] = display_dt.strftime("%Y-%m-%d %H:%M")
            result.append(d)
        return result
    finally:
        cur.close()


# ── Get single task ───────────────────────────────────────────────────────────
@router.get("/api/task/{tid}")
def get_task(tid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT Task_Name, Task_Time, Task_Frequency, Task_Priority, Task_Description
            FROM   Task WHERE TaskID = :1
        """, (tid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        return {
            "name":        row[0],
            "time":        row[1].strftime("%Y-%m-%dT%H:%M") if row[1] else "",
            "frequency":   row[2],
            "priority":    row[3],
            "description": row[4]
        }
    finally:
        cur.close()


# ── Create task ───────────────────────────────────────────────────────────────
@router.post("/api/task")
def create_task(t: TaskCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT CaretakerID, Patient_Name FROM Patient WHERE PatientID=:1", (t.patient_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Patient not found")
        cid, pname = row[0], row[1]

        vid_var   = cur.var(cx_Oracle.NUMBER)
        task_time = datetime.fromisoformat(t.time.replace('Z', ''))

        cur.execute("""
            INSERT INTO Task (Task_Name, Task_Time, Task_Frequency,
                              Task_Priority, Task_Description, PatientID, CaretakerID)
            VALUES (:1,:2,:3,:4,:5,:6,:7)
            RETURNING TaskID INTO :8
        """, (t.name, task_time, t.frequency, t.priority,
              t.description, t.patient_id, cid, vid_var))

        task_id = int(vid_var.getvalue()[0])
        next_time = get_next_notification_time(task_time, t.frequency)
        if next_time:
            send_notification(db, cid,
                f"Task Reminder: {t.name}",
                f"Task for {pname} due at {task_time.strftime('%H:%M')}",
                task_id=task_id, scheduled_time=next_time)

        db.commit()
        return {"message": "Task added", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating task: {str(e)}")
    finally:
        cur.close()


# ── Update task ───────────────────────────────────────────────────────────────
@router.put("/api/task/{tid}")
def update_task(tid: int, t: TaskCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        task_time = datetime.fromisoformat(t.time.replace('Z', ''))
        cur.execute("""
            UPDATE Task
            SET Task_Name=:1, Task_Time=:2, Task_Frequency=:3,
                Task_Priority=:4, Task_Description=:5
            WHERE TaskID=:6
        """, (t.name, task_time, t.frequency, t.priority, t.description, tid))

        cur.execute("SELECT CaretakerID, Patient_Name FROM Patient WHERE PatientID=:1", (t.patient_id,))
        row = cur.fetchone()
        if row:
            cid, pname = row[0], row[1]
            cur.execute("DELETE FROM Notification WHERE TaskID=:1", (tid,))
            next_time = get_next_notification_time(task_time, t.frequency)
            if next_time:
                send_notification(db, cid,
                    f"Task Reminder: {t.name}",
                    f"Task for {pname} due at {task_time.strftime('%H:%M')}",
                    task_id=tid, scheduled_time=next_time)

        db.commit()
        return {"message": "Task updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error updating task: {str(e)}")
    finally:
        cur.close()


# ── Delete task ───────────────────────────────────────────────────────────────
@router.delete("/api/task/{tid}")
def delete_task(tid: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM Notification WHERE TaskID=:1", (tid,))
        cur.execute("DELETE FROM Task          WHERE TaskID=:1", (tid,))
        db.commit()
        return {"message": "Task deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error deleting task: {str(e)}")
    finally:
        cur.close()