"""
app.py — AtliQ Technologies HR Analytics
Main entry point: handles auth routing → dashboard
"""

import hashlib
import json
import os
import streamlit as st

from data_loader import load_data, VERSION
from dashboard import show_dashboard

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HR Analytics · AtliQ Technologies",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

    /* Tab strip */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #f8fafc;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-size: 12.5px;
        font-weight: 500;
        padding: 6px 14px;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 1px 4px rgba(0,0,0,.08);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 13px;
    }
    .stButton > button[kind="primary"] {
        background: #1d4ed8;
        border-color: #1d4ed8;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Auth helpers ─────────────────────────────────────────────────────────────
USERS_FILE = "users.json"

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}

def _save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# ── Session defaults ─────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "auth_tab" not in st.session_state:
    st.session_state.auth_tab = "login"

# ── Auth screen ──────────────────────────────────────────────────────────────
def show_auth():
    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align:center;padding:32px 0 24px;">
              <div style="font-size:44px;">📊</div>
              <h1 style="margin:8px 0 4px;font-size:24px;font-weight:700;color:#0f172a;">
                HR Analytics
              </h1>
              <p style="margin:0;font-size:14px;color:#64748b;">
                AtliQ Technologies · Workforce Intelligence
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            uname = st.text_input("Username", key="li_user", placeholder="Enter your username")
            pw    = st.text_input("Password", type="password", key="li_pw",
                                  placeholder="Enter your password")
            if st.button("Sign In →", type="primary", use_container_width=True, key="li_btn"):
                users = _load_users()
                if uname in users and users[uname] == _hash(pw):
                    st.session_state.logged_in = True
                    st.session_state.username  = uname
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")

        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            new_u  = st.text_input("Choose username", key="su_user",
                                   placeholder="e.g. hr_manager")
            new_p  = st.text_input("Choose password", type="password", key="su_pw",
                                   placeholder="Minimum 6 characters")
            new_p2 = st.text_input("Confirm password", type="password", key="su_pw2",
                                   placeholder="Re-enter password")
            if st.button("Create Account", type="primary", use_container_width=True, key="su_btn"):
                if not new_u.strip():
                    st.error("Username cannot be empty.")
                elif len(new_p) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_p != new_p2:
                    st.error("Passwords do not match.")
                else:
                    users = _load_users()
                    if new_u in users:
                        st.error("Username already exists. Please choose another.")
                    else:
                        users[new_u] = _hash(new_p)
                        _save_users(users)
                        st.success("Account created! Please sign in.")

        st.markdown(
            """
            <p style="text-align:center;font-size:12px;color:#94a3b8;margin-top:24px;">
              🔒 Session-secured · SHA-256 authentication
            </p>
            """,
            unsafe_allow_html=True,
        )

# ── App header (shown when logged in) ───────────────────────────────────────
def show_header():
    col_l, col_r = st.columns([5, 1])
    with col_l:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:12px;padding:4px 0 16px;">
              <span style="font-size:28px;">📊</span>
              <div>
                <h1 style="margin:0;font-size:22px;font-weight:700;color:#0f172a;line-height:1.2;">
                  HR Analytics Dashboard
                </h1>
                <p style="margin:0;font-size:13px;color:#64748b;">
                  AtliQ Technologies · Apr–Jun 2022 · Welcome, <strong>{st.session_state.username}</strong>
                </p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_r:
        if st.button("Sign Out", key="signout"):
            st.session_state.logged_in = False
            st.session_state.username  = ""
            st.rerun()

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.logged_in:
        show_auth()
        return

    show_header()

    with st.spinner("Loading attendance data…"):
        df_long, emp_metrics = load_data(VERSION)

    if df_long is None:
        st.error(
            "**Attendance Sheet.xlsx not found.**  \n"
            "Place the file in the same directory as app.py and restart the app."
        )
        return

    show_dashboard(df_long, emp_metrics)

if __name__ == "__main__":
    main()
