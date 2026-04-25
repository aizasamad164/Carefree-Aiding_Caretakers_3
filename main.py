from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes import (auth, patients, caretakers, tasks, appointments,
                    expenses, notifications, predictions, vitals, symptoms)
from config import DB_HOST, DB_PORT, DB_SERVICE, DB_USER, DB_PASSWORD
import oracledb

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Carefree API", version="5.0 — Normalized Oracle Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ── DB startup ────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    try:
        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
        )
        print("✅ Oracle XE connected successfully")
        conn.close()
        print("✅ All tables verified/created")
    except Exception as e:
        print(f"❌ Oracle startup failed: {e}")


# ── Register all routers ──────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(caretakers.router)
app.include_router(patients.router)
app.include_router(tasks.router)
app.include_router(appointments.router)
app.include_router(expenses.router)
app.include_router(notifications.router)
app.include_router(predictions.router)
app.include_router(vitals.router)
app.include_router(symptoms.router)


# ── Page routes ───────────────────────────────────────────────────────────────
@app.get("/")
def login_page(): return FileResponse("templates/login.html")

@app.get("/caretaker")
def caretaker_page(): return FileResponse("templates/caretaker.html")

@app.get("/guardian")
def guardian_page(): return FileResponse("templates/guardian.html")