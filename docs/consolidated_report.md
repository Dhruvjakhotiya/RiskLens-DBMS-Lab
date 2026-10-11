# Consolidated DBMS Lab Report

## 1. Problem discovery
Students and community demonstrators need a low-cost, auditable way to show how risk prediction, data quality, and reliability differ from accuracy alone. Existing clinical products are outside this educational scope. This prototype addresses the gap with transparent demo records, historical persistence, calibration plots, and explicit limitations. References should be verified before submission; no clinical claims are made here.

## 2. Innovation proposal
RiskLens combines normalized health data management with reproducible model comparison, missing-data handling, probability calibration, and local feature contribution display. Its innovation is pedagogical: it makes reliability and explanation first-class database records rather than presenting a black-box score. Categories use Lower < 0.33, Moderate 0.33 to < 0.66, and Higher >= 0.66; these are not medically validated.

## 3. Software requirements
Functional requirements: register/update demo patients, add health records, train two models, assess a record, persist explanations, browse history, and view evaluation artifacts. Non-functional requirements: parameterized SQL, SQLite foreign-key enforcement, reproducibility, accessible responsive UI, and clear non-diagnostic messaging. Stakeholders are students, instructors, and demonstrators.

## 4. Database design
Tables are `patients`, `health_records`, `diseases`, `ml_models`, `risk_assessments`, `prediction_explanations`, and `model_evaluations`. Primary and foreign keys, unique identifiers, check constraints, indexes, and the `assessment_history` view are defined in `database/schema.sql`. The design is in 3NF: each fact has one owner, assessment rows reference entities, and explanations are separate rows rather than repeated groups.

## 5. Application prototype
The Flask routes call small service modules, which use `sqlite3` transactions and placeholders. The UI supports dashboard, patient and health-record workflows, assessment details, and history. Training artifacts are generated locally and ignored by Git. Assessment explanations are individual Logistic Regression contributions: transformed feature value multiplied by the learned coefficient. Positive values increase the model estimate and negative values decrease it; these are associations, not causation.

## 6. Testing and validation
Run `pytest -q` after installing requirements. The repository includes tests covering schema constraints, foreign keys, CRUD operations, SQL injection resistance, model output, missing artifact errors, and Flask responses. Record the actual command output here after execution; do not replace it with invented numbers.

## 7. Impact and TRL
Potential impact is improved understanding of responsible data and ML evaluation, not clinical deployment. Based on the implemented local prototype and synthetic fallback, the defensible assessment is TRL 3 (experimental proof of concept). It has no clinical validation, external security review, prospective study, or deployment evidence.

## Submission checklist
- [ ] Capture genuine dashboard, patient, assessment, and evaluation screenshots.
- [ ] Add the real recorded-video URL.
- [ ] Add a repository URL if published.
- [ ] Convert this Markdown to one PDF.
