# ─────────────────────────────────────────────────────────────────────────────
#  config.py  —  Carefree Oracle Connection Settings
#  Edit ONLY this file to match your Oracle installation.
#  Do NOT change app.py.
# ─────────────────────────────────────────────────────────────────────────────

# Oracle server address
# If Oracle is on THIS computer → keep "localhost"
# If Oracle is on another PC    → put that PC's IP e.g. "192.168.1.5"
DB_HOST = "localhost"

# Oracle port — default is always 1521
DB_PORT = 1521

# Your Oracle SID or Service Name
# Oracle XE (Express Edition) → "XE"
# Oracle 19c/21c              → "XEPDB1" or your service name
DB_SERVICE = "XE"

# Oracle username and password
# Default Oracle XE credentials are usually system/your_password
DB_USER     = "system"
DB_PASSWORD = "carefree123"

# Connection mode
# "SID"          → older Oracle (XE 11g, 12c)
# "SERVICE_NAME" → newer Oracle (19c, 21c)
DB_MODE = "SID"
