import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import (accuracy_score, brier_score_loss, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split

from config import DATABASE_PATH, MODEL_DIR, PLOTS_DIR
from database.db import transaction
from ml.data_loader import FEATURES, load_dataset


def evaluate_models(dataset_path=None, db_path=DATABASE_PATH):
    frame, source = load_dataset(dataset_path)
    train, test = train_test_split(frame, test_size=0.25, random_state=42, stratify=frame["target"])
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in ("Logistic Regression", "Random Forest"):
        slug = name.lower().replace(" ", "_")
        model_path = MODEL_DIR / f"{slug}.pkl"
        if not model_path.exists():
            continue
        import pickle
        with model_path.open("rb") as file:
            model = pickle.load(file)
        model.fit(train[FEATURES], train["target"])
        probabilities = model.predict_proba(test[FEATURES])[:, 1]
        predicted = (probabilities >= 0.5).astype(int)
        metrics = {
            "accuracy": accuracy_score(test["target"], predicted),
            "precision": precision_score(test["target"], predicted, zero_division=0),
            "recall": recall_score(test["target"], predicted, zero_division=0),
            "f1": f1_score(test["target"], predicted, zero_division=0),
            "brier_score": brier_score_loss(test["target"], probabilities),
            "confusion_matrix": confusion_matrix(test["target"], predicted).tolist(),
            "roc_auc": roc_auc_score(test["target"], probabilities) if test["target"].nunique() > 1 else None,
            "dataset_source": source,
            "test_count": len(test),
        }
        fraction, mean = calibration_curve(test["target"], probabilities, n_bins=5, strategy="quantile")
        evaluation_run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        evaluated_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        figure, axis = plt.subplots()
        axis.plot(mean, fraction, marker="o", label=name)
        axis.plot([0, 1], [0, 1], "--", label="Perfect calibration")
        axis.set(xlabel="Mean predicted probability", ylabel="Observed frequency", title=f"{name} calibration")
        axis.legend()
        plot_path = PLOTS_DIR / f"{slug}_calibration_{evaluation_run_id}.png"
        figure.savefig(plot_path, bbox_inches="tight")
        plt.close(figure)
        metrics["plot_path"] = str(plot_path)
        metrics["evaluation_run_id"] = evaluation_run_id
        results[name] = metrics
        with transaction(db_path) as db:
            model_row = db.execute(
                """SELECT model_id, version FROM ml_models
                WHERE model_name = ? AND is_active = 1
                ORDER BY model_id DESC LIMIT 1""",
                (name,),
            ).fetchone()
            if model_row:
                db.execute(
                    """INSERT INTO model_evaluations
                    (model_id, dataset_name, evaluated_at, metrics_json, plot_path)
                    VALUES (?, ?, ?, ?, ?)""",
                    (model_row[0], source, evaluated_at, json.dumps(metrics), str(plot_path)),
                )
    (MODEL_DIR / "evaluation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    print(json.dumps(evaluate_models(), indent=2))
