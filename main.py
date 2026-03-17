from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routes import auth, patients, tasks, appointments, expenses, notifications, predictions

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Carefree API", version="4.0 — Modular Oracle Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Register all route modules ─────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(tasks.router)
app.include_router(appointments.router)
app.include_router(expenses.router)
app.include_router(notifications.router)
app.include_router(predictions.router)

# ── Page routes ────────────────────────────────────────────────────────────────
@app.get("/")
def login_page(): return FileResponse("templates/login.html")

@app.get("/caretaker")
def caretaker_page(): return FileResponse("templates/caretaker.html")

@app.get("/guardian")
def guardian_page(): return FileResponse("templates/guardian.html")
