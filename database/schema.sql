PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    demo_identifier TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL CHECK(length(trim(full_name)) >= 2),
    date_of_birth TEXT NOT NULL,
    sex TEXT NOT NULL CHECK(sex IN ('Female', 'Male', 'Other', 'Prefer not to say')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS health_records (
    health_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    age INTEGER NOT NULL CHECK(age BETWEEN 18 AND 120),
    bmi REAL CHECK(bmi IS NULL OR bmi BETWEEN 10 AND 80),
    glucose REAL CHECK(glucose IS NULL OR glucose BETWEEN 40 AND 500),
    blood_pressure REAL CHECK(blood_pressure IS NULL OR blood_pressure BETWEEN 40 AND 250),
    physical_activity TEXT CHECK(physical_activity IS NULL OR physical_activity IN ('Low', 'Moderate', 'High')),
    smoking_status TEXT CHECK(smoking_status IS NULL OR smoking_status IN ('Never', 'Former', 'Current')),
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS diseases (
    disease_id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_code TEXT NOT NULL UNIQUE,
    disease_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS ml_models (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    trained_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    UNIQUE(disease_id, model_name, version),
    FOREIGN KEY(disease_id) REFERENCES diseases(disease_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    health_record_id INTEGER NOT NULL,
    disease_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    risk_probability REAL NOT NULL CHECK(risk_probability BETWEEN 0 AND 1),
    risk_category TEXT NOT NULL CHECK(risk_category IN ('Lower', 'Moderate', 'Higher')),
    assessed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    disclaimer_acknowledged INTEGER NOT NULL DEFAULT 1 CHECK(disclaimer_acknowledged IN (0, 1)),
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE RESTRICT,
    FOREIGN KEY(health_record_id) REFERENCES health_records(health_record_id) ON DELETE RESTRICT,
    FOREIGN KEY(disease_id) REFERENCES diseases(disease_id) ON DELETE RESTRICT,
    FOREIGN KEY(model_id) REFERENCES ml_models(model_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS prediction_explanations (
    explanation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value TEXT NOT NULL,
    contribution REAL NOT NULL,
    explanation_type TEXT NOT NULL CHECK(explanation_type IN ('local', 'global')),
    FOREIGN KEY(assessment_id) REFERENCES risk_assessments(assessment_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS model_evaluations (
    evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    dataset_name TEXT NOT NULL,
    evaluated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metrics_json TEXT NOT NULL,
    plot_path TEXT,
    FOREIGN KEY(model_id) REFERENCES ml_models(model_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_health_patient_time ON health_records(patient_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessment_patient_time ON risk_assessments(patient_id, assessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessment_disease ON risk_assessments(disease_id);

CREATE VIEW IF NOT EXISTS assessment_history AS
SELECT a.assessment_id, p.demo_identifier, p.full_name, d.disease_name,
       m.model_name, m.version, a.risk_probability, a.risk_category, a.assessed_at
FROM risk_assessments a
JOIN patients p ON p.patient_id = a.patient_id
JOIN diseases d ON d.disease_id = a.disease_id
JOIN ml_models m ON m.model_id = a.model_id;
