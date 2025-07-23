from aura.explain.explainer import generate_explanation

def test_llm_fallback(valid_payload, mock_model, mock_explainer, mock_llm_raise):
    fake_bundle = {
        "timestamp": "2025-01-01T00:00:00Z",
        "model_version": "v1",
        "threshold_policy": "profit",
        "threshold": 0.115,
        "near_threshold_band": 0.02,
        "prob_default": 0.2,
        "threshold_delta": 0.085,
        "risk_class": "High",
        "raw_input": valid_payload,
        "engineered": {},
        "top_local_shap": [{
            "feature": "FICO Score",
            "applicant_value": 750,
            "percentile": 80,
            "direction": "↓ risk",
            "magnitude": "High"
        }]
    }

    result = generate_explanation(fake_bundle, retries=1)
    assert "Explanation unavailable" in result["narrative"]