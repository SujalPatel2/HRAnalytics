import streamlit as st
from auth import login_page, signup_page
from dashboard import show_dashboard

st.set_page_config(
    page_title="AtliQ HR Analytics",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom Global CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit chrome on auth pages */
.auth-mode header, .auth-mode footer { display: none !important; }

/* Metric cards */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}
div[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #f8fafc !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stSelectbox label { color: #94a3b8 !important; }

/* Tabs */
div[data-testid="stTabs"] button {
    font-weight: 500;
    border-radius: 8px 8px 0 0;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom: 2px solid #6366f1 !important;
}

/* DataFrames */
div[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #334155;
}

/* Main background */
.main { background: #0f172a; }
.block-container { padding-top: 1rem; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1e293b; }
::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ─────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "login"

# ── Router ─────────────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard()
else:
    if st.session_state.page == "login":
        login_page()
    else:
        signup_page()
