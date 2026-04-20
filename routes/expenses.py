import random
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import ExpCreate
from datetime import datetime
from routes.notifications import send_notification
import uuid

router = APIRouter()


# ── Stats — MUST be before /api/expenses/{pid} ───────────────────────────────
@router.get("/api/expenses/stats/{cid}")
def get_exp_stats(cid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM Expense e
            JOIN   Patient p ON p.PatientID = e.PatientID
            WHERE  p.CaretakerID = :1
        """, (cid,))
        return {"count": cur.fetchone()[0]}
    finally:
        cur.close()


# ── Get expenses for a patient ────────────────────────────────────────────────
@router.get("/api/expenses/{pid}")
def get_expenses(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT ExpenseID, Expense_Name, Expense_Category,
                   Expense_Amount, Expense_Time, PatientID
            FROM   Expense
            WHERE  PatientID = :1
            ORDER BY Expense_Time DESC
        """, (pid,))
        rows = cur.fetchall()
        keys = ["expense_id", "expense_name", "expense_category",
                "expense_amount", "expense_time", "patient_id"]
        result = []
        for r in rows:
            d = {keys[i]: r[i] for i in range(len(keys))}
            if isinstance(d["expense_time"], datetime):
                d["expense_time"] = d["expense_time"].strftime("%Y-%m-%d %H:%M")
            result.append(d)
        return result
    finally:
        cur.close()


# ── Create expense ────────────────────────────────────────────────────────────
@router.post("/api/expense")
def create_expense(e: ExpCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT CaretakerID, Patient_Name FROM Patient WHERE PatientID=:1",
                    (e.patient_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Patient not found")
        cid, pname = row[0], row[1]

        eid = f"E-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        cur.execute("""
            INSERT INTO Expense (ExpenseID, Expense_Name, Expense_Category,
                                 Expense_Amount, Expense_Time, PatientID)
            VALUES (:1,:2,:3,:4,TO_TIMESTAMP(:5, 'YYYY-MM-DD"T"HH24:MI:SS.FF'),:6)
        """, (eid, e.name, e.category, e.amount, now, e.patient_id))

        cur.execute("""
            UPDATE Patient SET Charges=(
                SELECT NVL(SUM(Expense_Amount),0) FROM Expense WHERE PatientID=:1)
            WHERE PatientID=:2
        """, (e.patient_id, e.patient_id))

        send_notification(
            db, cid,
            name=f"New Expense: {e.name}",
            description=f"Rs. {e.amount} added for {pname}"
        )

        db.commit()
        return {"message": "Expense added", "expense_id": eid}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating expense: {str(e)}")
    finally:
        cur.close()


# ── Delete expense ────────────────────────────────────────────────────────────
@router.delete("/api/expense/{eid}")
def delete_expense(eid: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT PatientID FROM Expense WHERE ExpenseID=:1", (eid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Expense not found")
        pid = row[0]

        cur.execute("DELETE FROM Expense WHERE ExpenseID=:1", (eid,))
        cur.execute("""
            UPDATE Patient SET Charges=(
                SELECT NVL(SUM(Expense_Amount),0) FROM Expense WHERE PatientID=:1)
            WHERE PatientID=:2
        """, (pid, pid))

        db.commit()
        return {"message": "Expense deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error deleting expense: {str(e)}")
    finally:
        cur.close()