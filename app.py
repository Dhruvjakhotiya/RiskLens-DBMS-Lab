import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, url_for

from config import DATABASE_PATH, MODEL_DIR
from database.db import get_connection, init_db
from database.seed_data import seed
from ml.predict import explanations, load_model, predict
from services.assessment_service import create_assessment, get_assessment, history
from services.health_service import create_record, get_record, list_records
from services.patient_service import create_patient, get_patient, list_patients, update_patient
from time_utils import format_ist

app = Flask(__name__)
app.config["SECRET_KEY"] = "local-demo-key-change-before-deployment"
app.config["DATABASE"] = DATABASE_PATH
app.config["PLOTS_DIRECTORY"] = Path(__file__).resolve().parent / "static" / "plots"


LATEST_EVALUATIONS_SQL = """
    WITH ranked_evaluations AS (
        SELECT e.*, m.model_name, m.version,
               ROW_NUMBER() OVER (
                   PARTITION BY e.model_id, m.version
                   ORDER BY datetime(e.evaluated_at) DESC, e.evaluation_id DESC
               ) AS row_number
        FROM model_evaluations e
        JOIN ml_models m ON m.model_id = e.model_id
        WHERE trim(e.metrics_json) <> ''
          AND json_valid(e.metrics_json) = 1
    )
    SELECT * FROM ranked_evaluations
    WHERE row_number = 1
    ORDER BY model_name, version
"""


@app.template_filter("fromjson")
def fromjson(value):
    import json
    return json.loads(value)


@app.template_filter("ist_datetime")
def ist_datetime(value):
    return format_ist(value)


def evaluation_view_data(evaluations):
    plot_directory = Path(app.config["PLOTS_DIRECTORY"]).resolve()
    view_data = []
    for evaluation in evaluations:
        item = dict(evaluation)
        metrics = fromjson(item["metrics_json"])
        stored_plot = Path(item["plot_path"]) if item["plot_path"] else None
        filename = stored_plot.name if stored_plot else None
        candidate = (plot_directory / filename).resolve() if filename else None
        item["plot_available"] = bool(
            candidate
            and candidate.parent == plot_directory
            and candidate.is_file()
            and metrics.get("plot_path") == item["plot_path"]
        )
        item["plot_filename"] = filename
        item["plot_url"] = (
            url_for("evaluation_plot", filename=filename)
            if item["plot_available"]
            else None
        )
        view_data.append(item)
    return view_data


def validate_patient(form):
    required = ("demo_identifier", "full_name", "date_of_birth", "sex")
    if any(not form.get(field, "").strip() for field in required):
        return "All patient fields are required."
    try:
        birth_date = date.fromisoformat(form["date_of_birth"])
    except ValueError:
        return "Date of birth must be a valid date."
    if birth_date > date.today():
        return "Date of birth cannot be in the future."
    return None


def age_on(date_of_birth, on_date):
    birth_date = date.fromisoformat(date_of_birth)
    return on_date.year - birth_date.year - (
        (on_date.month, on_date.day) < (birth_date.month, birth_date.day)
    )


def prepare_records(patient, records):
    prepared = []
    for record in records:
        recorded_at = datetime.fromisoformat(record["recorded_at"]).date()
        item = dict(record)
        item["age_at_recorded"] = age_on(patient["date_of_birth"], recorded_at)
        item["age_consistent"] = item["age"] == item["age_at_recorded"]
        prepared.append(item)
    return prepared


def health_values(form):
    try:
        values = {
            "age": int(form["age"]),
            "bmi": float(form["bmi"]) if form.get("bmi") else None,
            "glucose": float(form["glucose"]) if form.get("glucose") else None,
            "blood_pressure": float(form["blood_pressure"]) if form.get("blood_pressure") else None,
            "physical_activity": form.get("physical_activity") or None,
            "smoking_status": form.get("smoking_status") or None,
        }
        if values["age"] < 18 or values["age"] > 120:
            raise ValueError
        return values
    except (KeyError, TypeError, ValueError):
        raise ValueError("Age must be 18-120 and numeric fields must contain valid numbers.")


@app.route("/")
def dashboard():
    init_db(app.config["DATABASE"])
    with get_connection(app.config["DATABASE"]) as db:
        stats = {
            "patients": db.execute("SELECT COUNT(*) FROM patients WHERE is_active=1").fetchone()[0],
            "records": db.execute("SELECT COUNT(*) FROM health_records").fetchone()[0],
            "assessments": db.execute("SELECT COUNT(*) FROM risk_assessments").fetchone()[0],
            "models": db.execute("SELECT COUNT(*) FROM ml_models WHERE is_active=1").fetchone()[0],
        }
        recent = db.execute("SELECT * FROM assessment_history ORDER BY datetime(assessed_at) DESC LIMIT 5").fetchall()
        evaluations = db.execute(LATEST_EVALUATIONS_SQL).fetchall()
    return render_template("dashboard.html", stats=stats, recent=recent, evaluations=evaluations)


@app.route("/patients")
def patients():
    return render_template("patients.html", patients=list_patients(app.config["DATABASE"]))


@app.route("/patients/new", methods=["GET", "POST"])
def new_patient():
    if request.method == "POST":
        error = validate_patient(request.form)
        if error:
            flash(error, "danger")
        else:
            try:
                create_patient(app.config["DATABASE"], request.form)
                flash("Patient registered.", "success")
                return redirect(url_for("patients"))
            except sqlite3.IntegrityError:
                flash("Demo identifier already exists or violates a database constraint.", "danger")
    return render_template("patient_form.html", patient=None)


@app.route("/patients/<int:patient_id>", methods=["GET", "POST"])
def patient_detail(patient_id):
    patient = get_patient(app.config["DATABASE"], patient_id)
    if not patient:
        return render_template("404.html"), 404
    if request.method == "POST":
        error = validate_patient(request.form)
        if error:
            flash(error, "danger")
        else:
            try:
                update_patient(app.config["DATABASE"], patient_id, request.form)
                flash("Patient updated.", "success")
                return redirect(url_for("patient_detail", patient_id=patient_id))
            except sqlite3.IntegrityError:
                flash("Update failed because the identifier is already in use.", "danger")
    return render_template(
        "patient_detail.html",
        patient=patient,
        current_age=age_on(patient["date_of_birth"], date.today()),
        records=prepare_records(patient, list_records(app.config["DATABASE"], patient_id)),
    )


@app.route("/patients/<int:patient_id>/health", methods=["GET", "POST"])
def new_health_record(patient_id):
    patient = get_patient(app.config["DATABASE"], patient_id)
    if not patient:
        return render_template("404.html"), 404
    if request.method == "POST":
        try:
            create_record(app.config["DATABASE"], patient_id, health_values(request.form))
            flash("Health record saved.", "success")
            return redirect(url_for("patient_detail", patient_id=patient_id))
        except (ValueError, sqlite3.IntegrityError) as error:
            flash(str(error), "danger")
    return render_template("health_form.html", patient=patient)


@app.route("/assess/<int:patient_id>/<int:record_id>", methods=["GET", "POST"])
def assess(patient_id, record_id):
    record = get_record(app.config["DATABASE"], record_id)
    patient = get_patient(app.config["DATABASE"], patient_id)
    if not record or not patient or record["patient_id"] != patient_id:
        return render_template("404.html"), 404
    if request.method == "POST":
        try:
            model = load_model(MODEL_DIR / "logistic_regression.pkl")
            values = {
                "age": record["age"], "bmi": record["bmi"], "glucose": record["glucose"],
                "blood_pressure": record["blood_pressure"], "activity_level": record["physical_activity"],
                "smoking": record["smoking_status"],
            }
            probability, category = predict(model, values)
            explanation = explanations(model, values)
            with get_connection(app.config["DATABASE"]) as db:
                disease = db.execute("SELECT disease_id FROM diseases WHERE disease_code='T2D'").fetchone()
                model_id = db.execute("SELECT model_id FROM ml_models WHERE model_name='Logistic Regression' ORDER BY model_id DESC LIMIT 1").fetchone()
            if not disease or not model_id:
                flash("Train and register a model before assessing risk.", "danger")
            else:
                assessment_id = create_assessment(app.config["DATABASE"], patient_id, record_id, disease[0], model_id[0], probability, category, explanation)
                return redirect(url_for("assessment_detail", assessment_id=assessment_id))
        except FileNotFoundError as error:
            flash(str(error), "danger")
    return render_template("assessment.html", patient=patient, record=record)


@app.route("/history")
def assessment_history():
    return render_template("history.html", assessments=history(app.config["DATABASE"]))


@app.route("/model-evaluation")
def model_evaluation():
    with get_connection(app.config["DATABASE"]) as db:
        evaluations = db.execute(LATEST_EVALUATIONS_SQL).fetchall()
    return render_template(
        "model_evaluation.html",
        evaluations=evaluation_view_data(evaluations),
    )


@app.route("/evaluation-plots/<path:filename>")
def evaluation_plot(filename):
    plot_directory = Path(app.config["PLOTS_DIRECTORY"]).resolve()
    requested = (plot_directory / filename).resolve()
    if requested.parent != plot_directory or not requested.is_file():
        abort(404)
    return send_from_directory(plot_directory, requested.name)


@app.route("/assessments/<int:assessment_id>")
def assessment_detail(assessment_id):
    assessment, explanations_ = get_assessment(app.config["DATABASE"], assessment_id)
    if not assessment:
        return render_template("404.html"), 404
    return render_template("assessment_detail.html", assessment=assessment, explanations=explanations_)


@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    seed()
    app.run(debug=True)
