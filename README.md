# RiskLens: Reliability-aware diabetes risk prototype

RiskLens is a Flask + SQLite DBMS laboratory project for demonstrating patient/demo data management, historical risk assessments, explainability, calibration, and missing-data-aware machine learning. It is an educational research prototype, not a medical diagnosis system.

## Quick start (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m database.seed_data
python -m ml.train_model
python -m ml.evaluate
python app.py
```

Open `http://127.0.0.1:5000`. Run tests with `pytest -q`.

If a local CSV is supplied to `load_dataset`, it must contain `age,bmi,glucose,blood_pressure,activity_level,smoking,target`. Without one, the training command uses a reproducible synthetic demonstration fallback and labels its source in metadata; it is not clinical evidence.

## Features and routes

Dashboard `/`, patient list `/patients`, patient registration `/patients/new`, health record entry `/patients/<id>/health`, assessment `/assess/<patient_id>/<record_id>`, history `/history`, and assessment detail `/assessments/<id>`.

The schema uses foreign keys, checks, unique identifiers, indexes, a reporting view, transactions, joins, aggregates, and parameterized SQL. Model training uses leakage-safe sklearn pipelines with imputation, scaling, and one-hot encoding. Logistic Regression and Random Forest are compared with accuracy, precision, recall, F1, ROC-AUC, Brier score, confusion matrix, and calibration plots.

Risk categories use the demonstration thresholds `Lower < 0.33`, `Moderate 0.33 to < 0.66`, and `Higher >= 0.66`. These thresholds are implementation choices, not medically validated cut-offs. Individual assessment explanations are Logistic Regression contributions (transformed feature value multiplied by its learned coefficient); positive values increase the model estimate and negative values decrease it. They describe model associations, not causation.

Event timestamps are stored in UTC: SQLite `CURRENT_TIMESTAMP` values are treated as UTC-naive legacy values, while Python-generated evaluation timestamps include UTC offsets. The `time_utils` display filter converts each event timestamp once to Asia/Kolkata (IST). Date-only fields such as date of birth are never timezone-shifted.

## Structure

`app.py` contains routes; `database/` contains schema and connection code; `services/` contains SQL-backed operations; `ml/` contains loading, training, prediction, explanation, and evaluation; `templates/` and `static/` contain the UI; `docs/` contains the seven report sections.

## Limitations and manual deliverables

The fallback data is synthetic, subgroup robustness experiments are not a clinical fairness certification, and no real patient data is included. Before submission, capture genuine screenshots, record and add the real demonstration link, publish the repository if desired, and convert `docs/consolidated_report.md` to the requested PDF.
