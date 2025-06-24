import shap

def get_shap_values(model, X, feature_names=None, top_n=3)
    explainer = shap.Explainer(model)
    shap_values = explainer(X)
    if feature_names is None:
        eature_names = [f"feature_{i}" for i in range(X.shape[1])]
    shap_dict = dict(zip(feature_names, shap_values.values[0]))
    top_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:top_n]
    shap_top_factors = [(k, f"{v:+.2f}") for k, v in top_features]
    return shap_top_factors