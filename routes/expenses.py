import random
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import ExpCreate
from datetime import datetime
from routes.notifications import send_notification

router = APIRouter()

# ── Create Expense table if not exists ───────────────────────────────────────
def create_expense_table(db):
    cur = db.cursor()
    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE Expense (
                    ExpenseID           VARCHAR2(20)    PRIMARY KEY,
                    Expense_Name        VARCHAR2(100)   NOT NULL,
                    Expense_Category    VARCHAR2(50),
                    Expense_Amount      NUMBER(10,2)    NOT NULL,
                    Expense_Time        TIMESTAMP,
                    PatientID           VARCHAR2(20)    REFERENCES Patient(PatientID)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)
    db.commit()
    cur.close()

# ── Get expenses for a patient ────────────────────────────────────────────────
@router.get("/api/expenses/{pid}")
def get_expenses(pid: str, db=Depends(get_db)):
    cur = db.cursor()
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
    
    # Clean way to handle datetime for ALL rows
    result = []
    for r in rows:
        d = {keys[i]: r[i] for i in range(len(keys))}
        # Check if the database value is a datetime object and convert to string
        if isinstance(d["expense_time"], datetime):
            d["expense_time"] = d["expense_time"].strftime("%Y-%m-%d %H:%M")
        result.append(d)
        
    return result

# ── Create expense ────────────────────────────────────────────────────────────
# ── Create expense ────────────────────────────────────────────────────────────
@router.post("/api/expense")
def create_expense(e: ExpCreate, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT CaretakerID, Patient_Name FROM Patient WHERE PatientID=:1",
                (e.patient_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Patient not found")
    cid, pname = row[0], row[1]

    eid = f"E-{random.randint(1,99999)}"
    now = datetime.now().isoformat()

    # 1. Fixed Expense Insert
    cur.execute("""
        INSERT INTO Expense (ExpenseID, Expense_Name, Expense_Category,
                             Expense_Amount, Expense_Time, PatientID)
        VALUES (:1,:2,:3,:4,TO_TIMESTAMP(:5, 'YYYY-MM-DD"T"HH24:MI:SS.FF'),:6)
    """, (eid, e.name, e.category, e.amount, now, e.patient_id))

    # 2. Update total charges
    cur.execute("""
        UPDATE Patient SET Charges=(
            SELECT NVL(SUM(Expense_Amount),0) FROM Expense WHERE PatientID=:1)
        WHERE PatientID=:2
    """, (e.patient_id, e.patient_id))

    # 3. Fixed Auto-Notification using the SHARED HELPER
    # This automatically handles the Notification table's logic and time format
    send_notification(
        db, 
        caretaker_id=cid, 
        name=f"New Expense: {e.name}", 
        description=f"Rs. {e.amount} added for {pname}"
    )

    db.commit()
    return {"message": "Expense added", "expense_id": eid}

# ── Delete expense ────────────────────────────────────────────────────────────
@router.delete("/api/expense/{eid}")
def delete_expense(eid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT PatientID FROM Expense WHERE ExpenseID=:1", (eid,))
    row = cur.fetchone()
    if row:
        pid = row[0]
        cur.execute("DELETE FROM Expense WHERE ExpenseID=:1", (eid,))
        cur.execute("""
            UPDATE Patient SET Charges=(
                SELECT NVL(SUM(Expense_Amount),0) FROM Expense WHERE PatientID=:1)
            WHERE PatientID=:2
        """, (pid, pid))
        db.commit()
    return {"message": "Expense deleted"}