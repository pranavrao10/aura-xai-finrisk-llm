from aura.models.predict import predict_with_explanations

def test_predict_with_mock_model(valid_payload, mock_model, mock_explainer):
    out = predict_with_explanations(valid_payload, max_reasons=3)
    for k in ["prob_default", "risk_class", "top_local_shap"]:
        assert k in out
    assert isinstance(out["prob_default"], float)
    assert len(out["top_local_shap"]) == 1