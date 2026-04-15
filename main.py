from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes import (auth, patients, caretaker, tasks, appointments,
                    expenses, notifications, predictions,
                    vitals, dietaryplan, meal)
from database import get_db
from routes.caretaker import create_caretaker_tables
from routes.patients import create_tables
from routes.tasks import create_task_table
from routes.appointments import create_appointment_tables
from routes.expenses import create_expense_table
from routes.vitals import create_vitals_tables
from routes.dietaryplan import create_dietary_plan_tables
from routes.meal import create_meal_tables
from routes.notifications import create_notification_table
from config import DB_HOST, DB_PORT, DB_SERVICE, DB_USER, DB_PASSWORD
import cx_Oracle

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Carefree API", version="5.0 — Normalized Oracle Edition")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── DB startup — connect + create all tables ──────────────────────────────────
@app.on_event("startup")
async def startup():
    try:
        conn = cx_Oracle.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
        )
        print("✅ Oracle XE connected successfully")

        # Create tables in FK-safe order
        # (parent tables must exist before child tables that reference them)
        create_caretaker_tables(conn)   # Caretaker, CaretakerSkill
        create_tables(conn)             # Patient, Guardian
        create_task_table(conn)         # Task (FK → Patient, Caretaker)
        create_appointment_tables(conn) # Doctor, Appointment
        create_expense_table(conn)      # Expense
        create_vitals_tables(conn)      # Vitals, Cardiac, Respiratory, OtherVitals
        create_dietary_plan_tables(conn)# DietaryPlan, DietaryGoal, DietaryRestriction
        create_meal_tables(conn)        # Meal, MealIngredient, MealNutrition
        create_notification_table(conn) # Notification (FK → Caretaker, Task, Appointment)

        conn.close()
        print("✅ All tables verified/created")

    except Exception as e:
        print(f"❌ Oracle startup failed: {e}")

# ── Register all routers ──────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(caretaker.router)
app.include_router(patients.router)
app.include_router(tasks.router)
app.include_router(appointments.router)
app.include_router(expenses.router)
app.include_router(notifications.router)
app.include_router(predictions.router)
app.include_router(vitals.router)
app.include_router(dietaryplan.router)
app.include_router(meal.router)

# ── Page routes ───────────────────────────────────────────────────────────────
@app.get("/")
def login_page(): return FileResponse("templates/login.html")

@app.get("/caretaker")
def caretaker_page(): return FileResponse("templates/caretaker.html")

@app.get("/guardian")
def guardian_page(): return FileResponse("templates/guardian.html")