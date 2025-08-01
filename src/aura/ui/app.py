import os
import requests
import streamlit as st

API_URL = os.getenv("AURA_API_URL", "http://localhost:8000")

st.set_page_config(page_title="AURA - Autonomous Risk Assessment", page_icon="💳",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={"About": "AURA - Autonomous Risk Assessment\n\n"})

st.title("AURA - Autonomous Risk Assessment")

with st.form("inputs"):
    grade = st.selectbox("Loan Grade", list("ABCDEFG"), index=None, placeholder="Select a grade")
    term = st.selectbox("Loan Term (months)", [36, 60], index=None, placeholder="Select a term")
    acc_open_s = st.text_input("Accounts opened (24m)", placeholder="ex: 2")
    dti_s = st.text_input("Debt-to-Income Ratio (%)", placeholder="ex: 15.0")
    fico_s = st.text_input("FICO Score", placeholder="300–850")
    def to_int(s):
        try: return int(s)
        except: return None
    def to_float(s):
        try: return float(s)
        except: return None

    acc_open = to_int(acc_open_s)
    dti = to_float(dti_s)
    fico = to_int(fico_s)

    valid = (
        grade is not None and term is not None and
        acc_open is not None and acc_open >= 0 and
        dti is not None and dti >= 0 and
        fico is not None and 300 <= fico <= 850
    )

    run = st.form_submit_button("Run Assessment", disabled=not valid)

if run:
    payload = {
        "grade": grade,
        "term": term,
        "acc_open_past_24mths": acc_open,
        "dti": dti,
        "fico_mid": fico
    }
    try:
        r = requests.post(f"{API_URL}/predict_explain", json=payload, timeout=60)
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
            st.markdown(exp)

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