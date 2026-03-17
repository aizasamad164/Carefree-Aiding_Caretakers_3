import cx_Oracle
from config import (DB_HOST, DB_PORT, DB_SERVICE, DB_USER, DB_PASSWORD,
                    DB_MODE, USE_CLOUD, WALLET_DIR, WALLET_PASSWORD)

# ── DSN builder ────────────────────────────────────────────────────────────────
def get_dsn():
    if DB_MODE == "SID":
        return cx_Oracle.makedsn(DB_HOST, DB_PORT, sid=DB_SERVICE)
    else:
        return cx_Oracle.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)

# ── Connection factory ─────────────────────────────────────────────────────────
def get_db():
    if USE_CLOUD and WALLET_DIR:
        # Oracle Cloud — uses wallet for secure connection
        cx_Oracle.init_oracle_client(config_dir=WALLET_DIR)
        if WALLET_PASSWORD:
            conn = cx_Oracle.connect(
                user=DB_USER, password=DB_PASSWORD, dsn=get_dsn(),
                wallet_location=WALLET_DIR, wallet_password=WALLET_PASSWORD
            )
        else:
            conn = cx_Oracle.connect(
                user=DB_USER, password=DB_PASSWORD, dsn=get_dsn(),
                wallet_location=WALLET_DIR
            )
    else:
        # Local Oracle — direct connection
        conn = cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=get_dsn())
    try:
        yield conn
    finally:
        conn.close()

# ── Row helpers ────────────────────────────────────────────────────────────────
def row_to_dict(cursor, row):
    """Convert a single Oracle row to a dictionary."""
    return {cursor.description[i][0].lower(): row[i] for i in range(len(row))}

def rows_to_list(cursor, rows):
    """Convert multiple Oracle rows to a list of dictionaries."""
    return [row_to_dict(cursor, r) for r in rows]
