import sqlite3
import os

DATABASE_PATH = "database/onnuri.db"

def get_connection():
    os.makedirs("database", exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def start_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] == 1

if __name__ == "__main__":
    if start_db():
        print("connection successful")
    else:
        print("connection failed")