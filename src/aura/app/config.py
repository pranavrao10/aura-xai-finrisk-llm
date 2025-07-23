from __future__ import annotations
import os, json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

model_version = os.getenv("model_version", "v1")
models_dir = Path(os.getenv("models", "models"))
sur_path = models_dir / f"surrogate_lr_{model_version}.joblib"
background_path = models_dir / f"surrogate_background_{model_version}.parquet"
percentiles_path = models_dir / f"surrogate_percentiles_{model_version}.csv"
threshold_path = models_dir / f"surrogate_thresholds_{model_version}.json"
default_threshold_value = 0.115
default_threshold_policy = "profit"

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
    "acc_open_past_24mths": "Number of Accounts Opened in Last 24 Months",
    "dti": "Debt-to-Income Ratio",
    "fico_mid": "FICO Score"
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

def write_threshold_config(cfg: ThresholdConfig, path: Path = threshold_path):
    path.write_text(json.dumps({
        "model_version": cfg.model_version,
        "value": cfg.value,
        "policy": cfg.policy,
        "date_set": cfg.date_set,
        "notes": cfg.notes
    }, indent=2))

def load_threshold_config(path: Path = threshold_path) -> ThresholdConfig:
    if not path.exists():
        cfg = ThresholdConfig(model_version=model_version,
                              value=default_threshold_value,
                              policy=default_threshold_policy,
                              notes="auto-created default threshold")
        write_threshold_config(cfg, path)
        return cfg
    data = json.loads(path.read_text())
    missing = [k for k in ("value", "policy") if k not in data]
    if missing:
        raise KeyError(f"Threshold JSON missing required keys: {missing}")
    try:
        val = float(data["value"])
    except Exception:
        raise TypeError("Threshold 'value' must be numeric")
    pol = str(data["policy"])
    mv = data.get("model_version", model_version)
    return ThresholdConfig(
        model_version=mv,
        value=val,
        policy=pol,
        date_set=data.get("date_set"),
        notes=data.get("notes")
    )

threshold_cfg = load_threshold_config()
decision_threshold = threshold_cfg.value
threshold_policy = threshold_cfg.policy
near_threshold_band = float(os.getenv("near_threshold_band", "0.02"))

valid_grades = set("ABCDEFG")
valid_terms = {36, 60}
fico_min, fico_max = 300, 850

class InputError(ValueError):
    pass

def validate_one(feature: str, raw: Any) -> Any:
    if feature == "grade":
        g = str(raw).strip().upper()
        if g not in valid_grades:
            raise InputError(f"Grade must be a letter between A-G. Got '{g}'")
        return g

    if feature == "term":
        try:
            n = int(str(raw).strip().split()[0])
        except Exception:
            raise InputError(f"Term must be 36 or 60. Got '{raw}'")
        if n not in valid_terms:
            raise InputError(f"Term must be 36 or 60. Got '{n}'")
        return n

    if feature == "acc_open_past_24mths":
        try:
            n = int(raw)
        except Exception:
            raise InputError(f"Cannot be negative or non-integer. Got '{raw}'")
        if n < 0:
            raise InputError(f"Cannot be negative or non-integer. Got '{raw}'")
        return n

    if feature == "dti":
        try:
            d = float(raw)
        except Exception:
            raise InputError(f"DTI must be numeric and cannot be negative (ex: 15 or 15.2). Got '{raw}'")
        if d < 0:
            raise InputError(f"DTI must be numeric and cannot be negative (ex: 15 or 15.2). Got '{raw}'")
        return d

    if feature == "fico_mid":
        try:
            f = int(raw)
        except Exception:
            raise InputError(f"FICO must be between 300 and 850. Got '{raw}'")
        if not (fico_min <= f <= fico_max):
            raise InputError(f"FICO must be between 300 and 850. Got '{raw}'")
        return f

    raise InputError(f"Unknown feature '{feature}'")


def validate_ui_payload(data: Dict[str, Any],
                        require_all: bool = True) -> Dict[str, Any]:
    if require_all:
        missing = [f for f in ui_features if f not in data]
        if missing:
            raise InputError(f"Missing required features: {missing}")

    cleaned: Dict[str, Any] = {}
    for k, v in data.items():
        if k not in ui_features:
            raise InputError(f"Unexpected feature '{k}'")
        cleaned[k] = validate_one(k, v)
    return cleaned

__all__ = [
    "model_version",
    "models_dir",
    "sur_path",
    "background_path",
    "percentiles_path",
    "threshold_path",
    "ui_features",
    "user_friendly",
    "regulation_whitelist",
    "ThresholdConfig",
    "load_threshold_config",
    "write_threshold_config",
    "threshold_cfg",
    "decision_threshold",
    "threshold_policy",
    "near_threshold_band",
    "validate_ui_payload",
    "validate_one",
    "InputError"
]