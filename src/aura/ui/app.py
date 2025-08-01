import os
import time
import json
import uuid
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
h1, .stMarkdown h1 { text-align: center; }
div[data-testid="stCaptionContainer"] p { text-align: center; }

/* Max width + mobile spacing (polish) */
.block-container { padding-top: 1.2rem; max-width: 900px; margin: auto; }
@media (max-width: 640px){
  div[data-testid="stForm"] { padding: 0.75rem; }
}

/* Card feel for the form */
div[data-testid="stForm"] { border: 1px solid #e9ecef; border-radius: 12px; padding: 1rem 1rem 0.5rem; }
div[data-testid="stMetricValue"] { font-weight: 700; }
button[kind="primary"] { border-radius: 10px; }

/* Health chip (bottom-right) */
.health-chip {
  position: fixed; bottom: 16px; right: 16px; z-index: 2147483647;
  padding: 6px 10px; border-radius: 999px; font-size: 0.80rem; font-weight: 600;
  display: inline-flex; align-items: center; gap: 6px; opacity: 0.95;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15); pointer-events: none;
}
.health-chip.ok  { background:#e8f7ee; color:#0a7f42; border:1px solid #cceedd; }
.health-chip.err { background:#fdecec; color:#a41020; border:1px solid #f5c2c7; }
.health-chip .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
.health-chip.ok  .dot { background:#0a7f42; }
.health-chip.err .dot { background:#a41020; }

/* Risk class pill */
.pill { display:inline-block; padding:4px 10px; border-radius:999px; font-size:0.85rem; font-weight:600; }
.pill.low    { background:#e8f7ee; color:#0a7f42; border:1px solid #cceedd; }
.pill.medium { background:#fff4e5; color:#8a4b00; border:1px solid #ffd8a8; }
.pill.high   { background:#fdecec; color:#a41020; border:1px solid #f5c2c7; }
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

@st.cache_data(ttl=15)
def cached_health(url: str):
    return check_health(url)

ok, status, h_latency, detail = cached_health(API_URL)
chip = (f"<div class='health-chip ok'><span class='dot'></span></div>"
        if ok else
        f"<div class='health-chip err' title='API DOWN · {h_latency:.2f}s'><span class='dot'></span> API DOWN</div>")
st.markdown(chip, unsafe_allow_html=True)
if not ok and SHOW_DEBUG:
    with st.expander("Health details (debug)"):
        st.code(detail if isinstance(detail, str) else json.dumps(detail, indent=2))

def build_retry():
    try:
        return Retry(
            total=3, backoff_factor=0.3,
            status_forcelist=[502, 503, 504],
            allowed_methods=frozenset({"GET","POST","PUT","DELETE","OPTIONS","HEAD","PATCH"})
        )
    except TypeError:
        return Retry(
            total=3, backoff_factor=0.3,
            status_forcelist=[502, 503, 504],
            method_whitelist=frozenset({"GET","POST","PUT","DELETE","OPTIONS","HEAD","PATCH"})
        )

@st.cache_resource
def get_session():
    s = requests.Session()
    adapter = HTTPAdapter(max_retries=build_retry())
    s.mount("https://", adapter); s.mount("http://", adapter)
    return s

def qp_get():
    try:
        return dict(st.query_params)
    except Exception:
        return {}

params = qp_get()
def qp(val_list, cast=str, default=None):
    if not val_list: return default
    try:
        return cast(val_list[0]) if isinstance(val_list, list) else cast(val_list)
    except Exception:
        return default

grade_q = qp(params.get("grade"), str, None)
term_q = qp(params.get("term"), int, None)
acc_q = qp(params.get("acc"), str, None)
dti_q = qp(params.get("dti"), str, None)
fico_q = qp(params.get("fico"), str, None)

if "submitting" not in st.session_state:
    st.session_state.submitting = False
if "should_run" not in st.session_state:
    st.session_state.should_run = False

def start_submit():
    st.session_state.submitting = True
    st.session_state.should_run = True

def halt():
    st.session_state.submitting = False
    st.session_state.should_run = False
    st.stop()

GRADE_KEY = "grade_in"; TERM_KEY = "term_in"; ACC_KEY = "acc_in"; DTI_KEY = "dti_in"; FICO_KEY = "fico_in"
if grade_q and GRADE_KEY not in st.session_state: st.session_state[GRADE_KEY] = grade_q
if term_q and TERM_KEY not in st.session_state: st.session_state[TERM_KEY] = term_q
if acc_q and ACC_KEY not in st.session_state: st.session_state[ACC_KEY] = acc_q
if dti_q and DTI_KEY not in st.session_state: st.session_state[DTI_KEY] = dti_q
if fico_q and FICO_KEY not in st.session_state: st.session_state[FICO_KEY] = fico_q

btn_label = "Running…" if st.session_state.submitting else "Run Assessment"

with st.form("inputs"):
    c1, c2 = st.columns(2)
    with c1:
        grade = st.selectbox("Loan Grade *", list("ABCDEFG"), index=None,
                             placeholder="Select a loan grade",
                             help="Letter grade assigned at origination.",
                             key=GRADE_KEY)
        acc_open_s = st.text_input("Accounts opened (24m) *", placeholder="ex: 2",
                                   help="Must be a non-negative integer.", key=ACC_KEY)
        fico_s = st.text_input("FICO Score *", placeholder="300–850",
                               help="Integer between 300 and 850.", key=FICO_KEY)
    with c2:
        term = st.selectbox("Loan Term (months) *", [36, 60], index=None,
                            placeholder="Select a term", help="Commonly 36 or 60 months.",
                            key=TERM_KEY)
        dti_s = st.text_input("Debt-to-Income Ratio (%) *", placeholder="ex: 15.0",
                              help="Non-negative number. Do not include the % sign.", key=DTI_KEY)

    st.form_submit_button(
        btn_label,
        on_click=start_submit,
        disabled=st.session_state.submitting
    )

def to_int(s):
    s = (s or "").strip()
    try: return int(s)
    except: return None

def to_float(s):
    s = (s or "").strip()
    try: return float(s)
    except: return None

if st.session_state.should_run:
    st.session_state.should_run = False
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
        halt()

    payload = {
        "grade": grade, "term": term,
        "acc_open_past_24mths": acc_open, "dti": dti, "fico_mid": fico
    }

    s = get_session()
    t0 = time.perf_counter()
    req_id = uuid.uuid4().hex
    headers = {"X-Request-ID": req_id}

    try:
        with st.spinner("Scoring and generating explanation…"):
            r = s.post(f"{API_URL}/predict_explain", json=payload, headers=headers, timeout=(5, 60))
        elapsed = time.perf_counter() - t0

        if r.status_code == 400:
            detail = r.json().get("detail", r.text)
            st.error(f"Input error: {detail}")
            if SHOW_DEBUG: st.caption(f"req_id: {req_id} · {int(elapsed*1000)} ms")
            st.caption(f"Response: {elapsed:.2f}s"); halt()
        if r.status_code == 429:
            st.error("Rate limit exceeded. Please wait and try again.")
            if SHOW_DEBUG: st.caption(f"req_id: {req_id} · {int(elapsed*1000)} ms")
            st.caption(f"Response: {elapsed:.2f}s"); halt()
        if not (200 <= r.status_code < 300):
            body = r.text if len(r.text) <= 800 else r.text[:800] + "…"
            st.error(f"API error: {r.status_code} - {body}")
            if SHOW_DEBUG: st.caption(f"req_id: {req_id} · {int(elapsed*1000)} ms")
            st.caption(f"Response: {elapsed:.2f}s"); halt()

        try:
            data = r.json()
        except ValueError:
            st.error("API returned non-JSON response.")
            if SHOW_DEBUG: st.caption(f"req_id: {req_id}")
            st.caption(f"Response: {elapsed:.2f}s"); halt()

        pred = data.get("prediction")
        expl = (data.get("explanation") or {})
        exp = expl.get("narrative")
        if not pred:
            st.error("API response missing 'prediction'.")
            if SHOW_DEBUG: st.caption(f"req_id: {req_id}")
            halt()

        try: st.toast("Results ready.")
        except Exception: pass

        st.caption(f"Response time: {elapsed:.2f}s")
        if SHOW_DEBUG: st.caption(f"req_id: {req_id}")

        pd = float(pred.get("prob_default", 0) or 0)
        thr = float(pred.get("threshold", 0) or 0)
        delta = float(pred.get("threshold_delta", pd - thr))
        policy = pred.get("threshold_policy", "—")
        near = bool(pred.get("near_threshold_flag", False))

        st.subheader("Risk Assessment")
        m1, m2, m3 = st.columns(3)
        m1.metric("Probability of Default", f"{pd:.2%}")
        m2.metric("Threshold", f"{thr:.2%}")
        m3.metric("Δ vs Threshold", f"{delta:.2%}")

        rc = str(pred.get("risk_class", "")).strip().lower()
        rc_map = {"low": "low", "medium": "medium", "moderate": "medium", "high": "high"}
        css_class = rc_map.get(rc, "medium")
        label = (pred.get("risk_class") or "Unknown").title()
        st.markdown(f"**Risk Class:** <span class='pill {css_class}'>{label}</span>", unsafe_allow_html=True)

        if near:
            st.info("Applicant is near the policy threshold — consider manual review or additional documentation.")

        st.caption(f"Policy: **{policy}**  ·  Near-threshold: **{near}**")

        st.subheader("Explanation")
        if exp:
            st.markdown(exp, unsafe_allow_html=False)

            cdl, cr = st.columns([3,1])
            with cdl:
                st.download_button("Download Narrative (TXT)", data=exp,
                                   file_name="explanation.txt", mime="text/plain")
            with cr:
                if st.button("Reset form"):
                    for k in [GRADE_KEY, TERM_KEY, ACC_KEY, DTI_KEY, FICO_KEY]:
                        if k in st.session_state: del st.session_state[k]
                    try:
                        st.query_params.clear()
                    except Exception:
                        pass
                    st.rerun()
        else:
            st.warning("Explanation unavailable. Review the risk metrics above.")

        if SHOW_DEBUG:
            with st.expander("Debug details"):
                st.subheader("Payload"); st.json(payload)
                st.subheader("Raw Response"); st.json(data)

    except requests.exceptions.ConnectTimeout:
        st.error("Connection timed out while contacting the API."); halt()
    except requests.exceptions.ReadTimeout:
        st.error("The API took too long to respond. Try again."); halt()
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
                st.markdown(f"**Risk Class:** <span class='pill {('low' if bundle['risk_class'].lower()=='low' else 'high')}'>"
                            f"{bundle['risk_class']}</span>", unsafe_allow_html=True)
                st.subheader("Narrative Explanation (Local)")
                st.write(exp)

                if st.button("Reset form"):
                    st.session_state.clear() 
                    try:
                        st.query_params.clear()
                    except Exception:
                        pass
                    st.rerun()
            except Exception as e2:
                st.error(f"Local fallback failed: {e2}"); halt()
        else:
            st.error(f"Network error: {e.__class__.__name__}: {e}"); halt()
    finally:
        st.session_state.submitting = False