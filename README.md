# Carefree — Oracle Edition

## Files
```
carefree/
├── app.py                               ← Backend (never needs editing)
├── config.py                            ← YOUR Oracle settings (edit this)
├── requirements.txt
├── Sleep_health_and_lifestyle_dataset.csv
├── insurance.csv
├── static/
└── templates/
    ├── login.html
    ├── caretaker.html
    └── guardian.html
```

## Step 1 — Edit config.py
Open config.py and fill in your Oracle details:
```python
DB_HOST     = "localhost"    # or IP address of Oracle server
DB_PORT     = 1521
DB_SERVICE  = "XE"           # your SID or service name
DB_USER     = "system"       # your Oracle username
DB_PASSWORD = "yourpassword" # your Oracle password
DB_MODE     = "SID"          # "SID" or "SERVICE_NAME"
```

## Step 2 — Install Oracle Instant Client
cx_Oracle needs Oracle Instant Client installed.
Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html
Choose the version matching your Oracle DB.

## Step 3 — Install Python dependencies
```cmd
cd D:\carefree
C:\Users\Dr.C\AppData\Local\Programs\Python\Python39\python.exe -m pip install -r requirements.txt
```

## Step 4 — Run
```cmd
C:\Users\Dr.C\AppData\Local\Programs\Python\Python39\python.exe -m uvicorn app:app --reload
```

## Step 5 — Open browser
```
http://localhost:8000
```

## Default Login
- Username: admin
- Password: admin123
- Role: Caretaker

## Oracle Tables Created Automatically
- Caretaker
- Patient
- Task
- Appointment
- Expenses

## On Another Desktop
Only change config.py with that computer's Oracle connection details.
Everything else stays the same.

## API Docs
```
http://localhost:8000/docs
```
