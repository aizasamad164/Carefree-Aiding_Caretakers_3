# ─────────────────────────────────────────────────────────────────────────────
#  config.example.py  —  TEMPLATE (copy this to config.py and fill in details)
# ─────────────────────────────────────────────────────────────────────────────

USE_CLOUD = False   # False = Local Oracle,  True = Oracle Cloud

# Local Oracle
DB_HOST     = "localhost"
DB_PORT     = 1521
DB_SERVICE  = "XEPDB1"
DB_USER     = "your_username"
DB_PASSWORD = "your_password"
DB_MODE     = "SERVICE_NAME"

# Oracle Cloud (set USE_CLOUD = True and fill these)
if USE_CLOUD:
    DB_HOST     = "adb.region.oraclecloud.com"
    DB_PORT     = 1522
    DB_SERVICE  = "your_db_high"
    DB_USER     = "admin"
    DB_PASSWORD = "your_cloud_password"
    DB_MODE     = "SERVICE_NAME"

# Wallet (Oracle Cloud only)
WALLET_DIR      = "D:\\carefree\\wallet"
WALLET_PASSWORD = ""