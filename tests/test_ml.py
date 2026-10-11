import pandas as pd
import pytest

from ml.predict import explanations, load_model
from ml.train_model import build_pipeline
from sklearn.linear_model import LogisticRegression


def test_prediction_probability():
    model = build_pipeline(LogisticRegression(max_iter=1000))
    frame = pd.DataFrame([
        {"age": 40, "bmi": 28, "glucose": 120, "blood_pressure": 130, "activity_level": "Moderate", "smoking": "Never", "target": 0},
        {"age": 65, "bmi": 35, "glucose": 190, "blood_pressure": 160, "activity_level": "Low", "smoking": "Current", "target": 1},
    ])
    model.fit(frame.drop(columns="target"), frame["target"])
    probability = model.predict_proba(frame.drop(columns="target"))[:, 1]
    assert all(0 <= item <= 1 for item in probability)


def test_missing_model_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_model(tmp_path / "missing.pkl")


def test_individual_explanations_are_readable_and_handle_missing_categories():
    model = build_pipeline(LogisticRegression(max_iter=1000))
    frame = pd.DataFrame([
        {"age": 40, "bmi": 28, "glucose": 120, "blood_pressure": 130, "activity_level": "Moderate", "smoking": "Never", "target": 0},
        {"age": 65, "bmi": 35, "glucose": 190, "blood_pressure": 160, "activity_level": "Low", "smoking": "Current", "target": 1},
        {"age": 52, "bmi": 31, "glucose": 150, "blood_pressure": 145, "activity_level": "High", "smoking": "Former", "target": 1},
    ])
    model.fit(frame.drop(columns="target"), frame["target"])
    result = explanations(model, {
        "age": 52, "bmi": None, "glucose": 150, "blood_pressure": 145,
        "activity_level": None, "smoking": None,
    })
    names = {item[0] for item in result}
    assert names <= {"Age", "BMI", "Glucose", "Blood pressure", "Physical activity", "Smoking status"}
    assert all(item[1] != "None" for item in result)
    assert any(item[1] == "Missing" for item in result)
