import os
import requests
import streamlit as st

API_URL = os.getenv("AURA_API_URL", "http://localhost:8000")

st.set_page_config(page_title="AURA - Autonomous Credit Risk Assessment", page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "AURA - Autonomous Credit Risk Assessment\n\n"})

st.title("AURA - Autonomous Credit Risk Assessment")

with st.form("inputs"):
    grade = st.selectbox("Loan Grade", list("ABCDEFG"), index=1)
    term = st.selectbox("Loan Term (months)", [36, 60], index=0)
    acc_open = st.number_input("Accounts opened (24m)", min_value=0, value=2, step=1)
    dti = st.number_input("Debt-to-Income Ratio (%)", min_value=0.0, value=15.0, step=0.1)
    fico = st.number_input("FICO Score", min_value=300, max_value=850, value=720, step=1)
    run = st.form_submit_button("Run Assessment")

if run:
    payload = {
        "grade": grade,
        "term": term,
        "acc_open_past_24mths": acc_open,
        "dti": dti,
        "fico_mid": fico
    }
    try:
        r = requests.post(f"{API_URL}/predict_explain", json=payload, timeout=20)
        if r.status_code != 200:
            st.error(f"API error: {r.status_code} - {r.text}")
        else:
            data = r.json()
            pred = data["prediction"]
            exp = data["explanation"]["narrative"]

            st.subheader("Risk Assessment")
            st.write(f"**Probability of Default:** {pred['prob_default']:.2%}")
            st.write(f"**Threshold:** {pred['threshold']:.2%}  (policy={pred['threshold_policy']})")
            st.write(f"**Delta:** {pred['threshold_delta']:.2%}")
            st.write(f"**Risk Class:** {pred['risk_class']}")
            st.write(f"**Near Threshold:** {pred['near_threshold_flag']}")

            st.subheader("Explanation")
            st.write(exp)

            st.download_button(
                "Download Narrative",
                data=exp,
                file_name="explanation.txt",
                mime="text/plain"
            )

    except requests.exceptions.RequestException:
        st.warning("API not reachable. Falling back to local model (demo mode).")
        try:
            from aura.models.predict import predict_with_explanations
            from aura.explain.explainer import generate_explanation
            cleaned = payload  
            bundle = predict_with_explanations(cleaned)
            exp = generate_explanation(bundle)["narrative"]

            st.write(f"**Probability of Default:** {bundle['prob_default']:.2%}")
            st.write(f"**Threshold:** {bundle['threshold']:.2%}")
            st.write(f"**Delta:** {bundle['threshold_delta']:.2%}")
            st.write(f"**Risk Class:** {bundle['risk_class']}")

            st.subheader("Narrative Explanation")
            st.write(exp)
        except Exception as e:
            st.error(f"Local fallback failed: {e}")