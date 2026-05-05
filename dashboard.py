import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from new_tabs import render_leave_breakdown, render_absenteeism_alerts, render_monthly_trends
from insights import render_ai_insights
from data_loader import load_attendance

# ── Path to your Excel file (same folder as app.py) ───────────────────────────
DATA_FILE = "Attendance_Sheet_2022-2023_Masked.xlsx"


def show_dashboard():
    """Called from app.py with no arguments — loads data internally."""

    # ── Load Data ──────────────────────────────────────────────────────────────
    df = load_attendance(DATA_FILE)

    if df.empty:
        st.error("❌ Could not load attendance data. Check that the Excel file is in the project folder.")
        return

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🏢 AtliQ HR Analytics")
        st.caption("Apr – Jun 2022")
        st.divider()

        months = sorted(df["Month"].unique())
        sel_months = st.multiselect("Filter by Month", months, default=months)
        st.divider()

        st.markdown("**Quick Stats**")
        st.metric("Total Employees", df["Employee Code"].nunique())
        st.metric("Total Records", len(df))
        st.divider()

        if st.button("🚪 Logout", width='stretch'):
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()

    # Apply month filter
    if sel_months:
        df = df[df["Month"].isin(sel_months)]

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "📈 Overview",
        "👤 Employee Deep-Dive",
        "🗺️ Heatmap",
        "📊 Leave Breakdown",
        "🚨 Absenteeism Alerts",
        "📅 Monthly Trends",
        "🤖 AI Insights",
        "📋 Raw Data",
    ])

    # ── TAB 0: Overview ────────────────────────────────────────────────────────
    with tabs[0]:
        st.header("📈 Company Overview")
        work_df = df[~df["Status"].isin(["WO", "HO"])]
        total = max(len(work_df), 1)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Attendance %",  f"{work_df['Status'].isin(['P']).sum() / total * 100:.1f}%")
        c2.metric("WFH %",         f"{work_df['Status'].isin(['WFH','HWFH']).sum() / total * 100:.1f}%")
        c3.metric("Sick Leave %",  f"{work_df['Status'].isin(['SL','HSL']).sum() / total * 100:.1f}%")
        c4.metric("Employees",     df["Employee Code"].nunique())

        if "Date" in df.columns:
            daily = (
                work_df.groupby("Date")
                .apply(lambda x: x["Status"].isin(["P"]).sum() / max(len(x), 1) * 100)
                .reset_index()
            )
            daily.columns = ["Date", "Attendance %"]
            fig = px.line(daily, x="Date", y="Attendance %",
                          title="Daily Attendance Trend",
                          color_discrete_sequence=["#6366f1"])
            fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width='stretch')

    # ── TAB 1: Employee Deep-Dive ──────────────────────────────────────────────
    with tabs[1]:
        st.header("👤 Employee Deep-Dive")
        selected_emp = st.selectbox("Select Employee", sorted(df["Name"].unique()))
        emp_df   = df[df["Name"] == selected_emp]
        work_emp = emp_df[~emp_df["Status"].isin(["WO", "HO"])]
        total_e  = max(len(work_emp), 1)

        c1, c2, c3 = st.columns(3)
        c1.metric("Attendance %", f"{work_emp['Status'].isin(['P']).sum() / total_e * 100:.1f}%")
        c2.metric("WFH %",        f"{work_emp['Status'].isin(['WFH']).sum() / total_e * 100:.1f}%")
        c3.metric("Sick Leave %", f"{work_emp['Status'].isin(['SL']).sum() / total_e * 100:.1f}%")

        status_counts = emp_df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig = px.pie(status_counts, names="Status", values="Count",
                     title=f"{selected_emp} — Status Distribution", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width='stretch')

    # ── TAB 2: Heatmap ────────────────────────────────────────────────────────
    with tabs[2]:
        st.header("🗺️ Attendance Heatmap")
        if "Date" in df.columns:
            pivot = (
                df[df["Status"] == "P"]
                .groupby(["Name", "Date"])
                .size()
                .unstack(fill_value=0)
            )
            fig = px.imshow(pivot, color_continuous_scale="Blues",
                            title="Attendance Heatmap (Blue = Present)", aspect="auto")
            fig.update_layout(height=600, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Date column not found — check data_loader.py")

    # ── TAB 3: Leave Breakdown (NEW) ───────────────────────────────────────────
    with tabs[3]:
        render_leave_breakdown(df)

    # ── TAB 4: Absenteeism Alerts (NEW) ───────────────────────────────────────
    with tabs[4]:
        render_absenteeism_alerts(df)

    # ── TAB 5: Monthly Trends (NEW) ───────────────────────────────────────────
    with tabs[5]:
        render_monthly_trends(df)

    # ── TAB 6: AI Insights (NEW) ──────────────────────────────────────────────
    with tabs[6]:
        render_ai_insights(df)

    # ── TAB 7: Raw Data ───────────────────────────────────────────────────────
    with tabs[7]:
        st.header("📋 Raw Attendance Data")
        st.dataframe(df, width='stretch', hide_index=True)
        st.download_button(
            "📥 Download CSV",
            data=df.to_csv(index=False),
            file_name="attendance_data.csv",
            mime="text/csv",
        )
