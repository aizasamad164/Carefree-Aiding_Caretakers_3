import random
from fastapi import APIRouter, Depends
from database import get_db
from models import ExpCreate
from datetime import datetime

router = APIRouter()

# ── Get expenses for a patient ────────────────────────────────────────────────
@router.get("/api/expenses/{pid}")
def get_expenses(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""SELECT Expense_ID, Expense_Name, Expense_Category,
                          Expense_Amount, Expense_Time, P_ID
                   FROM Expenses WHERE P_ID=:1
                   ORDER BY Expense_Time DESC""", (pid,))
    rows = cur.fetchall()
    keys = ["expense_id","expense_name","expense_category",
            "expense_amount","expense_time","p_id"]
    return [{keys[i]:r[i] for i in range(len(keys))} for r in rows]

# ── Create expense ────────────────────────────────────────────────────────────
@router.post("/api/expense")
def create_expense(e: ExpCreate, db=Depends(get_db)):
    cur = db.cursor()
    eid = f"E-{random.randint(1,99999)}"
    now = datetime.now().isoformat()
    cur.execute("INSERT INTO Expenses VALUES (:1,:2,:3,:4,:5,:6)",
                (eid,e.name,e.category,e.amount,now,e.patient_id))

    # Update total charges on patient
    cur.execute("""UPDATE Patient SET Charges=(
                   SELECT NVL(SUM(Expense_Amount),0) FROM Expenses WHERE P_ID=:1)
                   WHERE Patient_ID=:2""", (e.patient_id,e.patient_id))

    # ── Auto notification ──────────────────────────────────────────────────────
    cur.execute("SELECT C_ID, Patient_Name FROM Patient WHERE Patient_ID=:1", (e.patient_id,))
    row = cur.fetchone()
    if row:
        cid, pname = row[0], row[1]
        nid = f"N-{random.randint(10000,99999)}"
        cur.execute("INSERT INTO Notification VALUES (:1,:2,:3,:4,:5)",
                    (nid, cid, now,
                     f"New Expense: {e.name}",
                     f"Rs. {e.amount} ({e.category}) added for {pname}"))
    # ──────────────────────────────────────────────────────────────────────────

    db.commit()
    return {"message":"Expense added","expense_id":eid}

# ── Delete expense ────────────────────────────────────────────────────────────
@router.delete("/api/expense/{eid}")
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
