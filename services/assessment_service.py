import json

from database.db import transaction


def create_assessment(path, patient_id, record_id, disease_id, model_id, probability, category, explanations):
    with transaction(path) as db:
        cursor = db.execute(
            """INSERT INTO risk_assessments
            (patient_id, health_record_id, disease_id, model_id, risk_probability, risk_category)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (patient_id, record_id, disease_id, model_id, probability, category),
        )
        assessment_id = cursor.lastrowid
        db.executemany(
            """INSERT INTO prediction_explanations
            (assessment_id, feature_name, feature_value, contribution, explanation_type)
            VALUES (?, ?, ?, ?, 'local')""",
            [(assessment_id, name, str(value), contribution) for name, value, contribution in explanations],
        )
        return assessment_id


def history(path, patient_id=None, disease_id=None):
    query = "SELECT * FROM assessment_history WHERE 1=1"
    params = []
    if patient_id:
        query += " AND assessment_id IN (SELECT assessment_id FROM risk_assessments WHERE patient_id = ?)"
        params.append(patient_id)
    if disease_id:
        query += " AND disease_name = (SELECT disease_name FROM diseases WHERE disease_id = ?)"
        params.append(disease_id)
    query += " ORDER BY datetime(assessed_at) DESC"
    with transaction(path) as db:
        return db.execute(query, params).fetchall()


def get_assessment(path, assessment_id):
    with transaction(path) as db:
        assessment = db.execute("SELECT * FROM assessment_history WHERE assessment_id = ?", (assessment_id,)).fetchone()
        explanations = db.execute(
            "SELECT * FROM prediction_explanations WHERE assessment_id = ? ORDER BY ABS(contribution) DESC",
            (assessment_id,),
        ).fetchall()
        return assessment, explanations
