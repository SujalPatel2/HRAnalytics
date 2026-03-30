import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_loader import (
    load_attendance_data, get_employee_summary,
    get_monthly_summary, get_daily_trend
)

# ── Plotly base theme ──────────────────────────────────────────────────────────
PLOT_BG  = "#0f172a"
PAPER_BG = "#0f172a"
GRID_CLR = "#1e293b"
TEXT_CLR = "#94a3b8"
FONT     = "Inter, sans-serif"

PALETTE = {
    "present": "#6366f1",
    "wfh":     "#22d3ee",
    "leave":   "#f59e0b",
    "off":     "#475569",
    "sick":    "#ef4444",
    "gradient":["#6366f1","#8b5cf6","#ec4899","#22d3ee","#10b981","#f59e0b"],
}

def _base_layout(**kwargs):
    return dict(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT, color=TEXT_CLR, size=12),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor=GRID_CLR, linecolor=GRID_CLR, zerolinecolor=GRID_CLR),
        yaxis=dict(gridcolor=GRID_CLR, linecolor=GRID_CLR, zerolinecolor=GRID_CLR),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_CLR)),
        **kwargs
    )


# ── Sidebar ────────────────────────────────────────────────────────────────────
def _sidebar(df: pd.DataFrame):
    with st.sidebar:
        # User info
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg,#6366f1,#8b5cf6);
            border-radius:12px; padding:1rem; margin-bottom:1rem; text-align:center;">
            <div style="font-size:2rem">👤</div>
            <div style="color:#fff; font-weight:700; font-size:1rem">
                {st.session_state.get('user_name','User')}
            </div>
            <div style="color:rgba(255,255,255,0.7); font-size:0.75rem">
                {st.session_state.get('user_role','HR Staff')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔍 Filters")
        
        months = ["All Months"] + sorted(df["month"].unique().tolist()) if not df.empty else ["All Months"]
        selected_month = st.selectbox("📅 Month", months)

        employees = ["All Employees"] + sorted(df["name"].unique().tolist()) if not df.empty else ["All Employees"]
        selected_emp = st.selectbox("👤 Employee", employees)

        st.markdown("---")
        st.markdown("""
        <div style='color:#475569; font-size:0.72rem; text-align:center;'>
            <b>Legend</b><br>
            🟢 P — Present<br>
            🔵 WFH — Work From Home<br>
            🟡 PL — Paid Leave<br>
            🔴 SL — Sick Leave<br>
            ⚫ WO — Weekly Off<br>
            ⚪ HO — Holiday
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 Logout", width="stretch"):
            for k in ["authenticated","username","user_name","user_role"]:
                st.session_state.pop(k, None)
            st.session_state.page = "login"
            st.rerun()

    return selected_month, selected_emp


# ── KPI Cards ──────────────────────────────────────────────────────────────────
def _kpi_row(df: pd.DataFrame, filtered_df: pd.DataFrame):
    working = filtered_df[~filtered_df["is_off"]]
    
    total_employees = filtered_df["name"].nunique()
    overall_att     = round(working["is_present"].mean() * 100, 1) if len(working) > 0 else 0
    wfh_pct         = round(working["is_wfh"].mean() * 100, 1)    if len(working) > 0 else 0
    leave_pct       = round(working["is_leave"].mean() * 100, 1)  if len(working) > 0 else 0
    total_days      = filtered_df["date"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👥 Employees",        total_employees)
    c2.metric("✅ Attendance Rate",   f"{overall_att}%",
              delta=f"{overall_att - 85:.1f}% vs target 85%",
              delta_color="normal")
    c3.metric("🏠 WFH Rate",          f"{wfh_pct}%")
    c4.metric("🏖️ Leave Rate",         f"{leave_pct}%")
    c5.metric("📅 Working Days",       total_days)


# ── Charts ─────────────────────────────────────────────────────────────────────
def _chart_monthly_trend(df: pd.DataFrame):
    monthly = get_monthly_summary(df)
    if monthly.empty:
        st.info("No monthly data available.")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month_year"], y=monthly["attendance_pct"],
        name="Attendance %", mode="lines+markers",
        line=dict(color=PALETTE["present"], width=3),
        marker=dict(size=8, color=PALETTE["present"]),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.15)"
    ))
    fig.add_trace(go.Scatter(
        x=monthly["month_year"], y=monthly["wfh_pct"],
        name="WFH %", mode="lines+markers",
        line=dict(color=PALETTE["wfh"], width=3),
        marker=dict(size=8, color=PALETTE["wfh"]),
        fill="tozeroy", fillcolor="rgba(34,211,238,0.1)"
    ))
    fig.add_hline(y=85, line_dash="dash", line_color="#f59e0b",
                  annotation_text="85% Target", annotation_font_color="#f59e0b")
    fig.update_layout(
        **_base_layout(title="Monthly Attendance & WFH Trend"),
        hovermode="x unified"
    )
    st.plotly_chart(fig, width="stretch")


def _chart_attendance_dist(df: pd.DataFrame):
    if df.empty:
        return
    working = df[~df["is_off"]]
    counts = working["category"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    
    fig = px.pie(
        counts, names="Category", values="Count",
        color_discrete_sequence=PALETTE["gradient"],
        hole=0.55
    )
    fig.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value} days (%{percent})<extra></extra>"
    )
    fig.update_layout(
        **_base_layout(title="Attendance Distribution"),
        showlegend=False,
        annotations=[dict(text="Days", x=0.5, y=0.5, font_size=14,
                          font_color=TEXT_CLR, showarrow=False)]
    )
    st.plotly_chart(fig, width="stretch")


def _chart_top_employees(df: pd.DataFrame):
    emp_summary = get_employee_summary(df)
    if emp_summary.empty:
        return

    top10 = emp_summary.nlargest(10, "attendance_pct")
    colors = [PALETTE["present"] if p >= 85 else "#f59e0b" if p >= 70 else "#ef4444"
              for p in top10["attendance_pct"]]
    
    fig = go.Figure(go.Bar(
        x=top10["attendance_pct"],
        y=top10["name"],
        orientation="h",
        marker_color=colors,
        text=[f"{p}%" for p in top10["attendance_pct"]],
        textposition="outside",
        textfont=dict(color=TEXT_CLR),
        hovertemplate="<b>%{y}</b><br>Attendance: %{x}%<extra></extra>"
    ))
    fig.update_layout(**_base_layout(title="Top 10 Employees — Attendance Rate"))
    fig.update_yaxes(gridcolor=GRID_CLR, linecolor=GRID_CLR, autorange="reversed")
    fig.update_xaxes(gridcolor=GRID_CLR, linecolor=GRID_CLR, range=[0, 110])
    st.plotly_chart(fig, width="stretch")


def _chart_wfh_trend(df: pd.DataFrame):
    emp_summary = get_employee_summary(df)
    if emp_summary.empty:
        return

    fig = px.scatter(
        emp_summary,
        x="attendance_pct", y="wfh_pct",
        size="total_days", color="attendance_pct",
        hover_name="name",
        hover_data={"attendance_pct": ":.1f", "wfh_pct": ":.1f", "total_days": True},
        color_continuous_scale=["#ef4444","#f59e0b","#6366f1"],
        title="Attendance vs WFH Rate per Employee"
    )
    fig.update_layout(
        **_base_layout(),
        coloraxis_showscale=False,
        xaxis_title="Attendance %",
        yaxis_title="WFH %",
    )
    st.plotly_chart(fig, width="stretch")


def _chart_leave_breakdown(df: pd.DataFrame):
    leave_df = df[df["is_leave"]]
    if leave_df.empty:
        st.info("No leave data.")
        return
    leave_counts = leave_df["category"].value_counts().reset_index()
    leave_counts.columns = ["Leave Type", "Days"]
    
    fig = px.bar(
        leave_counts, x="Leave Type", y="Days",
        color="Leave Type",
        color_discrete_sequence=PALETTE["gradient"],
        text="Days"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        **_base_layout(title="Leave Type Breakdown"),
        showlegend=False,
        xaxis_tickangle=-25
    )
    st.plotly_chart(fig, width="stretch")


def _chart_daily_heatmap(df: pd.DataFrame):
    if df.empty:
        return
    working = df[~df["is_off"]]
    if working.empty:
        return
    pivot = (
        working.groupby(["name","date"])["is_present"].mean().unstack(fill_value=0) * 100
    )
    # Limit to 20 employees for readability
    pivot = pivot.iloc[:20]
    
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c.date()) if hasattr(c,'date') else str(c) for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0,"#1e293b"],[0.5,"#6366f1"],[1,"#22d3ee"]],
        hoverongaps=False,
        hovertemplate="Employee: %{y}<br>Date: %{x}<br>Present: %{z:.0f}%<extra></extra>",
        colorbar=dict(title=dict(text="Present %", font=dict(color=TEXT_CLR)), tickfont=dict(color=TEXT_CLR))
    ))
    fig.update_layout(**_base_layout(title="Attendance Heatmap (per Employee per Day)"))
    fig.update_xaxes(gridcolor=GRID_CLR, tickangle=-45, tickfont=dict(size=9))
    fig.update_yaxes(gridcolor=GRID_CLR, tickfont=dict(size=9))
    st.plotly_chart(fig, width="stretch")


def _chart_day_of_week(df: pd.DataFrame):
    if df.empty:
        return
    working = df[~df["is_off"]]
    dow = (
        working.groupby("day_of_week")["is_present"]
        .mean().mul(100).round(1).reset_index()
    )
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow["day_of_week"] = pd.Categorical(dow["day_of_week"], categories=order, ordered=True)
    dow = dow.sort_values("day_of_week")
    
    fig = px.bar(
        dow, x="day_of_week", y="is_present",
        color="is_present",
        color_continuous_scale=["#ef4444","#f59e0b","#6366f1"],
        labels={"is_present":"Attendance %","day_of_week":"Day"},
        text=dow["is_present"].apply(lambda x: f"{x}%")
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        **_base_layout(title="Attendance by Day of Week"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, width="stretch")


def _employee_detail(df: pd.DataFrame, employee: str):
    emp_df = df[df["name"] == employee]
    if emp_df.empty:
        st.warning("No data for this employee.")
        return

    working = emp_df[~emp_df["is_off"]]
    total   = len(working)
    present = working["is_present"].sum()
    wfh     = working["is_wfh"].sum()
    leave   = working["is_leave"].sum()
    att_pct = round(present / total * 100, 1) if total else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Working Days", total)
    c2.metric("Present",      int(present))
    c3.metric("WFH Days",     int(wfh))
    c4.metric("Attendance",   f"{att_pct}%")

    # Timeline
    timeline = (
        working.groupby(["date","category"]).size().unstack(fill_value=0).reset_index()
    )
    # Category dist
    cat_counts = working["category"].value_counts().reset_index()
    cat_counts.columns = ["Category","Days"]
    
    col1, col2 = st.columns([2,1])
    with col1:
        # Daily attendance strip
        emp_df_sorted = emp_df.sort_values("date")
        color_map = {
            "Present":"#6366f1","Work From Home":"#22d3ee",
            "Sick Leave":"#ef4444","Paid Leave":"#f59e0b",
            "Festival Leave":"#10b981","Weekly Off":"#374151",
            "Holiday":"#4b5563","Birthday Leave":"#ec4899",
            "Leave Without Pay":"#dc2626","Bereavement Leave":"#7c3aed",
            "Menstrual Leave":"#db2777","Other":"#6b7280"
        }
        fig = px.strip(
            emp_df_sorted, x="date", y="category",
            color="category", color_discrete_map=color_map,
            title=f"Daily Attendance — {employee}"
        )
        fig.update_layout(**_base_layout(), showlegend=False)
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        fig2 = px.pie(cat_counts, names="Category", values="Days",
                      color_discrete_sequence=PALETTE["gradient"], hole=0.5,
                      title="Breakdown")
        fig2.update_layout(**_base_layout(), showlegend=False)
        fig2.update_traces(textinfo="percent")
        st.plotly_chart(fig2, width="stretch")

    # Raw data
    with st.expander("📋 View Raw Attendance Data"):
        display_df = emp_df[["date","code","category","month"]].sort_values("date")
        display_df["date"] = display_df["date"].dt.strftime("%d %b %Y")
        st.dataframe(display_df, width="stretch", hide_index=True)


# ── Main Dashboard ─────────────────────────────────────────────────────────────
def show_dashboard():
    # Header
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#1e293b,#0f172a);
        border:1px solid #334155; border-radius:16px;
        padding:1.2rem 1.5rem; margin-bottom:1rem;
        display:flex; align-items:center; gap:1rem;">
        <span style="font-size:2rem">🏢</span>
        <div>
            <div style="color:#f8fafc;font-size:1.3rem;font-weight:700;line-height:1.2">
                AtliQ HR Analytics Dashboard
            </div>
            <div style="color:#64748b;font-size:0.82rem">
                Attendance Insights · Apr–Jun 2022 · Powered by AtliQ Technologies
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    with st.spinner("Loading attendance data..."):
        df = load_attendance_data()

    if df.empty:
        st.error("⚠️ Could not load attendance data. Ensure **Attendance_Sheet_2022-2023_Masked.xlsx** is in the same folder as app.py.")
        st.stop()

    # Sidebar filters
    selected_month, selected_emp = _sidebar(df)

    # Apply filters
    fdf = df.copy()
    if selected_month != "All Months":
        fdf = fdf[fdf["month"] == selected_month]
    if selected_emp != "All Employees":
        fdf = fdf[fdf["name"] == selected_emp]

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", "👤 Employee Deep Dive", "🗓️ Attendance Grid", "📋 Raw Data"
    ])

    with tab1:
        _kpi_row(df, fdf)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            _chart_monthly_trend(fdf)
        with col2:
            _chart_attendance_dist(fdf)

        col3, col4 = st.columns(2)
        with col3:
            _chart_top_employees(fdf)
        with col4:
            _chart_leave_breakdown(fdf)

        col5, col6 = st.columns(2)
        with col5:
            _chart_day_of_week(fdf)
        with col6:
            _chart_wfh_trend(fdf)

    with tab2:
        st.markdown("#### 🔎 Select an Employee for Detailed Analysis")
        emp_list = sorted(df["name"].unique().tolist())
        chosen = st.selectbox("Employee", emp_list, key="deep_emp")
        st.markdown("---")
        _employee_detail(df, chosen)

    with tab3:
        st.markdown("#### 🗓️ Attendance Heatmap")
        month_filter = st.selectbox(
            "Filter by Month", ["All"] + sorted(df["month"].unique().tolist()), key="hm_month"
        )
        hm_df = df if month_filter == "All" else df[df["month"] == month_filter]
        _chart_daily_heatmap(hm_df)

    with tab4:
        st.markdown("#### 📋 Full Attendance Records")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            emp_filter = st.multiselect("Employees", sorted(df["name"].unique().tolist()))
        with col2:
            month_f = st.multiselect("Months", sorted(df["month"].unique().tolist()))
        with col3:
            cat_f = st.multiselect("Categories", sorted(df["category"].unique().tolist()))

        raw = df.copy()
        if emp_filter:   raw = raw[raw["name"].isin(emp_filter)]
        if month_f:      raw = raw[raw["month"].isin(month_f)]
        if cat_f:        raw = raw[raw["category"].isin(cat_f)]

        display_raw = raw[["employee_code","name","date","code","category","month"]].copy()
        display_raw["date"] = display_raw["date"].dt.strftime("%d %b %Y")
        display_raw = display_raw.sort_values("date").rename(columns={
            "employee_code":"Code","name":"Employee","date":"Date",
            "code":"Attendance Code","category":"Category","month":"Month"
        })
        
        st.markdown(f"**{len(display_raw):,} records**")
        st.dataframe(display_raw, width="stretch", hide_index=True, height=450)
        
        # Download
        csv = display_raw.to_csv(index=False)
        st.download_button(
            "⬇️ Download CSV", csv, "atliq_attendance.csv", "text/csv",
            width="stretch"
        )