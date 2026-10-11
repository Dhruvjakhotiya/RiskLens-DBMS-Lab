import json
import pickle
from datetime import datetime, timezone

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import MODEL_DIR
from database.db import init_db, transaction
from ml.data_loader import FEATURES, load_dataset


NUMERIC = ["age", "bmi", "glucose", "blood_pressure"]
CATEGORICAL = ["activity_level", "smoking"]


def build_pipeline(estimator):
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                            ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    preprocessor = ColumnTransformer([("numeric", numeric, NUMERIC), ("categorical", categorical, CATEGORICAL)])
    return Pipeline([("preprocessor", preprocessor), ("model", estimator)])


def train_models(dataset_path=None):
    frame, source = load_dataset(dataset_path)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    models = {
        "Logistic Regression": build_pipeline(LogisticRegression(max_iter=1000, random_state=42)),
        "Random Forest": build_pipeline(RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)),
    }
    metadata = {"dataset_source": source, "features": FEATURES, "trained_at": datetime.now(timezone.utc).isoformat()}
    for name, pipeline in models.items():
        pipeline.fit(frame[FEATURES], frame["target"])
        slug = name.lower().replace(" ", "_")
        with (MODEL_DIR / f"{slug}.pkl").open("wb") as file:
            pickle.dump(pipeline, file)
        metadata[name] = {"artifact": str(MODEL_DIR / f"{slug}.pkl"), "version": "1.0"}
    (MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    init_db()
    with transaction() as db:
        disease = db.execute(
            "SELECT disease_id FROM diseases WHERE disease_code = 'T2D'"
        ).fetchone()
        if disease is None:
            db.execute(
                "INSERT INTO diseases (disease_code, disease_name) VALUES ('T2D', 'Type-2 Diabetes')"
            )
            disease = db.execute(
                "SELECT disease_id FROM diseases WHERE disease_code = 'T2D'"
            ).fetchone()
        for name in models:
            artifact = metadata[name]["artifact"]
            db.execute(
                """INSERT OR IGNORE INTO ml_models
                (disease_id, model_name, version, artifact_path, trained_at)
                VALUES (?, ?, ?, ?, ?)""",
                (disease[0], name, metadata[name]["version"], artifact, metadata["trained_at"]),
            )
    return metadata


if __name__ == "__main__":
    print(train_models())
