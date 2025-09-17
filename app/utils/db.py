# app/utils/db.py
import mysql.connector
from flask import current_app

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=current_app.config['DB_HOST'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            database=current_app.config['DB_NAME']
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, args)
    rv = cursor.fetchall()
    cursor.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), fetch_lastrowid=False):
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, args)
        conn.commit()
        if fetch_lastrowid:
            return cursor.lastrowid
        return True
    except mysql.connector.Error as err:
        print(f"Database execution error: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()