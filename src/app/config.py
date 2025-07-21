from __future__ import annotations
import os, json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

model_version = os.getenv("model_version", "v1")
models_dir = Path(os.getenv("models", "models"))
sur_path = models_dir / f"surrogate_lr_{model_version}.joblib"
preprocessor_path = models_dir / f"surrogate_lr_preprocessor_{model_version}.joblib"
background_path = models_dir / f"surrogate_background_{model_version}.parquet"
percentiles_path = models_dir / f"surrogate_percentiles_{model_version}.csv"
threshold_path = models_dir / f"surrogate_thresholds_{model_version}.json"

ui_features: List[str] = [
    "grade",
    "term",
    "acc_open_past_24mths",
    "dti",
    "fico_mid"
]

user_friendly: Dict[str, str] = {
    "grade": "Loan Grade",
    "term": "Loan Term (months)",
    "acc_open_past_24mths": "Accounts Opened (Past 24 Months)",
    "dti": "Debt-to-Income Ratio",
    "fico_mid": "FICO Score"
}

engineered_mapping: Dict[str, str] = {
    "grade_term": "grade + '_' + term string",
    "dti_inv": "inverse of (dti + 1e-3)",
    "fico_mid_sq": "square of fico_mid"
}

engineered_features_order: List[str] = [
    "grade_term",
    "acc_open_past_24mths",
    "dti_inv",
    "fico_mid_sq"
]

reason_codes: Dict[str, str] = {
    "grade_term": "GRADE_TERM_RISK",
    "acc_open_past_24mths": "RECENT_CREDIT_ACTIVITY",
    "dti": "HIGH_DTI",
    "dti_inv": "HIGH_DTI",
    "fico_mid": "FICO_SCORE",
    "fico_mid_sq": "FICO_SCORE"
}

display_names: Dict[str, str] = {
    "grade_term": "Grade & Term",
    "acc_open_past_24mths": "Recent Account Openings (24m)",
    "dti": "Debt-to-Income Ratio",
    "dti_inv": "Debt-to-Income Ratio",
    "fico_mid": "FICO Score",
    "fico_mid_sq": "FICO Score"
}

regulation_whitelist = [
    "12 CFR 1002 (ECOA)",
    "15 U.S.C. §1681 (FCRA)",
    "42 U.S.C. §3601 (Fair Housing Act)",
    "Gramm-Leach-Bliley Act",
    "Bank Secrecy Act",
    "UDAAP (CFPB)",
    "OCC Safety and Soundness Guidelines"
]

@dataclass
class ThresholdConfig:
    model_version: str
    value: float
    policy: str
    date_set: Optional[str] = None
    notes: Optional[str] = None

default_threshold_value = 0.115
default_threshold_policy = "profit"

def load_threshold_config(path: Path = threshold_path,
                          default_value: float = default_threshold_value,
                          default_policy: str = default_threshold_policy) -> ThresholdConfig:
    if not path.exists():
        cfg = ThresholdConfig(
            model_version=model_version,
            value=default_value,
            policy=default_policy,
            notes="auto-created default threshold"
        )
        write_threshold_config(cfg, path)
        return cfg
    data = json.loads(path.read_text())
    return ThresholdConfig(
        model_version=data.get("model_version", model_version),
        value=data.get("value", default_value),
        policy=data.get("policy", default_policy),
        date_set=data.get("date_set"),
        notes=data.get("notes")
    )

def write_threshold_config(cfg: ThresholdConfig, path: Path = threshold_path):
    path.write_text(json.dumps({
        "model_version": cfg.model_version,
        "value": cfg.value,
        "policy": cfg.policy,
        "date_set": cfg.date_set,
        "notes": cfg.notes
    }, indent=2))

threshold_cfg = load_threshold_config()
decision_threshold = threshold_cfg.value
threshold_policy = threshold_cfg.policy
near_threshold_band = float(os.getenv("near_threshold_band", "0.02"))

valid_grades = set("ABCDEFG")
valid_terms = {36, 60}

def validate_ui_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    missing = [f for f in ui_features if f not in payload]
    if missing:
        raise ValueError(f"Missing required features: {missing}")
    grade = str(payload["grade"]).strip().upper()
    if grade not in valid_grades:
        raise ValueError(f"Invalid grade '{grade}'. Expected one of {sorted(valid_grades)}")
    try:
        term_raw = str(payload["term"]).strip().lower().replace("months", "").strip()
        term = int(term_raw)
    except Exception:
        raise ValueError("Term must parse to integer 36 or 60")
    if term not in valid_terms:
        raise ValueError(f"Term must be 36 or 60. Got {term}")
    try:
        acc = int(payload["acc_open_past_24mths"])
        if acc < 0:
            raise ValueError
    except Exception:
        raise ValueError(f"Must be 0 or above. Got {acc}")
    try:
        dti = float(payload["dti"])
        if dti < 0:
            raise ValueError
    except Exception:
        raise ValueError("DTI must be greater than or equal to 0. Got {dti}")
    try:
        fico = int(payload["fico_mid"])
        if not (300 <= fico <= 850):
            raise ValueError
    except Exception:
        raise ValueError("FICO score must be between 300 and 850. Got {fico}")
    return {
        "grade": grade,
        "term": term,
        "acc_open_past_24mths": acc,
        "dti": dti,
        "fico_mid": fico
    }

__all__ = [
    "model_version",
    "models_dir",
    "sur_path",
    "preprocessor_path",
    "background_path",
    "percentiles_path",
    "threshold_path",
    "ui_features",
    "user_friendly",
    "engineered_mapping",
    "engineered_features_order",
    "reason_codes",
    "display_names",
    "regulation_whitelist",
    "ThresholdConfig",
    "load_threshold_config",
    "write_threshold_config",
    "threshold_cfg",
    "decision_threshold",
    "threshold_policy",
    "near_threshold_band",
    "validate_ui_payload"
]