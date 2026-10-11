import pickle
from pathlib import Path

import pandas as pd

from ml.data_loader import FEATURES

DISPLAY_NAMES = {
    "age": "Age",
    "bmi": "BMI",
    "glucose": "Glucose",
    "blood_pressure": "Blood pressure",
    "activity_level": "Physical activity",
    "smoking": "Smoking status",
}


def load_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Model artifact not found: {path}. Run python -m ml.train_model.")
    with path.open("rb") as file:
        return pickle.load(file)


def predict(model, values):
    frame = pd.DataFrame([{feature: values.get(feature) for feature in FEATURES}])
    probability = float(model.predict_proba(frame)[0, 1])
    category = "Lower" if probability < 0.33 else "Moderate" if probability < 0.66 else "Higher"
    return probability, category


def explanations(model, values):
    estimator = model.named_steps["model"]
    names = model.named_steps["preprocessor"].get_feature_names_out()
    transformed = model.named_steps["preprocessor"].transform(pd.DataFrame([{f: values.get(f) for f in FEATURES}]))
    transformed_values = transformed.toarray() if hasattr(transformed, "toarray") else transformed
    if not hasattr(estimator, "coef_"):
        raise ValueError("Individual explanations require a model with coefficients.")
    contributions = transformed_values[0] * estimator.coef_[0]
    grouped = {}
    for name, contribution in zip(names, contributions):
        transformed_name = name.split("__", 1)[-1]
        feature = next(
            (candidate for candidate in FEATURES
             if transformed_name == candidate or transformed_name.startswith(f"{candidate}_")),
            transformed_name,
        )
        grouped[feature] = grouped.get(feature, 0.0) + float(contribution)
    ordered = sorted(grouped.items(), key=lambda item: abs(item[1]), reverse=True)[:5]
    return [
        (DISPLAY_NAMES.get(feature, feature.replace("_", " ").title()),
         "Missing" if values.get(feature) is None else values.get(feature),
         contribution)
        for feature, contribution in ordered
    ]
