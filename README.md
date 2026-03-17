# Carefree — Modular Oracle Edition

## Folder Structure
```
carefree/
├── main.py                              ← starts the app
├── config.py                            ← YOUR settings (only file to edit)
├── database.py                          ← Oracle connection
├── models.py                            ← all data schemas
├── ml_models.py                         ← stress + cost ML
├── requirements.txt
├── config.example.py                    ← safe template for GitHub
├── Sleep_health_and_lifestyle_dataset.csv
├── insurance.csv
├── static/
├── templates/
│   ├── login.html
│   ├── caretaker.html
│   └── guardian.html
└── routes/
    ├── __init__.py
    ├── auth.py                          ← login, signup
    ├── patients.py                      ← patient CRUD
    ├── tasks.py                         ← task CRUD
    ├── appointments.py                  ← appointment CRUD
    ├── expenses.py                      ← expense CRUD
    ├── notifications.py                 ← notification CRUD
    └── predictions.py                   ← ML predictions
```

## Setup

### Step 1 — Edit config.py
```python
USE_CLOUD   = False         # True for Oracle Cloud
DB_HOST     = "localhost"
DB_PORT     = 1521
DB_SERVICE  = "XEPDB1"
DB_USER     = "carefree"
DB_PASSWORD = "carefree123"
DB_MODE     = "SERVICE_NAME"
```

### Step 2 — Create Oracle tables manually
Run your SQL scripts in SQLPlus before starting the app.

### Step 3 — Install dependencies
```cmd
cd D:\carefree
C:\Users\Dr.C\AppData\Local\Programs\Python\Python39\python.exe -m pip install -r requirements.txt
```

### Step 4 — Run
```cmd
C:\Users\Dr.C\AppData\Local\Programs\Python\Python39\python.exe -m uvicorn main:app --reload
```
Note: command is now `main:app` not `app:app`

## URLs
| URL | Page |
|-----|------|
| http://localhost:8000 | Login |
| http://localhost:8000/caretaker | Caretaker Dashboard |
| http://localhost:8000/guardian | Guardian Portal |
| http://localhost:8000/docs | API Docs |

## Adding a new feature
1. Add schema to `models.py`
2. Create `routes/yourfeature.py`
3. Register in `main.py`: `app.include_router(yourfeature.router)`
4. Done!
