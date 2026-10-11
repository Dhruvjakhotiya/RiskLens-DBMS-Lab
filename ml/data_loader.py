from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["age", "bmi", "glucose", "blood_pressure", "activity_level", "smoking"]


def synthetic_dataset(n=500, seed=42):
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 81, n)
    bmi = np.round(rng.normal(27, 5, n).clip(16, 48), 1)
    glucose = np.round(rng.normal(115, 35, n).clip(55, 260), 1)
    blood_pressure = np.round(rng.normal(125, 18, n).clip(80, 210), 1)
    activity_level = rng.choice(["Low", "Moderate", "High"], n, p=[0.25, 0.5, 0.25])
    smoking = rng.choice(["Never", "Former", "Current"], n, p=[0.6, 0.25, 0.15])
    score = -6 + age * 0.035 + bmi * 0.07 + glucose * 0.018 + blood_pressure * 0.006
    score += (activity_level == "Low") * 0.35 + (smoking == "Current") * 0.2
    probability = 1 / (1 + np.exp(-score))
    target = rng.binomial(1, probability)
    return pd.DataFrame({
        "age": age, "bmi": bmi, "glucose": glucose, "blood_pressure": blood_pressure,
        "activity_level": activity_level, "smoking": smoking, "target": target,
    })


def load_dataset(path: Path | None = None):
    """Load a local CSV if supplied; otherwise create labelled demo data."""
    if path and path.exists():
        frame = pd.read_csv(path)
        required = set(FEATURES + ["target"])
        if not required.issubset(frame.columns):
            raise ValueError(f"Dataset must contain columns: {', '.join(sorted(required))}")
        return frame[FEATURES + ["target"]], "local_csv"
    return synthetic_dataset(), "synthetic_demo_fallback"
