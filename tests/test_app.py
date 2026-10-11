from datetime import date, timedelta
import json

from app import app
from database.db import init_db
from database.db import get_connection


def test_dashboard_and_patient_creation(tmp_path):
    path = tmp_path / "app.db"
    app.config.update(TESTING=True, DATABASE=path)
    init_db(path)
    client = app.test_client()
    assert client.get("/").status_code == 200
    response = client.post("/patients/new", data={
        "demo_identifier": "WEB-1", "full_name": "Web User",
        "date_of_birth": "2000-01-01", "sex": "Female",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"WEB-1" in response.data


def test_patient_registration_rejects_future_date(tmp_path):
    path = tmp_path / "future.db"
    app.config.update(TESTING=True, DATABASE=path)
    init_db(path)
    client = app.test_client()
    future = (date.today() + timedelta(days=1)).isoformat()
    response = client.post("/patients/new", data={
        "demo_identifier": "FUTURE", "full_name": "Future User",
        "date_of_birth": future, "sex": "Female",
    })
    assert response.status_code == 200
    assert b"cannot be in the future" in response.data


def test_patient_update_rejects_future_date_and_accepts_valid_date(tmp_path):
    path = tmp_path / "update.db"
    app.config.update(TESTING=True, DATABASE=path)
    init_db(path)
    client = app.test_client()
    client.post("/patients/new", data={
        "demo_identifier": "UPDATE-1", "full_name": "Update User",
        "date_of_birth": "2000-01-01", "sex": "Female",
    })
    future = (date.today() + timedelta(days=1)).isoformat()
    response = client.post("/patients/1", data={
        "demo_identifier": "UPDATE-1", "full_name": "Update User",
        "date_of_birth": future, "sex": "Female",
    })
    assert response.status_code == 200
    assert b"cannot be in the future" in response.data
    response = client.post("/patients/1", data={
        "demo_identifier": "UPDATE-1", "full_name": "Updated User",
        "date_of_birth": "1999-01-01", "sex": "Female",
    })
    assert response.status_code == 302


def test_model_evaluation_shows_latest_once_per_model_version(tmp_path):
    path = tmp_path / "evaluation.db"
    app.config.update(TESTING=True, DATABASE=path)
    init_db(path)
    with get_connection(path) as db:
        db.execute("INSERT INTO diseases (disease_code, disease_name) VALUES ('T2D', 'Type-2 Diabetes')")
        disease_id = db.execute("SELECT disease_id FROM diseases WHERE disease_code = 'T2D'").fetchone()[0]
        for name in ("Logistic Regression", "Random Forest"):
            db.execute(
                """INSERT INTO ml_models
                (disease_id, model_name, version, artifact_path, trained_at)
                VALUES (?, ?, '1.0', ?, '2026-10-11T10:00:00+00:00')""",
                (disease_id, name, f"{name}.pkl"),
            )
            model_id = db.execute(
                "SELECT model_id FROM ml_models WHERE model_name = ?", (name,)
            ).fetchone()[0]
            for run, timestamp, accuracy in (("old", "2026-10-11T10:01:00+00:00", 0.1), ("latest", "2026-10-11T10:02:00+00:00", 0.9)):
                db.execute(
                    """INSERT INTO model_evaluations
                    (model_id, dataset_name, evaluated_at, metrics_json, plot_path)
                    VALUES (?, 'synthetic_demo_fallback', ?, ?, ?)""",
                    (model_id, timestamp, json.dumps({"accuracy": accuracy, "f1": 0.5, "roc_auc": 0.5, "brier_score": 0.2, "test_count": 10, "run": run}), f"{name}-{run}.png"),
                )
    response = app.test_client().get("/model-evaluation")
    assert response.status_code == 200
    assert response.data.count(b"Logistic Regression v1.0") == 1
    assert response.data.count(b"Random Forest v1.0") == 1
    assert b"0.900" in response.data
    assert b"0.100" not in response.data
    with get_connection(path) as db:
        assert db.execute("SELECT COUNT(*) FROM model_evaluations").fetchone()[0] == 4


def test_model_evaluation_serves_matching_plots_and_reports_missing_files(tmp_path):
    path = tmp_path / "evaluation-plots.db"
    plot_directory = tmp_path / "plots"
    plot_directory.mkdir()
    app.config.update(TESTING=True, DATABASE=path, PLOTS_DIRECTORY=plot_directory)
    init_db(path)
    with get_connection(path) as db:
        db.execute("INSERT INTO diseases (disease_code, disease_name) VALUES ('T2D', 'Type-2 Diabetes')")
        disease_id = db.execute("SELECT disease_id FROM diseases WHERE disease_code = 'T2D'").fetchone()[0]
        for name in ("Logistic Regression", "Random Forest"):
            db.execute(
                """INSERT INTO ml_models
                (disease_id, model_name, version, artifact_path, trained_at)
                VALUES (?, ?, '1.0', ?, '2026-10-11T10:00:00+00:00')""",
                (disease_id, name, f"{name}.pkl"),
            )
            model_id = db.execute(
                "SELECT model_id FROM ml_models WHERE model_name = ?", (name,)
            ).fetchone()[0]
            filename = f"{name.lower().replace(' ', '_')}_calibration_run.png"
            plot_path = str(plot_directory / filename)
            metrics = {
                "accuracy": 0.9, "f1": 0.8, "roc_auc": 0.7,
                "brier_score": 0.2, "test_count": 10,
                "evaluation_run_id": "run-1", "plot_path": plot_path,
            }
            (plot_directory / filename).write_bytes(b"plot")
            db.execute(
                """INSERT INTO model_evaluations
                (model_id, dataset_name, evaluated_at, metrics_json, plot_path)
                VALUES (?, 'synthetic_demo_fallback', '2026-10-11T10:02:00+00:00', ?, ?)""",
                (model_id, json.dumps(metrics), plot_path),
            )

    client = app.test_client()
    response = client.get("/model-evaluation")
    assert response.status_code == 200
    assert response.data.count(b"<img") == 2
    assert b"Mean predicted probability" in response.data
    assert client.get("/evaluation-plots/logistic_regression_calibration_run.png").status_code == 200
    assert client.get("/evaluation-plots/random_forest_calibration_run.png").status_code == 200

    (plot_directory / "random_forest_calibration_run.png").unlink()
    response = client.get("/model-evaluation")
    assert response.status_code == 200
    assert b"Calibration plot is unavailable" in response.data


def test_event_timestamps_are_displayed_in_ist_on_main_pages(tmp_path):
    path = tmp_path / "timestamps.db"
    app.config.update(TESTING=True, DATABASE=path)
    init_db(path)
    with get_connection(path) as db:
        db.execute(
            "INSERT INTO patients (demo_identifier, full_name, date_of_birth, sex, created_at) VALUES (?, ?, ?, ?, ?)",
            ("TIME-1", "Time User", "2000-01-01", "Female", "2026-10-11 10:00:00"),
        )
        patient_id = db.execute("SELECT patient_id FROM patients WHERE demo_identifier = 'TIME-1'").fetchone()[0]
        db.execute(
            """INSERT INTO health_records
            (patient_id, recorded_at, age, glucose)
            VALUES (?, '2026-10-11 10:06:00', 26, 120)""",
            (patient_id,),
        )
        record_id = db.execute("SELECT health_record_id FROM health_records WHERE patient_id = ?", (patient_id,)).fetchone()[0]
        db.execute("INSERT INTO diseases (disease_code, disease_name) VALUES ('T2D', 'Type-2 Diabetes')")
        disease_id = db.execute("SELECT disease_id FROM diseases WHERE disease_code = 'T2D'").fetchone()[0]
        db.execute(
            """INSERT INTO ml_models
            (disease_id, model_name, version, artifact_path, trained_at)
            VALUES (?, 'Logistic Regression', '1.0', 'model.pkl', '2026-10-11 10:00:00')""",
            (disease_id,),
        )
        model_id = db.execute("SELECT model_id FROM ml_models").fetchone()[0]
        db.execute(
            """INSERT INTO risk_assessments
            (patient_id, health_record_id, disease_id, model_id, risk_probability, risk_category, assessed_at)
            VALUES (?, ?, ?, ?, 0.5, 'Moderate', '2026-10-11 10:06:00')""",
            (patient_id, record_id, disease_id, model_id),
        )
    client = app.test_client()
    assert b"11 Oct 2026, 15:36:00 IST" in client.get("/").data
    assert b"11 Oct 2026, 15:36:00 IST" in client.get("/history").data
    assert b"11 Oct 2026, 15:36:00 IST" in client.get("/patients/1").data
