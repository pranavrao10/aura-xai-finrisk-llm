import json
import numpy as np
import pandas as pd
import pytest

from aura.app.config import validate_ui_payload, validate_one, InputError
from aura.app.config import decision_threshold, near_threshold_band
from aura.models import predict as predict_mod

@pytest.fixture
def valid_payload():
    return {
        "grade": "A",
        "term": 36,
        "acc_open_past_24mths": 2,
        "dti": 15.0,
        "fico_mid": 750
    }

@pytest.fixture
def dummy_percentiles_df(monkeypatch):
    df = pd.DataFrame({
        "feature": ["fico_mid_sq", "dti_inv", "acc_open_past_24mths", "fico_mid", "dti"],
        "min": [0, 0, 0, 300, 0],
        "max": [850**2, 1, 50, 850, 100],
        "p25": [600**2, 0.2, 5, 600, 20],
        "p50": [700**2, 0.1, 10, 700, 30],
        "p75": [780**2, 0.05, 20, 780, 40]
    })
    def fake_load():
        return df
    monkeypatch.setattr(predict_mod, "load_percentiles", fake_load)
    return df

@pytest.fixture
def mock_model(monkeypatch):
    class DummyModel:
        def predict_proba(self, X):
            return np.array([[0.123, 0.877]])  

    def fake_load_sur():
        return DummyModel()

    monkeypatch.setattr(predict_mod, "load_sur", fake_load_sur)
    return DummyModel()

@pytest.fixture
def mock_explainer(monkeypatch):
    def fake_local_shap(eng_df, raw_row, max_reasons=5):
        return [
            {
                "feature": "FICO Score",
                "raw_feature_key": "fico_mid",
                "engineered_feature_key": "fico_mid_sq",
                "applicant_value": raw_row["fico_mid"],
                "percentile": 90,
                "direction": "↓ risk",
                "shap_contribution": -0.12,
                "magnitude": "High",
            }
        ]
    monkeypatch.setattr(predict_mod, "local_shap", fake_local_shap)
    return fake_local_shap

@pytest.fixture
def mock_llm_raise(monkeypatch):
    from src.explain import explainer as exp_mod
    def boom(*args, **kwargs):
        raise RuntimeError("LLM down")
    monkeypatch.setattr(exp_mod, "call_llm", boom)

@pytest.fixture
def mock_llm_ok(monkeypatch):
    from src.explain import explainer as exp_mod
    def ok(prompt, temperature=0.25, max_tokens=1000):
        return "Fake narrative. (Model-version: v1)"
    monkeypatch.setattr(exp_mod, "call_llm", ok)