from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import MealCreate, MealUpdate

router = APIRouter()


# ── Create tables if not exist ────────────────────────────────────────────────
#def create_meal_tables(db):
#    cur = db.cursor()

#    cur.execute("""
#        BEGIN
#            EXECUTE IMMEDIATE '
#                CREATE TABLE Meal (
#                    MealID      VARCHAR2(20)    PRIMARY KEY,
#                    Name        VARCHAR2(100)   NOT NULL,
#                    Flag        VARCHAR2(20)    DEFAULT ''OK'',
#                    PlanID      VARCHAR2(20)    REFERENCES DietaryPlan(PlanID)
#                )
#            ';
#        EXCEPTION WHEN OTHERS THEN
#            IF SQLCODE != -955 THEN RAISE; END IF;
#        END;
#    """)

#    cur.execute("""
#        BEGIN
#            EXECUTE IMMEDIATE '
#                CREATE TABLE MealIngredient (
#                    MealID      VARCHAR2(20)    REFERENCES Meal(MealID),
#                    Ingredient  VARCHAR2(100)   NOT NULL,
#                    CONSTRAINT pk_meal_ingredient PRIMARY KEY (MealID, Ingredient)
#                )
#            ';
#        EXCEPTION WHEN OTHERS THEN
#            IF SQLCODE != -955 THEN RAISE; END IF;
#        END;
#    """)

#    cur.execute("""
#        BEGIN
#            EXECUTE IMMEDIATE '
#                CREATE TABLE MealNutrition (
#                    MealID      VARCHAR2(20)    REFERENCES Meal(MealID),
#                    Nutrient    VARCHAR2(50)    NOT NULL,
#                    Value       NUMBER(8,2),
#                    CONSTRAINT pk_meal_nutrition PRIMARY KEY (MealID, Nutrient)
#                )
#            ';
#        EXCEPTION WHEN OTHERS THEN
#            IF SQLCODE != -955 THEN RAISE; END IF;
#        END;
#    """)

#    db.commit()
#    cur.close()
#"""


# ── Get all meals for a plan ──────────────────────────────────────────────────
@router.get("/api/meals/{plan_id}")
def get_meals(plan_id: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT MealID, Name, Flag, PlanID
        FROM   Meal WHERE PlanID=:1
        ORDER BY MealID
    """, (plan_id,))
    rows = cur.fetchall()
    keys = ["meal_id", "name", "flag", "plan_id"]
    result = []
    for r in rows:
        meal = {keys[i]: r[i] for i in range(len(keys))}

        cur.execute("SELECT Ingredient FROM MealIngredient WHERE MealID=:1", (r[0],))
        meal["ingredients"] = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT Nutrient, Value FROM MealNutrition WHERE MealID=:1", (r[0],))
        meal["nutrition"] = {row[0]: row[1] for row in cur.fetchall()}

        result.append(meal)
    return result


# ── Get single meal ───────────────────────────────────────────────────────────
@router.get("/api/meal/{meal_id}")
def get_meal(meal_id: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT MealID, Name, Flag, PlanID FROM Meal WHERE MealID=:1",
                (meal_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Meal not found")

    meal = {"meal_id": row[0], "name": row[1], "flag": row[2], "plan_id": row[3]}

    cur.execute("SELECT Ingredient FROM MealIngredient WHERE MealID=:1", (meal_id,))
    meal["ingredients"] = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT Nutrient, Value FROM MealNutrition WHERE MealID=:1", (meal_id,))
    meal["nutrition"] = {r[0]: r[1] for r in cur.fetchall()}

    return meal


# ── Create meal ───────────────────────────────────────────────────────────────
@router.post("/api/meal")
def create_meal(m: MealCreate, db=Depends(get_db)):
    cur = db.cursor()
    import random
    meal_id = f"M-{random.randint(10000,99999)}"

    cur.execute("""
        INSERT INTO Meal (MealID, Name, Flag, PlanID)
        VALUES (:1,:2,:3,:4)
    """, (meal_id, m.name, m.flag or "OK", m.plan_id))

    # Insert ingredients — one row per ingredient (1NF)
    for ingredient in m.ingredients:
        cur.execute("INSERT INTO MealIngredient (MealID, Ingredient) VALUES (:1,:2)",
                    (meal_id, ingredient.strip()))

    # Insert nutrition — one row per nutrient (1NF)
    for nutrient, value in m.nutrition.items():
        cur.execute("INSERT INTO MealNutrition (MealID, Nutrient, Value) VALUES (:1,:2,:3)",
                    (meal_id, nutrient.strip(), value))

    db.commit()
    return {"message": "Meal created", "meal_id": meal_id}


# ── Update meal ───────────────────────────────────────────────────────────────
@router.put("/api/meal/{meal_id}")
def update_meal(meal_id: str, m: MealUpdate, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM Meal WHERE MealID=:1", (meal_id,))
    if cur.fetchone()[0] == 0:
        raise HTTPException(404, "Meal not found")

    cur.execute("UPDATE Meal SET Name=:1, Flag=:2 WHERE MealID=:3",
                (m.name, m.flag, meal_id))

    # Replace ingredients
    if m.ingredients is not None:
        cur.execute("DELETE FROM MealIngredient WHERE MealID=:1", (meal_id,))
        for ingredient in m.ingredients:
            cur.execute("INSERT INTO MealIngredient (MealID, Ingredient) VALUES (:1,:2)",
                        (meal_id, ingredient.strip()))

    # Replace nutrition
    if m.nutrition is not None:
        cur.execute("DELETE FROM MealNutrition WHERE MealID=:1", (meal_id,))
        for nutrient, value in m.nutrition.items():
            cur.execute("INSERT INTO MealNutrition (MealID, Nutrient, Value) VALUES (:1,:2,:3)",
                        (meal_id, nutrient.strip(), value))

    db.commit()
    return {"message": "Meal updated"}


# ── Delete meal ───────────────────────────────────────────────────────────────
@router.delete("/api/meal/{meal_id}")
def delete_meal(meal_id: str, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM Meal WHERE MealID=:1", (meal_id,))
    if cur.fetchone()[0] == 0:
        raise HTTPException(404, "Meal not found")

    # Delete children first, then meal
    cur.execute("DELETE FROM MealNutrition  WHERE MealID=:1", (meal_id,))
    cur.execute("DELETE FROM MealIngredient WHERE MealID=:1", (meal_id,))
    cur.execute("DELETE FROM Meal           WHERE MealID=:1", (meal_id,))

    db.commit()
    return {"message": "Meal deleted"}
