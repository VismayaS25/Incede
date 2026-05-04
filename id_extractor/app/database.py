import sqlite3

DB_NAME = "data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_type TEXT,
            name TEXT,
            father_name TEXT,
            dob TEXT,
            id_number TEXT,
            gender TEXT,
            address TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_record(doc_type, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    id_number = data.get("aadhaar_number") or data.get("pan_number")

    cursor.execute("""
        INSERT INTO records 
        (document_type, name, father_name, dob, id_number, gender, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_type,
        data.get("name"),
        data.get("father_name"),
        data.get("dob"),
        id_number,
        data.get("gender"),
        data.get("address")
    ))

    conn.commit()
    conn.close()