import cx_Oracle as oracledb
from config import (DB_HOST, DB_PORT, DB_SERVICE, DB_USER, DB_PASSWORD,
                    DB_MODE, USE_CLOUD, WALLET_DIR, WALLET_PASSWORD)

def get_dsn():
    return f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"

def get_db():
    if USE_CLOUD and WALLET_DIR:
        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=get_dsn(),
            config_dir=WALLET_DIR,
            wallet_location=WALLET_DIR,
            wallet_password=WALLET_PASSWORD
        )
    else:
        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=get_dsn()
        )
    try:
        yield conn
    finally:
        conn.close()

def row_to_dict(cursor, row):
    return {cursor.description[i][0].lower(): row[i] for i in range(len(row))}

def rows_to_list(cursor, rows):
    return [row_to_dict(cursor, r) for r in rows]