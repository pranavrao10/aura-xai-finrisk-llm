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
    "Equal Credit Opportunity Act (ECOA), 15 U.S.C. §1691 et seq.; Regulation B, 12 CFR Part 1002",
    "CFPB Official Interpretations to Regulation B (12 CFR Part 1002, Supp. I)",
    "Adverse Action Notice Requirements (ECOA Reg B §1002.9; FCRA §615(a))",
    "Truth in Lending Act (TILA), 15 U.S.C. §1601 et seq.; Regulation Z, 12 CFR Part 1026",
    "CFPB Official Interpretations to Regulation Z (12 CFR Part 1026, Supp. I)",
    "Risk-Based Pricing Rule, FCRA §615(h); 12 CFR Part 1022 Subpart H",
    "Fair Credit Reporting Act (FCRA), 15 U.S.C. §1681 et seq.; Regulation V, 12 CFR Part 1022",
    "Furnisher Duties and Accuracy (FCRA §623; 12 CFR §1022.40-43)",
    "Credit Score Disclosure Requirements (FCRA §609(f), §609(g), §615(a))",
    "Home Mortgage Disclosure Act (HMDA), 12 U.S.C. §2801 et seq.; Regulation C, 12 CFR Part 1003",
    "CFPB Ability-to-Repay/Qualified Mortgage (ATR/QM), 12 CFR §1026.43 (Reg Z)",
    "Gramm-Leach-Bliley Act (GLBA) Privacy, 15 U.S.C. §6801-§6809; Regulation P, 12 CFR Part 1016",
    "GLBA Safeguards Rule (for non-bank financial institutions), 16 CFR Part 314",
    "CFPB Privacy of Consumer Financial Information—Reg P Appendix & Guidance",
    "Dodd-Frank Act UDAAP, 12 U.S.C. §§5531-5536 (CFPB)",
    "Federal Trade Commission Act §5 (UDAP) (for non-banks)",
    "Bank Secrecy Act (BSA), 31 U.S.C. §5311-§5336; FinCEN AML Program Rules, 31 CFR Chapter X",
    "Customer Identification Program (CIP) Rule, 31 CFR §1020.220",
    "Customer Due Diligence (CDD) Rule, 31 CFR §1010.230",
    "OFAC Sanctions Compliance (31 CFR Parts 500-599; OFAC Guidance)",
    "Servicemembers Civil Relief Act (SCRA), 50 U.S.C. §3901 et seq.",
    "Military Lending Act (MLA), 10 U.S.C. §987; DoD Rule, 32 CFR Part 232",
    "Fair Debt Collection Practices Act (FDCPA), 15 U.S.C. §1692 et seq.",
    "CFPB Mortgage Servicing (where applicable), 12 CFR Part 1024 (Reg X) & §1026.41 (Reg Z)",
    "CFPB Payday, Vehicle Title, and Certain High-Cost Installment Loans Rule, 12 CFR Part 1041",
    "OCC Interagency Guidelines Establishing Standards for Safety and Soundness, 12 CFR Part 30 App. A",
    "FDIC Interagency Guidelines for Safety and Soundness, 12 CFR Part 364 App. A",
    "Federal Reserve Safety and Soundness Standards, 12 CFR Part 208 App. D-1",
    "OCC Comptroller’s Handbook—Retail Credit Risk Management",
    "FFIEC IT Examination Handbook (Information Security, Development and Acquisition, Model Governance excerpts)",
    "SR 11-7 / OCC 2011-12: Supervisory Guidance on Model Risk Management",
    "Interagency Model Risk Management Guidance (SR 11-7 conforming materials and FAQs)",
    "CFPB Circular 2022-03 (Adverse action and use of complex models—specific reasons required)",
    "OCC 2023 Interagency Guidance on Third-Party Risk Management (OCC, FDIC, FRB)",
    "OCC 2013-29 (legacy) Third-Party Relationships—Risk Management (superseded but often cited historically)",
    "Interagency Guidelines Establishing Information Security Standards (GLBA Safeguards)—OCC/FDIC/FRB",
    "FFIEC Cybersecurity Assessment Tool (CAT) (reference framework)",
    "Community Reinvestment Act (CRA), 12 U.S.C. §2901 et seq.; 12 CFR Parts 25 (OCC), 228 (FRB), 345 (FDIC)",
    "Electronic Signatures in Global and National Commerce Act (E-SIGN), 15 U.S.C. §7001 et seq.",
    "NCUA Fair Lending and Consumer Compliance Guidance (NCUA Letters to Credit Unions, various)",
    "NCUA Privacy and Security—GLBA/Part 748 (Appendix A) (for credit unions)",
    "NIST AI Risk Management Framework (AI RMF 1.0) (non-binding reference)",
    "OCC, FDIC, FRB—Request for Information and statements on AI/ML in Banking (context references)",
    "OCC Safety and Soundness Guidelines",
    "UDAAP (CFPB)",
    "Bank Secrecy Act",
    "Gramm-Leach-Bliley Act",
    "42 U.S.C. §3601 (Fair Housing Act)",
    "15 U.S.C. §1681 (FCRA)",
    "12 CFR 1002 (ECOA)"
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