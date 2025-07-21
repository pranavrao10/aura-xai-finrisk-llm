from __future__ import annotations
import joblib, pandas as pd, numpy as np, shap, json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
import scipy.sparse as sp
from rich import print as rprint
from src.app.config import (
    model_version,
    sur_path,
    preprocessor_path,
    background_path,
    percentiles_path,
    ui_features,
    engineered_features_order,
    reason_codes,
    display_names,
    decision_threshold,
    threshold_policy,
    near_threshold_band,
    validate_ui_payload
)

sur_cache = None
background_cache = None
explainer_cache = None
percentiles_cache = None

def load_sur():
    global sur_cache
    if sur_cache is None:
        if not Path(sur_path).exists():
            raise FileNotFoundError(f"missing sur artifact {sur_path}")
        sur_cache = joblib.load(sur_path)   
    return sur_cache

def load_background():
    global background_cache
    if background_cache is None:
        if not Path(background_path).exists():
            raise FileNotFoundError(f"missing background artifact {background_path}")
        background_cache = pd.read_parquet(background_path)
    return background_cache

def load_percentiles():
    global percentiles_cache
    if percentiles_cache is None:
        if Path(percentiles_path).exists():
            df = pd.read_csv(percentiles_path)
            percentiles_cache = df
        else:
            percentiles_cache = pd.DataFrame()
    return percentiles_cache

def canonical_term_str(term_val):
    try:
        n = int(str(term_val).strip().split()[0])
        return f" {n} months" 
    except (ValueError, IndexError):
        raise ValueError(f"Invalid term value: {term_val}")

def engineer(df: pd.DataFrame) -> pd.DataFrame:
    z = df.copy()
    z["term"] = z["term"].apply(canonical_term_str)
    z["grade_term"] = z["grade"].astype(str) + "_" + z["term"]
    z["dti_inv"] = 1.0 / (z["dti"] + 1e-3)
    z["fico_mid_sq"] = z["fico_mid"].astype(float) ** 2
    z = z[["grade_term", "acc_open_past_24mths", "dti_inv", "fico_mid_sq"]]
    return z

def build_explainer():
    global explainer_cache
    if explainer_cache is not None:
        return explainer_cache
    sur = load_sur()              
    if hasattr(sur, "calibrated_classifiers_"):
        inner = sur.calibrated_classifiers_[0].estimator
    else:
        inner = getattr(sur, "estimator", sur)
    pre = inner.named_steps["pre"]
    clf = inner.named_steps["clf"]
    bg = load_background()
    needed = {"grade_term","acc_open_past_24mths","dti_inv","fico_mid_sq"}
    if not needed.issubset(bg.columns):
        if set(ui_features).issubset(bg.columns):
            bg = engineer(bg[ui_features])
        else:
            raise ValueError(f"Background columns mismatch; have {bg.columns.tolist()}")
    bg_trans = pre.transform(bg)
    masker = shap.maskers.Independent(bg_trans)
    explainer = shap.LinearExplainer(clf, masker)
    explainer_cache = (explainer, pre)
    return explainer_cache

def extract_feature_names(pre):
    if hasattr(pre, "get_feature_names_out"):
        return pre.get_feature_names_out().tolist()
    names = []
    for (name, trans, cols) in pre.transformers_:
        if name == "remainder":
            continue
        if hasattr(trans, "get_feature_names_out"):
            out = trans.get_feature_names_out(cols)
            names.extend(out.tolist())
        else:
            names.extend(list(cols))
    return names

def map_engineered_to_raw(feature: str) -> str:
    if feature.startswith("grade_term"):
        return "grade_term"
    if feature in ("dti_inv",):
        return "dti"
    if feature in ("fico_mid_sq",):
        return "fico_mid"
    return feature


def percentile_lookup(value: float, feature: str) -> float | None:
    pct_df = load_percentiles()
    if pct_df.empty:
        return None
    row = pct_df[pct_df["feature"] == feature]
    if row.empty:
        return None
    row = row.iloc[0].to_dict()
    anchors = []
    for k, v in row.items():
        if k.startswith("p") and k[1:].isdigit():
            anchors.append((int(k[1:]), float(v)))
    if not anchors:
        return None
    anchors.sort()
    if value <= row["min"]:
        return 0.0
    if value >= row["max"]:
        return 1.0
    prev_q, prev_v = 0, row["min"]
    for q, v in anchors:
        if value <= v:
            if v == prev_v:
                return q / 100.0
            frac = (value - prev_v) / (v - prev_v)
            return (prev_q / 100.0) + frac * ((q - prev_q) / 100.0)
        prev_q, prev_v = q, v
    last_q_val = anchors[-1]
    if value <= row["max"]:
        q, v = last_q_val
        if row["max"] == v:
            return q / 100.0
        frac = (value - v) / (row["max"] - v)
        return (q / 100.0) + frac * ((1.0 - q / 100.0))
    return None


def consolidate_reason(base_feature: str,
                       shap_val: float,
                       raw_row: dict,
                       eng_row: dict) -> dict:
    raw_feature = map_engineered_to_raw(base_feature)
    value = raw_row.get(raw_feature, eng_row.get(base_feature))
    display = display_names.get(raw_feature, display_names.get(base_feature, raw_feature))
    pct_key, pct_val = None, None
    if isinstance(value, (int, float)):
        if base_feature == "fico_mid_sq":
            pct_key, pct_val = "fico_mid_sq", eng_row["fico_mid_sq"] 
        elif base_feature == "dti_inv":
            pct_key, pct_val = "dti_inv", eng_row["dti_inv"]
        elif raw_feature not in ("grade", "term", "grade_term"):
            pct_key, pct_val = raw_feature, float(value)
    percentile = None
    if pct_key is not None:
        frac = percentile_lookup(pct_val, pct_key)       
        percentile = int(round(frac * 100)) if frac is not None else None
    if base_feature == "dti_inv":
        direction = "↑ risk" if shap_val < 0 else "↓ risk"
    else:
        direction = "↑ risk" if shap_val > 0 else "↓ risk"
    reason_code = reason_codes.get(base_feature,
                   reason_codes.get(raw_feature, base_feature.upper()))
    return {
        "feature": display,
        "raw_feature_key": raw_feature,
        "engineered_feature_key": base_feature,
        "applicant_value": value,
        "percentile": percentile,
        "direction": direction,
        "shap_contribution": float(shap_val),
        "reason_code": reason_code
    }

def local_shap(eng_df: pd.DataFrame,
               raw_row: dict,
               max_reasons: int = 5) -> list[dict]:
    explainer, pre = build_explainer()
    x_trans = pre.transform(eng_df)
    shap_vals = explainer.shap_values(x_trans)
    if isinstance(shap_vals, list):      
        shap_vals = shap_vals[0]
    shap_row = np.array(shap_vals)[0]

    feature_names = extract_feature_names(pre)

    if sp.issparse(x_trans):
        row_values = x_trans.toarray()[0]
    else:
        row_values = np.array(x_trans)[0]

    candidates = []
    for idx, full_name in enumerate(feature_names):
        if "__" in full_name:
            base_part = full_name.split("__", 1)[1]
        else:
            base_part = full_name

        if base_part.startswith("grade_term_"):
            if row_values[idx] == 1:
                candidates.append(("grade_term", shap_row[idx], base_part))
        else:
            candidates.append((base_part, shap_row[idx], base_part))

    agg = {}
    levels = {}
    for feat, sval, lvl in candidates:
        if feat not in agg or abs(sval) > abs(agg[feat]):
            agg[feat] = sval
            levels[feat] = lvl

    ordered = sorted(agg.items(), key=lambda kv: -abs(kv[1]))

    reasons = []
    used_raw = set()
    eng_row = eng_df.iloc[0].to_dict()

    for feat, sval in ordered:
        if len(reasons) >= max_reasons:
            break
        raw_key = map_engineered_to_raw(feat)
        if raw_key in used_raw and raw_key not in ("grade_term",):
            continue
        reasons.append(consolidate_reason(feat, sval, raw_row, eng_row))
        used_raw.add(raw_key)
    
    abs_vals = [abs(r["shap_contribution"]) for r in reasons if r.get("shap_contribution") is not None]
    if abs_vals:
        m = max(abs_vals)
        for r in reasons:
            a = abs(r["shap_contribution"])
            rel = a / m if m > 0 else 0
            r["magnitude"] = "High" if rel >= 0.60 else "Moderate" if rel >= 0.30 else "Low"
    for r in reasons:
        r.pop("reason_code", None)
    return reasons

def predict_with_explanations(applicant_payload: Dict[str,Any], max_reasons=5):
    raw_valid = validate_ui_payload(applicant_payload)
    raw_df = pd.DataFrame([raw_valid], columns=ui_features)
    eng_df = engineer(raw_df)
    sur = load_sur()
    prob = float(sur.predict_proba(eng_df)[0,1])
    delta = prob - decision_threshold
    risk = "High" if prob >= decision_threshold else "Low"
    reasons = local_shap(eng_df, raw_valid, max_reasons=max_reasons)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_version": model_version,
        "threshold_policy": threshold_policy,
        "threshold": decision_threshold,
        "near_threshold_band": near_threshold_band,
        "prob_default": prob,
        "threshold_delta": delta,
        "risk_class": risk,
        "raw_input": raw_valid,
        "engineered": eng_df.iloc[0].to_dict(),
        "top_local_shap": reasons
    }

def save_prediction_log(record: Dict[str, Any], path: Path = Path("logs") / "predictions.log"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")