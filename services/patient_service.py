from database.db import transaction


def list_patients(path):
    with transaction(path) as db:
        return db.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY demo_identifier").fetchall()


def get_patient(path, patient_id):
    with transaction(path) as db:
        return db.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()


def create_patient(path, data):
    with transaction(path) as db:
        cursor = db.execute(
            "INSERT INTO patients (demo_identifier, full_name, date_of_birth, sex) VALUES (?, ?, ?, ?)",
            (data["demo_identifier"], data["full_name"], data["date_of_birth"], data["sex"]),
        )
        return cursor.lastrowid


def update_patient(path, patient_id, data):
    with transaction(path) as db:
        db.execute(
            "UPDATE patients SET demo_identifier = ?, full_name = ?, date_of_birth = ?, sex = ? WHERE patient_id = ?",
            (data["demo_identifier"], data["full_name"], data["date_of_birth"], data["sex"], patient_id),
        )
