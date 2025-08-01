import os
import time
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st

API_URL = os.getenv("AURA_API_URL", "http://localhost:8000").rstrip("/")
SHOW_DEBUG = os.getenv("SHOW_DEBUG", "false").lower() == "true" 

st.set_page_config(
    page_title="AURA - Autonomous Risk Assessment",
    page_icon="💳",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={"About": "AURA - Autonomous Risk Assessment\n\n"}
)

st.markdown("""
<style>
/* Center the main title and captions */
h1, .stMarkdown h1 { text-align: center; }
div[data-testid="stCaptionContainer"] p { text-align: center; }

/* Card feel for the form */
.block-container { padding-top: 1.2rem; }
div[data-testid="stForm"] { border: 1px solid #e9ecef; border-radius: 12px; padding: 1rem 1rem 0.5rem; }
div[data-testid="stMetricValue"] { font-weight: 700; }

/* Buttons */
button[kind="primary"] { border-radius: 10px; }

/* Compact health chip in top-right corner */
.health-chip {
  position: fixed;
  bottom: 16px;            
  right: 16px;
  z-index: 2147483647;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.80rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  opacity: 0.95;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  pointer-events: none;
}
.health-chip.ok  { background:#e8f7ee; color:#0a7f42; border:1px solid #cceedd; }
.health-chip.err { background:#fdecec; color:#a41020; border:1px solid #f5c2c7; }
.health-chip .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
.health-chip.ok  .dot { background:#0a7f42; }
.health-chip.err .dot { background:#a41020; }
</style>
""", unsafe_allow_html=True)

st.title("AURA - Autonomous Risk Assessment")
st.caption("Enter loan application details below to generate a risk assessment with an explanatory narrative.")


def check_health(api_base: str, timeout_s: float = 2.0):
    url = f"{api_base}/health"
    t0 = time.perf_counter()
    try:
        r = requests.get(url, timeout=timeout_s)
        elapsed = time.perf_counter() - t0
        ok = (200 <= r.status_code < 300)
        return ok, r.status_code, elapsed, (r.text or "")
    except requests.exceptions.RequestException as e:
        elapsed = time.perf_counter() - t0
        return False, None, elapsed, str(e)

ok, status, h_latency, detail = check_health(API_URL)
st.markdown(
    f'''
    <div class="health-chip {'ok' if ok else 'err'}" title="API Health · Latency {h_latency:.2f}s">
      <span class="dot"></span>
      {'API OK' if ok else 'API DOWN'} · {h_latency:.2f}s
    </div>
    ''',
    unsafe_allow_html=True
)
if not ok and SHOW_DEBUG:
    with st.expander("Health details (debug)"):
        st.code(detail if isinstance(detail, str) else json.dumps(detail, indent=2))

with st.form("inputs"):
    c1, c2 = st.columns(2)
    with c1:
        grade = st.selectbox(
            "Loan Grade *",
            list("ABCDEFG"),
            index=None,
            placeholder="Select a loan grade",
            help="Letter grade assigned at origination."
        )
        acc_open_s = st.text_input(
            "Accounts opened (24m) *",
            placeholder="ex: 2",
            help="Must be a non-negative integer."
        )
        fico_s = st.text_input(
            "FICO Score *",
            placeholder="300–850",
            help="Integer between 300 and 850."
        )
    with c2:
        term = st.selectbox(
            "Loan Term (months) *",
            [36, 60],
            index=None,
            placeholder="Select a term",
            help="Commonly 36 or 60 months."
        )
        dti_s = st.text_input(
            "Debt-to-Income Ratio (%) *",
            placeholder="ex: 15.0",
            help="Non-negative number. Do not include the % sign."
        )
    run = st.form_submit_button("Run Assessment")

def to_int(s):
    s = (s or "").strip()
    try: return int(s)
    except: return None

def to_float(s):
    s = (s or "").strip()
    try: return float(s)
    except: return None

def new_session():
    sess = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.3, status_forcelist=[502, 503, 504]))
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    return sess

if run:
    errors = []
    if grade is None: errors.append("Loan Grade is required.")
    if term is None:  errors.append("Loan Term is required.")
    acc_open = to_int(acc_open_s)
    dti = to_float(dti_s)
    fico = to_int(fico_s)
    if acc_open is None or acc_open < 0: errors.append("Accounts opened must be a non-negative integer.")
    if dti is None or dti < 0: errors.append("Debt-to-Income must be a non-negative number.")
    if fico is None or not (300 <= fico <= 850): errors.append("FICO must be 300–850.")
    if errors:
        for e in errors: st.error(e)
        st.stop()

    payload = {
        "grade": grade,
        "term": term,
        "acc_open_past_24mths": acc_open,
        "dti": dti,
        "fico_mid": fico
    }

    s = new_session()
    t0 = time.perf_counter()
    try:
        with st.spinner("Scoring and generating explanation…"):
            r = s.post(f"{API_URL}/predict_explain", json=payload, timeout=(5, 60))
        elapsed = time.perf_counter() - t0

        if r.status_code == 400:
            detail = r.json().get("detail", r.text)
            st.error(f"Input error: {detail}")
            st.caption(f"Response: {elapsed:.2f}s"); st.stop()
        if r.status_code == 429:
            st.error("Rate limit exceeded. Please wait and try again.")
            st.caption(f"Response: {elapsed:.2f}s"); st.stop()
        if not (200 <= r.status_code < 300):
            st.error(f"API error: {r.status_code} - {r.text}")
            st.caption(f"Response: {elapsed:.2f}s"); st.stop()

        try:
            data = r.json()
        except ValueError:
            st.error("API returned non-JSON response.")
            st.caption(f"Response: {elapsed:.2f}s"); st.stop()

        pred = data.get("prediction")
        expl = (data.get("explanation") or {})
        exp = expl.get("narrative")
        if not pred:
            st.error("API response missing 'prediction'."); st.stop()

        st.caption(f"Response time: {elapsed:.2f}s")

        st.subheader("Risk Assessment")
        m1, m2, m3 = st.columns(3)
        m1.metric("Probability of Default", f"{pred['prob_default']:.2%}")
        m2.metric("Threshold", f"{pred['threshold']:.2%}")
        m3.metric("Δ vs Threshold", f"{pred['threshold_delta']:.2%}")
        st.caption(f"Near-threshold: **{pred['near_threshold_flag']}**  ·  Policy: **{pred['threshold_policy']}**")

        st.subheader("Explanation")
        if exp:
            st.markdown(exp)
            st.download_button("Download Narrative (TXT)", data=exp, file_name="explanation.txt", mime="text/plain")
        else:
            st.warning("Explanation unavailable. Review the risk metrics above.")

        if SHOW_DEBUG:
            with st.expander("Debug details"):
                st.subheader("Payload")
                st.json(payload)
                st.subheader("Raw Response")
                st.json(data)

    except requests.exceptions.ConnectTimeout:
        st.error("Connection timed out while contacting the API.")
    except requests.exceptions.ReadTimeout:
        st.error("The API took too long to respond. Try again.")
    except requests.exceptions.RequestException as e:
        if os.getenv("ENABLE_LOCAL_FALLBACK", "false").lower() == "true":
            st.warning(f"API not reachable ({e.__class__.__name__}). Falling back to local demo.")
            try:
                from aura.models.predict import predict_with_explanations
                from aura.explain.explainer import generate_explanation
                bundle = predict_with_explanations(payload)
                exp = generate_explanation(bundle)["narrative"]
                m1, m2, m3 = st.columns(3)
                m1.metric("Probability of Default", f"{bundle['prob_default']:.2%}")
                m2.metric("Threshold", f"{bundle['threshold']:.2%}")
                m3.metric("Δ vs Threshold", f"{bundle['threshold_delta']:.2%}")
                st.caption(f"Risk Class: **{bundle['risk_class']}**")
                st.subheader("Narrative Explanation (Local)")
                st.write(exp)
            except Exception as e2:
                st.error(f"Local fallback failed: {e2}")
        else:
            st.error(f"Network error: {e.__class__.__name__}: {e}")