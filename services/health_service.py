from database.db import transaction


def list_records(path, patient_id):
    with transaction(path) as db:
        return db.execute(
            "SELECT * FROM health_records WHERE patient_id = ? ORDER BY datetime(recorded_at) DESC", (patient_id,)
        ).fetchall()


def create_record(path, patient_id, data):
    with transaction(path) as db:
        cursor = db.execute(
            """INSERT INTO health_records
            (patient_id, age, bmi, glucose, blood_pressure, physical_activity, smoking_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (patient_id, data["age"], data["bmi"], data["glucose"], data["blood_pressure"],
             data["physical_activity"], data["smoking_status"]),
        )
        return cursor.lastrowid


def get_record(path, record_id):
    with transaction(path) as db:
        return db.execute("SELECT * FROM health_records WHERE health_record_id = ?", (record_id,)).fetchone()
