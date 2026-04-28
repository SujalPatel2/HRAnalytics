import streamlit as st
import json
import hashlib
import os
from datetime import datetime

USERS_FILE = "users.json"

# ── Helpers ────────────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        default = {
            "admin": {
                "password": _hash("admin123"),
                "name": "Admin User",
                "role": "HR Manager",
                "created": str(datetime.now().date())
            }
        }
        _save_users(default)
        return default
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def _save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def authenticate(username: str, password: str) -> bool:
    users = _load_users()
    if username in users and users[username]["password"] == _hash(password):
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_name = users[username]["name"]
        st.session_state.user_role = users[username].get("role", "HR Staff")
        return True
    return False

def register(username: str, password: str, name: str, role: str) -> tuple[bool, str]:
    users = _load_users()
    if username in users:
        return False, "Username already exists."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not username.strip():
        return False, "Username cannot be empty."
    users[username] = {
        "password": _hash(password),
        "name": name,
        "role": role,
        "created": str(datetime.now().date())
    }
    _save_users(users)
    return True, "Account created successfully!"

# ── Auth Card CSS ──────────────────────────────────────────────────────────────
AUTH_CSS = """
<style>
body { background: #0f172a !important; }
.auth-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}
.auth-card {
    background: rgba(30, 41, 59, 0.9);
    backdrop-filter: blur(16px);
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 2.5rem 2rem;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 25px 50px rgba(0,0,0,0.5);
}
.auth-logo {
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: 0.25rem;
}
.auth-title {
    color: #f8fafc;
    font-size: 1.5rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.25rem;
}
.auth-sub {
    color: #64748b;
    font-size: 0.85rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.auth-divider {
    border: none;
    border-top: 1px solid #334155;
    margin: 1.2rem 0;
}
.auth-switch {
    color: #94a3b8;
    font-size: 0.82rem;
    text-align: center;
    margin-top: 1rem;
}
.stTextInput input {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
    padding: 0.6rem 0.9rem !important;
}
.stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}
.stTextInput label { color: #94a3b8 !important; font-size: 0.8rem !important; }
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    width: 100%;
    transition: all 0.2s;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}
.stSelectbox select, .stSelectbox > div > div {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
}
</style>
"""

# ── Login Page ─────────────────────────────────────────────────────────────────
def login_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    
    # Center column
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class="auth-logo">🏢</div>
        <div class="auth-title">AtliQ HR Analytics</div>
        <div class="auth-sub">Sign in to access your dashboard</div>
        <hr class="auth-divider">
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter your username", key="login_user")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
        
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("🔐  Sign In", key="login_btn", width='stretch'):
            if not username or not password:
                st.error("Please fill in all fields.")
            elif authenticate(username, password):
                st.success(f"Welcome back, {st.session_state.user_name}! 👋")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")
        
        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)
        st.markdown("""
        <div class="auth-switch">Don't have an account?</div>
        """, unsafe_allow_html=True)
        
        if st.button("✨  Create Account", key="goto_signup", width='stretch'):
            st.session_state.page = "signup"
            st.rerun()
        
        st.markdown("""
        <div style='text-align:center; color:#475569; font-size:0.72rem; margin-top:1.5rem;'>
            Default credentials: <code style='color:#6366f1'>admin</code> / <code style='color:#6366f1'>admin123</code>
        </div>
        """, unsafe_allow_html=True)

# ── Signup Page ────────────────────────────────────────────────────────────────
def signup_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class="auth-logo">✨</div>
        <div class="auth-title">Create Account</div>
        <div class="auth-sub">Join AtliQ HR Analytics</div>
        <hr class="auth-divider">
        """, unsafe_allow_html=True)
        
        full_name = st.text_input("Full Name", placeholder="e.g. Priya Sharma", key="su_name")
        username  = st.text_input("Username", placeholder="Choose a username", key="su_user")
        role      = st.selectbox("Role", ["HR Manager", "HR Analyst", "Team Lead", "HR Staff"], key="su_role")
        password  = st.text_input("Password", type="password", placeholder="Min. 6 characters", key="su_pass")
        confirm   = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="su_conf")
        
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        
        if st.button("🚀  Create Account", key="signup_btn", width='stretch'):
            if not all([full_name, username, password, confirm]):
                st.error("Please fill in all fields.")
            elif password != confirm:
                st.error("❌ Passwords do not match.")
            else:
                success, msg = register(username, password, full_name, role)
                if success:
                    st.success(f"✅ {msg} Please sign in.")
                    st.balloons()
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
        
        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)
        st.markdown('<div class="auth-switch">Already have an account?</div>', unsafe_allow_html=True)
        
        if st.button("← Back to Sign In", key="goto_login", width='stretch'):
            st.session_state.page = "login"
            st.rerun()
