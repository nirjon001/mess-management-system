import mysql.connector
from config import DB_HOST, DB_USER, DB_PASS, DB_NAME

def get_connection():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )
    return conn

def query(sql, params=None, fetch=True):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        conn.commit()
        return {'insert_id': cursor.lastrowid, 'affected': cursor.rowcount}
    finally:
        cursor.close()
        conn.close()

def query_row(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None
