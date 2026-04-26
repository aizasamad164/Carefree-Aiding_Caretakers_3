# ─────────────────────────────────────────────────────────────────────────────
#  config.py  —  Carefree Database Connection Settings
#
#  TWO MODES:
#  1. Local Oracle  → set USE_CLOUD = False
#  2. Oracle Cloud  → set USE_CLOUD = True  and fill wallet details
#
#  Only edit this file. Never touch any other file.
# ─────────────────────────────────────────────────────────────────────────────

# ── Switch between Local and Cloud ───────────────────────────────────────────
USE_CLOUD = False   # False = Local Oracle,  True = Oracle Cloud

# ─────────────────────────────────────────────────────────────────────────────
#  LOCAL ORACLE SETTINGS  (used when USE_CLOUD = False)
# ─────────────────────────────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_PORT     = 1521
DB_SERVICE  = "xepdb1"
DB_USER     = "system"
DB_PASSWORD = "carefree123"
DB_MODE     = "SERVICE_NAME"

USE_CLOUD       = False
WALLET_DIR      = None
WALLET_PASSWORD = None

# ─────────────────────────────────────────────────────────────────────────────
#  ORACLE CLOUD SETTINGS  (used when USE_CLOUD = True)
#  1. Login to cloud.oracle.com
#  2. Go to Autonomous Database → DB Connection
#  3. Download Wallet zip → extract to D:\carefree\wallet\
#  4. Open wallet\tnsnames.ora to find host and service_name
#  5. Fill in below and set USE_CLOUD = True
# ─────────────────────────────────────────────────────────────────────────────
if USE_CLOUD:
    DB_HOST     = "adb.ap-mumbai-1.oraclecloud.com"
    DB_PORT     = 1522
    DB_SERVICE  = "your_db_high"
    DB_USER     = "admin"
    DB_PASSWORD = "YourCloudPassword123"
    DB_MODE     = "SERVICE_NAME"

# ── Wallet (Oracle Cloud only) ────────────────────────────────────────────────
WALLET_DIR      = "D:\\carefree\\wallet"
WALLET_PASSWORD = ""