import sqlite3

import pytest

from database.db import get_connection
from services.health_service import create_record
from services.patient_service import create_patient


def test_foreign_keys_and_duplicate_identifier(db_path):
    with get_connection(db_path) as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    create_patient(db_path, {"demo_identifier": "X", "full_name": "Test User", "date_of_birth": "2000-01-01", "sex": "Female"})
    with pytest.raises(sqlite3.IntegrityError):
        create_patient(db_path, {"demo_identifier": "X", "full_name": "Another", "date_of_birth": "2000-01-01", "sex": "Male"})
    with pytest.raises(sqlite3.IntegrityError):
        create_record(db_path, 999, {"age": 20, "bmi": None, "glucose": None, "blood_pressure": None, "physical_activity": None, "smoking_status": None})


def test_parameterized_sql_resists_injection(db_path):
    create_patient(db_path, {"demo_identifier": "SAFE", "full_name": "Normal", "date_of_birth": "2000-01-01", "sex": "Female"})
    with get_connection(db_path) as db:
        row = db.execute("SELECT * FROM patients WHERE demo_identifier = ?", ("' OR 1=1 --",)).fetchone()
        assert row is None
