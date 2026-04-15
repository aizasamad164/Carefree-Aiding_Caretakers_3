from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import DietaryPlanCreate, DietaryPlanUpdate

router = APIRouter()

# ── Create tables if not exist ────────────────────────────────────────────────
def create_dietary_plan_tables(db):
    cur = db.cursor()

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE DietaryPlan (
                    PlanID      VARCHAR2(20)    PRIMARY KEY,
                    Duration    VARCHAR2(50),
                    PatientID   VARCHAR2(20)    REFERENCES Patient(PatientID)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE DietaryGoal (
                    PlanID      VARCHAR2(20)    REFERENCES DietaryPlan(PlanID),
                    Goal        VARCHAR2(100)   NOT NULL,
                    CONSTRAINT pk_dietary_goal PRIMARY KEY (PlanID, Goal)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    cur.execute("""
        BEGIN
            EXECUTE IMMEDIATE '
                CREATE TABLE DietaryRestriction (
                    PlanID          VARCHAR2(20)    REFERENCES DietaryPlan(PlanID),
                    Restriction     VARCHAR2(100)   NOT NULL,
                    CONSTRAINT pk_dietary_restriction PRIMARY KEY (PlanID, Restriction)
                )
            ';
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE != -955 THEN RAISE; END IF;
        END;
    """)

    db.commit()
    cur.close()


# ── Get all dietary plans for a patient ───────────────────────────────────────
@router.get("/api/dietary-plans/{pid}")
def get_plans(pid: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT PlanID, Duration, PatientID
        FROM   DietaryPlan
        WHERE  PatientID = :1
        ORDER BY PlanID
    """, (pid,))
    rows = cur.fetchall()
    keys = ["plan_id", "duration", "patient_id"]
    result = []
    for r in rows:
        plan = {keys[i]: r[i] for i in range(len(keys))}

        # Fetch goals list
        cur.execute("SELECT Goal FROM DietaryGoal WHERE PlanID=:1", (r[0],))
        plan["goals"] = [row[0] for row in cur.fetchall()]

        # Fetch restrictions list
        cur.execute("SELECT Restriction FROM DietaryRestriction WHERE PlanID=:1", (r[0],))
        plan["restrictions"] = [row[0] for row in cur.fetchall()]

        result.append(plan)
    return result


# ── Get single dietary plan ───────────────────────────────────────────────────
@router.get("/api/dietary-plan/{plan_id}")
def get_plan(plan_id: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT PlanID, Duration, PatientID FROM DietaryPlan WHERE PlanID=:1",
                (plan_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Dietary plan not found")

    plan = {"plan_id": row[0], "duration": row[1], "patient_id": row[2]}

    cur.execute("SELECT Goal FROM DietaryGoal WHERE PlanID=:1", (plan_id,))
    plan["goals"] = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT Restriction FROM DietaryRestriction WHERE PlanID=:1", (plan_id,))
    plan["restrictions"] = [r[0] for r in cur.fetchall()]

    return plan


# ── Create dietary plan ───────────────────────────────────────────────────────
@router.post("/api/dietary-plan")
def create_plan(p: DietaryPlanCreate, db=Depends(get_db)):
    cur = db.cursor()
    import random
    plan_id = f"DP-{random.randint(10000,99999)}"

    cur.execute("""
        INSERT INTO DietaryPlan (PlanID, Duration, PatientID)
        VALUES (:1,:2,:3)
    """, (plan_id, p.duration, p.patient_id))

    # Insert goals — one row per goal (1NF)
    for goal in p.goals:
        cur.execute("INSERT INTO DietaryGoal (PlanID, Goal) VALUES (:1,:2)",
                    (plan_id, goal.strip()))

    # Insert restrictions — one row per restriction (1NF)
    for restriction in p.restrictions:
        cur.execute("INSERT INTO DietaryRestriction (PlanID, Restriction) VALUES (:1,:2)",
                    (plan_id, restriction.strip()))

    db.commit()
    return {"message": "Dietary plan created", "plan_id": plan_id}


# ── Update dietary plan ───────────────────────────────────────────────────────
@router.put("/api/dietary-plan/{plan_id}")
def update_plan(plan_id: str, p: DietaryPlanUpdate, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM DietaryPlan WHERE PlanID=:1", (plan_id,))
    if cur.fetchone()[0] == 0:
        raise HTTPException(404, "Dietary plan not found")

    cur.execute("UPDATE DietaryPlan SET Duration=:1 WHERE PlanID=:2",
                (p.duration, plan_id))

    # Replace goals
    if p.goals is not None:
        cur.execute("DELETE FROM DietaryGoal WHERE PlanID=:1", (plan_id,))
        for goal in p.goals:
            cur.execute("INSERT INTO DietaryGoal (PlanID, Goal) VALUES (:1,:2)",
                        (plan_id, goal.strip()))

    # Replace restrictions
    if p.restrictions is not None:
        cur.execute("DELETE FROM DietaryRestriction WHERE PlanID=:1", (plan_id,))
        for restriction in p.restrictions:
            cur.execute("INSERT INTO DietaryRestriction (PlanID, Restriction) VALUES (:1,:2)",
                        (plan_id, restriction.strip()))

    db.commit()
    return {"message": "Dietary plan updated"}


# ── Delete dietary plan ───────────────────────────────────────────────────────
@router.delete("/api/dietary-plan/{plan_id}")
def delete_plan(plan_id: str, db=Depends(get_db)):
    cur = db.cursor()

    # Delete in FK-safe order
    cur.execute("DELETE FROM DietaryRestriction WHERE PlanID=:1", (plan_id,))
    cur.execute("DELETE FROM DietaryGoal         WHERE PlanID=:1", (plan_id,))
    # Meals and their children are handled by meal.py cascade
    cur.execute("""
        DELETE FROM MealIngredient WHERE MealID IN
        (SELECT MealID FROM Meal WHERE PlanID=:1)
    """, (plan_id,))
    cur.execute("""
        DELETE FROM MealNutrition WHERE MealID IN
        (SELECT MealID FROM Meal WHERE PlanID=:1)
    """, (plan_id,))
    cur.execute("DELETE FROM Meal         WHERE PlanID=:1", (plan_id,))
    cur.execute("DELETE FROM DietaryPlan  WHERE PlanID=:1", (plan_id,))

    db.commit()
    return {"message": "Dietary plan deleted"}
