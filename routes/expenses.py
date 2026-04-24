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
        # 1. Get the starting Balance from the Patient table
        cur.execute("SELECT Balance FROM Patient WHERE PatientID = :1", (pid,))
        p_row = cur.fetchone()
        if not p_row:
            raise HTTPException(404, "Patient not found")
        initial_balance = p_row[0] or 0

        # 2. Get all expenses for this patient
        cur.execute("""
            SELECT ExpenseID, Expense_Name, Expense_Category,
                   Expense_Amount, Expense_Time
            FROM   Expense
            WHERE  PatientID = :1
            ORDER BY Expense_Time DESC
        """, (pid,))
        rows = cur.fetchall()
        
        expense_list = []
        total_spent = 0
        
        for r in rows:
            # Add to the sum of expenses
            total_spent += r[3] # Expense_Amount
            
            expense_list.append({
                "expense_id": r[0],
                "expense_name": r[1],
                "expense_category": r[2],
                "expense_amount": r[3],
                "expense_time": r[4].strftime("%Y-%m-%d %H:%M") if isinstance(r[4], datetime) else r[4]
            })

        # 3. Apply the Formula: Balance - Sum(Expenses)
        final_remaining = initial_balance - total_spent

        return {
            "expenses": expense_list,
            "calculated_balance": round(final_remaining, 2)
        }
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

