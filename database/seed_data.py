from database.db import init_db, transaction
from config import DATABASE_PATH


def seed(path=DATABASE_PATH):
    init_db(path)
    with transaction(path) as db:
        db.execute(
            "INSERT OR IGNORE INTO diseases (disease_code, disease_name) VALUES (?, ?)",
            ("T2D", "Type-2 Diabetes"),
        )
        patients = [
            ("DEMO-001", "Aarav Demo", "1999-04-12", "Male"),
            ("DEMO-002", "Maya Example", "1988-09-23", "Female"),
            ("DEMO-003", "Sam Sample", "1976-01-05", "Other"),
        ]
        for identifier, name, dob, sex in patients:
            db.execute(
                "INSERT OR IGNORE INTO patients (demo_identifier, full_name, date_of_birth, sex) VALUES (?, ?, ?, ?)",
                (identifier, name, dob, sex),
            )
        ids = {row["demo_identifier"]: row["patient_id"] for row in db.execute("SELECT patient_id, demo_identifier FROM patients")}
        for identifier, age, bmi, glucose, bp, activity, smoking in [
            ("DEMO-001", 26, 23.4, 94, 118, "High", "Never"),
            ("DEMO-002", 37, 29.1, 132, 138, "Moderate", "Former"),
            ("DEMO-003", 50, 31.8, 168, 145, "Low", "Current"),
        ]:
            if not db.execute("SELECT 1 FROM health_records WHERE patient_id = ?", (ids[identifier],)).fetchone():
                db.execute(
                    """INSERT INTO health_records
                    (patient_id, age, bmi, glucose, blood_pressure, physical_activity, smoking_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (ids[identifier], age, bmi, glucose, bp, activity, smoking),
                )
        # This correction is intentionally limited to the known synthetic demo row.
        # It never changes records with user-created identifiers.
        db.execute(
            """UPDATE patients SET date_of_birth = '2007-01-01'
            WHERE lower(demo_identifier) = 'demo-004'
            AND date_of_birth > date('now')"""
        )
        db.execute(
            """UPDATE health_records SET age = 19
            WHERE patient_id IN (
                SELECT patient_id FROM patients
                WHERE lower(demo_identifier) = 'demo-004'
            ) AND age = 19"""
        )
        # Keep the bundled synthetic records internally consistent with their DOBs.
        for identifier, age in (("DEMO-001", 27), ("DEMO-002", 38), ("DEMO-003", 50)):
            db.execute(
                """UPDATE health_records SET age = ?
                WHERE patient_id = (
                    SELECT patient_id FROM patients WHERE demo_identifier = ?
                ) AND recorded_at = (
                    SELECT MIN(recorded_at) FROM health_records
                    WHERE patient_id = (
                        SELECT patient_id FROM patients WHERE demo_identifier = ?
                    )
                )""",
                (age, identifier, identifier),
            )


if __name__ == "__main__":
    seed()
    print(f"Seeded demonstration database at {DATABASE_PATH}")
