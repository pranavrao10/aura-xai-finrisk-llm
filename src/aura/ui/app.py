import os, time, json, uuid, requests
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
)

st.markdown("""
<style>
h1, .stMarkdown h1 { text-align:center; }
div[data-testid="stCaptionContainer"] p{ text-align:center; }

.block-container{ padding-top:1.2rem; max-width:900px; margin:auto; }
@media(max-width:640px){ div[data-testid="stForm"]{ padding:0.75rem;} }

div[data-testid="stForm"]{border:1px solid #e9ecef;border-radius:12px;padding:1rem 1rem 0.5rem;}
div[data-testid="stMetricValue"]{font-weight:700;} button[kind="primary"]{border-radius:10px;}

.health-chip{position:fixed;bottom:16px;right:16px;z-index:2147483647;
  padding:6px 10px;border-radius:999px;font-size:0.80rem;font-weight:600;display:inline-flex;gap:6px;
  opacity:.95;box-shadow:0 2px 6px rgba(0,0,0,.15);pointer-events:none;}
.health-chip.ok {background:#e8f7ee;color:#0a7f42;border:1px solid #cceedd;}
.health-chip.err{background:#fdecec;color:#a41020;border:1px solid #f5c2c7;}
.health-chip .dot{width:8px;height:8px;border-radius:50%;display:inline-block;}
.health-chip.ok  .dot{background:#0a7f42;} .health-chip.err .dot{background:#a41020;}

.pill{display:inline-block;padding:4px 10px;border-radius:999px;font-size:.85rem;font-weight:600;}
.pill.low{background:#e8f7ee;color:#0a7f42;border:1px solid #cceedd;}
.pill.medium{background:#fff4e5;color:#8a4b00;border:1px solid #ffd8a8;}
.pill.high{background:#fdecec;color:#a41020;border:1px solid #f5c2c7;}
</style>
""", unsafe_allow_html=True)

st.title("AURA - Autonomous Risk Assessment")
st.caption("Enter loan application details below to generate a risk assessment with an explanatory narrative.")

def check_health(api: str, timeout: float = 2):
    start = time.perf_counter()
    try:
        r = requests.get(f"{api}/health", timeout=timeout)
        return (200 <= r.status_code < 300), r.status_code, time.perf_counter()-start, r.text
    except requests.exceptions.RequestException as e:
        return False, None, time.perf_counter()-start, str(e)

@st.cache_data(ttl=15)
def cached_health(api: str):
    return check_health(api)

def build_retry():
    try:
        return Retry(total=3, backoff_factor=0.3,
                     status_forcelist=[502,503,504],
                     allowed_methods=frozenset({"GET","POST","PUT","DELETE","OPTIONS","HEAD","PATCH"}))
    except TypeError:                   
        return Retry(total=3, backoff_factor=0.3,
                     status_forcelist=[502,503,504],
                     method_whitelist=frozenset({"GET","POST","PUT","DELETE","OPTIONS","HEAD","PATCH"}))

@st.cache_resource
def get_session():
    s = requests.Session()
    adapter = HTTPAdapter(max_retries=build_retry())
    s.mount("https://", adapter); s.mount("http://", adapter)
    return s

def render_chip(ok: bool, latency: float):
    html = (
        "<div class='health-chip ok'><span class='dot'></span></div>"
        if ok else
        f"<div class='health-chip err' title='API DOWN · {latency:.2f}s'><span class='dot'></span> API DOWN</div>"
    )
    chip_slot.markdown(html, unsafe_allow_html=True)

def start_submit():
    st.session_state.submitting = True
    st.session_state.should_run = True

def halt():
    st.session_state.submitting = False
    st.session_state.should_run = False
    st.stop()

def save_and_rerun(result_dict: dict):
    st.session_state["last_result"] = result_dict
    st.session_state.submitting = False
    st.session_state.just_finished = True
    st.rerun()

to_int = lambda s: int(s)   if (s:=s.strip()) else None
to_float = lambda s: float(s) if (s:=s.strip()) else None


if "submitting" not in st.session_state: st.session_state.submitting = False
if "should_run" not in st.session_state: st.session_state.should_run = False
if "form_key" not in st.session_state: st.session_state.form_key = "f_" + uuid.uuid4().hex
if "force_blank" in st.session_state:
    st.session_state.form_key = "f_" + uuid.uuid4().hex
    del st.session_state["force_blank"]

chip_slot = st.empty()
ok, _, lat, _ = cached_health(API_URL)
render_chip(ok, lat)

btn_label = "Running…" if st.session_state.submitting else "Run Assessment"
with st.form(key=st.session_state.form_key):
    c1, c2 = st.columns(2)
    grade = c1.selectbox("Loan Grade *", list("ABCDEFG"), index=None,
                          placeholder="Select a loan grade")
    acc_s  = c1.text_input("Accounts opened (24m) *", placeholder="ex: 2")
    fico_s = c1.text_input("FICO Score *", placeholder="300–850")

    term = c2.selectbox("Loan Term (months) *", [36, 60], index=None,
                          placeholder="Select a term")
    dti_s = c2.text_input("Debt-to-Income Ratio (%) *", placeholder="ex: 15.0")

    st.form_submit_button(btn_label, on_click=start_submit,
                          disabled=st.session_state.submitting)

if st.button("Reset form", key="reset_top"):
    st.session_state.clear()
    st.session_state["force_blank"] = True
    st.rerun()

if st.session_state.get("last_result") and st.session_state.get("just_finished"):
    res = st.session_state["last_result"]
    st.session_state.just_finished = False 

    pd, thr, delta = res["pd"], res["thr"], res["delta"]
    policy, near = res["policy"], res["near"]
    pred_rc = res["rc"]

    st.subheader("Risk Assessment")
    c1,c2,c3 = st.columns(3)
    c1.metric("Probability of Default", f"{pd:.2%}")
    c2.metric("Threshold", f"{thr:.2%}")
    c3.metric("Δ vs Threshold", f"{delta:.2%}")

    rc_map={"low":"low","medium":"medium","moderate":"medium","high":"high"}
    st.markdown(
        f"**Risk Class:** "
        f"<span class='pill {rc_map.get(pred_rc,'medium')}'>{pred_rc.title()}</span>",
        unsafe_allow_html=True
    )
    if near:
        st.info("Applicant is near the policy threshold — consider manual review.")
    st.caption(f"Policy: **{policy}** · Near-threshold: **{near}**")

    st.subheader("Explanation")
    exp = res["exp"]
    if exp:
        st.markdown(exp)
        st.download_button("Download Narrative (TXT)", exp,
                           file_name="explanation.txt", mime="text/plain")

if st.session_state.should_run:
    st.session_state.should_run = False

    errors=[]
    if grade is None: errors.append("Loan Grade is required.")
    if term is None: errors.append("Loan Term is required.")
    acc = to_int(acc_s or "")
    dti = to_float(dti_s or "")
    fico = to_int(fico_s or "")
    if acc is None or acc<0: errors.append("Accounts opened must be non-negative integer.")
    if dti is None or dti<0:errors.append("Debt-to-Income must be non-negative number.")
    if fico is None or not 300<=fico<=850: errors.append("FICO must be 300–850.")
    if errors:
        for e in errors: st.error(e)
        halt()

    payload = {"grade":grade,"term":term,
               "acc_open_past_24mths":acc,"dti":dti,"fico_mid":fico}

    sess = get_session()
    rid = uuid.uuid4().hex
    t0 = time.perf_counter()
    try:
        with st.spinner("Scoring and generating explanation…"):
            r = sess.post(f"{API_URL}/predict_explain",
                          json=payload, headers={"X-Request-ID":rid},
                          timeout=(5,60))
        elapsed = time.perf_counter()-t0

        if r.status_code==400:
            st.error(f"Input error: {r.json().get('detail',r.text)}"); halt()
        if r.status_code==429:
            st.error("Rate limit exceeded. Try again."); halt()
        if not (200<=r.status_code<300):
            st.error(f"API error {r.status_code}: {r.text[:800]}"); halt()

        data = r.json()
        pred = data.get("prediction")
        exp = (data.get("explanation") or {}).get("narrative")
        if not pred: st.error("API response missing 'prediction'."); halt()

        pd = float(pred["prob_default"])
        thr = float(pred["threshold"])
        delta = float(pred["threshold_delta"])
        policy= pred["threshold_policy"]
        near = bool(pred["near_threshold_flag"])
        rc = pred["risk_class"].lower()

        save_and_rerun({
            "pred":pred,"exp":exp,
            "pd":pd,"thr":thr,"delta":delta,
            "policy":policy,"near":near,"rc":rc
        })

    except requests.exceptions.ConnectTimeout:
        st.error("Connection timed out."); halt()
    except requests.exceptions.ReadTimeout:
        st.error("API took too long.");   halt()
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {e}");  halt()