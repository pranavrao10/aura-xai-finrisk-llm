# AURA: Explainable AI for Financial Risk Assessment Using Large Language Models

---

## Table of Contents

1. [Project Overview](#overview-of-project)
2. [Key Features](#key-features)
3. [How It Works (Architecture)](#how-it-works)
4. [Dataset & Pre-processing](#dataset--preprocessing)
5. [Model & Performance](#performance)
6. [Explainability Layer](#explainability-layer)
7. [Regulatory Context](#regulatory-context)
8. [Reproducibility & Running the App](#reproducibility--running-the-app)
   - [Quick Start with Docker (Recommended)](#quick-start-with-docker-recommended)
   - [Local Dev Setup](#local-dev-setup)
9. [Testing](#testing)
10. [Contributors](#contributors)
11. [License](#license)

---

## Overview of Project

AURA (Autonomous Risk Assessment) is focused on making AI driven credit risk assessments more transparent, explainable, and regulatory compliant. In highly regulated industries like finance, black box models fail to meet trust and compliance standards. AURA bridges this gap by combining advanced machine learning, explainable AI (XAI), and Large Language Models (LLMs) to assess loan default risk with interpretability baked in.

The system predicts the likelihood of loan default and also generates human readable justifications for every decision using SHAP and Retrieval-Augmented Generation (RAG) grounded in real world lending regulations.

AURA demonstrates an end to end credit risk scoring system for educational and demo purposes. It ingests simple applicant attributes (grade, term, FICO, DTI, recently opened accounts), predicts probability of default (PD), and provides transparent, audit ready explanations.

This repository shows how an ML/LLM system can be engineered like a real product: validated inputs, cached SHAP explainers, narrative generation with graceful fallbacks, a clean FastAPI service, a Streamlit UI, unit tests, and Docker for reproducibility.

---

## Key Features

- **Credit Risk Prediction** using LightGBM and a Surrogate Logistic Regression Model with calibrated thresholding (profit policy by default).
- **Feature Engineering**: `grade_term`, `dti_inv`, `fico_mid_sq`.
- **Percentile Mapping** for each numeric factor (CSV anchors → continuous percentile).
- **Local Explainability**: SHAP values aggregated & humanized (direction, magnitude).
- **Natural Language Explanations** powered by GPT 4.1 constrained by a strict system prompt, with fallback text if the LLM fails.
- **Policy Grounding** through Retrieval-Augmented Generation (RAG)
- **Strict Input Validation**: Single source of truth for validation rules. CLI, API, and UI all reuse it.
- **API + UI**: FastAPI endpoints and a Streamlit front-end.
- **Hygiene**: Pyproject packaging, pytest suite, Docker multi-stage build, env-based secrets.

---

## How it Works:

### Building the App

1. **Data Collection**: Acquire dataset from Lending Club.
2. **EDA/Preprocessing**: Clean, impute, feature engineering.
3. **Modeling**: Train baseline, advanced, and surrogate models.
4. **Explainability**: Add SHAP for per decision transparency.
5. **LLM Integration**: Use GPT 4.1 to convert SHAP outputs into readable justifications.
6. **RAG**: Store compliance docs in a vector DB (ChromaDB). Retrieve relevant snippets to contextualize decisions.
7. **Deployment**: Backend with FastAPI, frontend with Streamlit, all containerized using Docker.
8. **Evaluation**: Analyze performance + interpretability through metrics and user feedback.

### Using the App

9. **Input & Transport**

   - A user submits loan attributes via the Streamlit UI

10. **Validation**
    - `validate_one/validate_ui_payload` enforce strict type/range checks (grade A–G, term 36/60, DTI ≥ 0, FICO 300–850, etc.).
11. **Feature Engineering**

    - Raw inputs are transformed (`grade_term`, `dti_inv`, `fico_mid_sq`).
    - The same transformations used in training are applied at inference.

12. **Prediction**

    - A cached surrogate Logistic Regression model (`surrogate_lr_v1.joblib`) produces a probability of default (PD).
    - A profit optimized threshold classifies as High/Low risk and computes the delta.

13. **Local Explainability (SHAP)**

    - SHAP values are computed using a cached explainer and background mask.
    - Values are aggregated per raw feature, direction (↑/↓ risk) is derived from SHAP sign, and magnitude is normalized (High/Moderate/Low).
    - Percentiles are looked up from a precomputed CSV and converted to 0–100.

14. **Narrative Generation (LLM)**

    - A compact JSON summary of the decision is fed to GPT-4.1 with a strict system prompt (regulatory whitelist, formatting rules).
    - If the LLM fails (no key, timeout), a deterministic fallback narrative is returned.

15. **Response**

    - `/predict` returns PD, threshold, classification, SHAP reasons.
    - `/explain` returns only the narrative.
    - `/predict_explain` bundles both.
    - Streamlit renders the results, shows the narrative, and offers a download button.

16. **Logging & Audit**
    - Predictions and narratives are appended to JSONL logs for reproducibility/audit.
    - Thresholds and config are versioned.

---

## Dataset & Preprocessing

**Dataset**:

- **Primary Dataset**: Lending Club loan data
- **Target**: Default / non-default binary label.
- **Splits**: Time Based Train/validation/test split. Train data up to 2016, Validation data up to 2017, Test data up to 2018.
- **Format**: CSV
- **Source**: [https://www.lendingclub.com/info/download-data.action](https://www.lendingclub.com/info/download-data.action)

**Preprocessing Steps**:

- Data Cleaning
- Drop unusable/missing records and protected attributes.
- Missing value imputation
- Feature Engineering
- Continuous features standardized via the scikit-learn pipeline (inside the saved preprocessor).
- Engineered features computed before model inference (see `engineer()`).

> Percentiles are precomputed and stored in `data/surrogate_percentiles_v1.csv`; they’re not regenerated during demo runtime.

---

## Performance

-- **Model**: Baseline Logistic Regression Model -> LightGBM -> SHAP Analysis -> Surrogate Logistic Regression Model trained on engineered features.

- **Thresholding**: Profit optimized cutoff (~0.115).

| Model         | PR_AUC  | Precision | Recall  | F1 Score | ROC-AUC | KS Score |
| ------------- | ------- | --------- | ------- | -------- | ------- | -------- |
| Logistic Reg. | `0.823` | `0.412`   | `0.932` | `0.572`  | `0.870` | `0.583`  |
| LightGBM      | `0.834` | `0.407`   | `0.935` | `0.568`  | `0.871` | `0.588`  |
| Surrogate LR  | `0.414` | `0.324`   | `0.966` | `0.485`  | `0.652` | `0.227`  |

- Accuracy not reported due to imbalanced dataset.

---

## Explainability Layer

- **SHAP** identifies directional contribution of each feature for the applicant.
- Consolidation logic:

  - Maps engineered → raw features (e.g., `dti_inv` → `dti`).
  - Computes percentiles correctly (0th–100th) with edge-case handling (e.g., 850 FICO).
  - Direction arrow uses SHAP sign (+ = ↑ risk, − = ↓ risk) with special handling for inversions.
  - Magnitude (High/Moderate/Low) is relative to the max absolute SHAP.

- **LLM Narrative** (GPT-4.1):
  - Constrained system prompt to ensure regulatory compliance tone and formatting.
  - Regulatory whitelist only (ECOA, FCRA, etc.).
  - Fallback text if the API is down or output malformed.

---

## Regulatory Context

The narrative cites at least one regulation from:

- 12 CFR 1002 (ECOA)
- 15 U.S.C. §1681 (FCRA)
- 42 U.S.C. §3601 (Fair Housing Act), etc.

No protected classes are used; explanations avoid causal language (“associated with” vs. “causes”).

---

## Reproducibility & Running the App

### Quick Start with Docker (Recommended)

1. **Clone & configure env:**

   ```bash
   git clone https://github.com/pranavrao10/aura-xai-finrisk-llm.git
   cd aura-xai-finrisk-llm

   cp .env.example .env  # put your OPENAI_API_KEY inside

   ```

2. **Build and Run**

   ```bash
   docker compose up --build

   •API: http://localhost:8000
   •UI:  http://localhost:8501

   ```

3. **Stop**

   ```bash
   docker compose down
   ```

### Local Dev Setup

4. ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e .[api,ui,dev]

   export OPENAI_API_KEY=sk-...
   uvicorn aura.api.server:app --reload   # API on :8000
   streamlit run src/aura/ui/streamlit_app.py  # UI on :8501
   ```

---

## Testing

We use pytest with minimal yet critical coverage:
-test_validate.py – input edge cases (grade, negatives, bounds).
-test_percentiles.py – min/max, engineered feature mapping.
-test_predict.py – mocks predict_proba for deterministic outputs.
-test_explainer_fallback.py – forces LLM error to test graceful degradation.
-test_threshold_logic.py – confirm threshold & near-threshold flag behavior.

Run:

pytest -q --disable-warnings

---

## Contributors

• Pranav Rao (@pranavrao10)

---

## License

MIT License – see LICENSE.
