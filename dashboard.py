"""
dashboard.py — AtliQ Technologies HR Analytics Dashboard
Features: Overview · Calendar Heatmap · Risk Radar · Leaderboard ·
          Day Analysis · Employee Profile · Trends+Forecast ·
          Leave Breakdown · Alerts · AI Insights
"""

import io
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from data_loader import compute_monthly_metrics, MONTH_ORDER, DAY_ORDER

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
CAT_COLORS = {
    "Present":    "#22c55e",
    "WFH":        "#3b82f6",
    "Sick Leave": "#f59e0b",
    "Paid Leave": "#8b5cf6",
    "Leave":      "#a855f7",
    "Absent":     "#ef4444",
    "Off":        "#cbd5e1",
}

RISK_COLORS = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────
def _chart(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#0f172a"), x=0),
        template="plotly_white",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#334155"),
        margin=dict(t=48, b=36, l=8, r=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#e2e8f0", borderwidth=1),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor="#e2e8f0", tickfont_size=11)
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", showline=False, tickfont_size=11)
    return fig


def _kpi(label, value, delta=None, delta_inv=False):
    """Return HTML for a styled KPI card with optional delta arrow."""
    delta_html = ""
    if delta is not None:
        pos = delta >= 0 if not delta_inv else delta <= 0
        color = "#22c55e" if pos else "#ef4444"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = (
            f'<p style="margin:0;font-size:12px;color:{color};">'
            f"{arrow} {abs(delta):.1f}% vs last month</p>"
        )
    return f"""
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                padding:18px 14px;text-align:center;">
      <p style="margin:0 0 4px;font-size:11px;color:#64748b;font-weight:600;
                text-transform:uppercase;letter-spacing:.05em;">{label}</p>
      <p style="margin:0 0 4px;font-size:28px;font-weight:700;color:#0f172a;">{value}</p>
      {delta_html}
    </div>"""


def _initials(name):
    parts = name.strip().split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()


def _risk_badge(level):
    c = {"High": "#dc2626", "Medium": "#d97706", "Low": "#16a34a"}.get(level, "#64748b")
    bg = {"High": "#fef2f2", "Medium": "#fffbeb", "Low": "#f0fdf4"}.get(level, "#f8fafc")
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:20px;'
        f'font-size:12px;font-weight:600;background:{bg};color:{c};">{level} Risk</span>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 – Overview
# ─────────────────────────────────────────────────────────────────────────────
def _tab_overview(df, filt_metrics, selected_months):
    st.markdown("### 📊 Company Overview")

    n_emp    = len(filt_metrics)
    avg_att  = filt_metrics["attendance_pct"].mean()
    avg_wfh  = filt_metrics["wfh_pct"].mean()
    avg_sl   = filt_metrics["sl_pct"].mean()
    n_high   = (filt_metrics["risk_level"] == "High").sum()

    # ── Executive summary card ───────────────────────────────────────────────
    months_str = ", ".join(selected_months)
    risk_note = (
        f"⚠️ <strong>{n_high} employee{'s' if n_high>1 else ''}</strong> "
        "flagged as high attrition risk — immediate review recommended."
        if n_high else "✅ No employees currently flagged as high risk."
    )
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#eff6ff 0%,#f0fdf4 100%);
                    border:1px solid #bfdbfe;border-radius:14px;
                    padding:20px 24px;margin-bottom:20px;">
          <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#1e40af;">
            📋 Executive Summary · AtliQ Technologies · {months_str}
          </p>
          <p style="margin:0;font-size:14px;color:#1e3a5f;line-height:1.75;">
            Across <strong>{n_emp}</strong> employees, average attendance is
            <strong>{avg_att:.1f}%</strong> with WFH adoption at
            <strong>{avg_wfh:.1f}%</strong>.
            Sick leave averages <strong>{avg_sl:.1f}%</strong> of working days.
            {risk_note}
          </p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── KPI cards with delta ─────────────────────────────────────────────────
    monthly = compute_monthly_metrics(df, list(filt_metrics["employee_name"]))
    att_d = wfh_d = sl_d = None
    if len(monthly) >= 2:
        prev, curr = monthly.iloc[-2], monthly.iloc[-1]
        att_d = round(curr["attendance_pct"] - prev["attendance_pct"], 1)
        wfh_d = round(curr["wfh_pct"]        - prev["wfh_pct"],        1)
        sl_d  = round(curr["sl_pct"]          - prev["sl_pct"],         1)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(_kpi("Total Employees",  n_emp),                   unsafe_allow_html=True)
    c2.markdown(_kpi("Avg Attendance",   f"{avg_att:.1f}%", att_d), unsafe_allow_html=True)
    c3.markdown(_kpi("Avg WFH",          f"{avg_wfh:.1f}%", wfh_d), unsafe_allow_html=True)
    c4.markdown(_kpi("Avg Sick Leave",   f"{avg_sl:.1f}%",  sl_d, delta_inv=True),
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ───────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        cat_counts = (
            df[df["category"] != "Off"]["category"]
            .value_counts()
            .reset_index()
        )
        cat_counts.columns = ["Category", "Days"]
        fig = px.pie(
            cat_counts, names="Category", values="Days",
            color="Category", color_discrete_map=CAT_COLORS, hole=0.45,
        )
        _chart(fig, "Overall Attendance Breakdown")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        if not monthly.empty:
            fig2 = go.Figure()
            for col, name, color in [
                ("attendance_pct", "Attendance %",  "#22c55e"),
                ("wfh_pct",        "WFH %",         "#3b82f6"),
                ("sl_pct",         "Sick Leave %",  "#f59e0b"),
            ]:
                fig2.add_trace(go.Scatter(
                    x=monthly["month"], y=monthly[col], name=name,
                    mode="lines+markers",
                    line=dict(color=color, width=2.5),
                    marker=dict(size=8),
                ))
            _chart(fig2, "Monthly KPI Trends")
            fig2.update_yaxes(title_text="Percentage (%)")
            st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 – Calendar Heatmap
# ─────────────────────────────────────────────────────────────────────────────
def _tab_heatmap(df_long, selected_employees):
    st.markdown("### 📅 Attendance Calendar Heatmap")
    st.caption("GitHub-style calendar — see any employee's daily attendance pattern across Apr–Jun 2022.")

    emp_list = sorted(df_long["employee_name"].unique())
    if selected_employees:
        emp_list = [e for e in emp_list if e in selected_employees] or emp_list

    chosen = st.selectbox("Select Employee", emp_list, key="heatmap_emp")

    emp_df = df_long[
        (df_long["employee_name"] == chosen) &
        (df_long["day_num"] <= 4)  # Mon–Fri only
    ].copy()

    if emp_df.empty:
        st.warning("No weekday data for this employee.")
        return

    cat_num_map = {
        "Off": 0, "Present": 1, "WFH": 2,
        "Sick Leave": 3, "Paid Leave": 4, "Leave": 4, "Absent": 5,
    }
    emp_df["cat_num"] = emp_df["category"].map(cat_num_map).fillna(0)

    weeks = sorted(emp_df["week_num"].unique())
    x_labels = [f"W{w}" for w in weeks]
    y_labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    z, hover = [], []
    for day_num in range(5):
        row_z, row_h = [], []
        for wk in weeks:
            cell = emp_df[(emp_df["week_num"] == wk) & (emp_df["day_num"] == day_num)]
            if cell.empty:
                row_z.append(None)
                row_h.append("")
            else:
                r = cell.iloc[0]
                row_z.append(r["cat_num"])
                row_h.append(f"{r['date'].strftime('%b %d')}: {r['category']}")
        z.append(row_z)
        hover.append(row_h)

    colorscale = [
        [0.00, "#f1f5f9"],  # Off
        [0.20, "#22c55e"],  # Present
        [0.40, "#3b82f6"],  # WFH
        [0.60, "#f59e0b"],  # Sick Leave
        [0.80, "#8b5cf6"],  # Leave
        [1.00, "#ef4444"],  # Absent
    ]

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=x_labels,
            y=y_labels,
            text=hover,
            hovertemplate="%{text}<extra></extra>",
            colorscale=colorscale,
            zmin=0, zmax=5,
            showscale=False,
            xgap=3, ygap=3,
        )
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(t=16, b=30, l=50, r=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=220,
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    # Colour legend
    legend_items = [
        ("Present",    "#22c55e"),
        ("WFH",        "#3b82f6"),
        ("Sick Leave", "#f59e0b"),
        ("Leave",      "#8b5cf6"),
        ("Absent",     "#ef4444"),
        ("Off/Holiday","#f1f5f9"),
    ]
    cols = st.columns(6)
    for i, (lbl, clr) in enumerate(legend_items):
        cols[i].markdown(
            f'<div style="display:flex;align-items:center;gap:5px;font-size:12px;">'
            f'<div style="width:13px;height:13px;border-radius:3px;background:{clr};'
            f'border:1px solid #e2e8f0;flex-shrink:0;"></div>{lbl}</div>',
            unsafe_allow_html=True,
        )

    # Quick metrics for chosen employee
    st.markdown("---")
    m = df_long[df_long["employee_name"] == chosen].agg(
        tw=("is_working", "sum"),
        p=("present_val", "sum"),
        wfh=("wfh_val", "sum"),
        sl=("sl_val", "sum"),
    )
    tw = m["tw"] or 1
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Attendance",   f"{m['p']/tw*100:.1f}%")
    c2.metric("WFH",          f"{m['wfh']/tw*100:.1f}%")
    c3.metric("Sick Leave",   f"{m['sl']/tw*100:.1f}%")
    c4.metric("Working Days", int(tw))


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3 – Risk Radar
# ─────────────────────────────────────────────────────────────────────────────
def _tab_risk(filt_metrics):
    st.markdown("### ⚠️ Attrition Risk Radar")
    st.caption(
        "Each employee is scored on attendance, sick leave frequency, and absenteeism. "
        "High Risk = immediate HR attention required."
    )

    if filt_metrics.empty:
        st.warning("No data for current filter.")
        return

    rc = filt_metrics["risk_level"].value_counts()
    high = int(rc.get("High", 0))
    med  = int(rc.get("Medium", 0))
    low  = int(rc.get("Low", 0))

    c1, c2, c3 = st.columns(3)
    for col, label, icon, n, bg, bc, tc in [
        (c1, "High Risk",   "⚠️", high, "#fef2f2", "#fca5a5", "#dc2626"),
        (c2, "Medium Risk", "⚡", med,  "#fffbeb", "#fcd34d", "#d97706"),
        (c3, "Low Risk",    "✅", low,  "#f0fdf4", "#86efac", "#16a34a"),
    ]:
        col.markdown(
            f"""<div style="background:{bg};border:1px solid {bc};border-radius:12px;
                            padding:18px;text-align:center;">
              <p style="margin:0;font-size:11px;color:{tc};font-weight:600;
                        text-transform:uppercase;">{icon} {label}</p>
              <p style="margin:4px 0 0;font-size:36px;font-weight:700;color:{tc};">{n}</p>
              <p style="margin:0;font-size:12px;color:{tc};">employees</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        fig = px.scatter(
            filt_metrics,
            x="attendance_pct", y="sl_pct",
            color="risk_level", color_discrete_map=RISK_COLORS,
            hover_name="employee_name",
            size="risk_score", size_max=22,
            labels={"attendance_pct": "Attendance %", "sl_pct": "Sick Leave %"},
        )
        fig.add_hline(y=5,  line_dash="dash", line_color="#f59e0b",
                      annotation_text="SL threshold (5%)")
        fig.add_vline(x=85, line_dash="dash", line_color="#ef4444",
                      annotation_text="Att threshold (85%)")
        _chart(fig, "Risk Profile: Attendance vs Sick Leave")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        top20 = filt_metrics.sort_values("risk_score").tail(20)
        fig2 = px.bar(
            top20, x="risk_score", y="employee_name",
            color="risk_level", color_discrete_map=RISK_COLORS,
            orientation="h",
            labels={"risk_score": "Risk Score", "employee_name": ""},
        )
        _chart(fig2, "Top 20 Employees by Risk Score")
        fig2.update_layout(showlegend=False, height=420)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Risk Register")
    lvl_filter = st.selectbox("Filter", ["All", "High", "Medium", "Low"], key="risk_lvl_sel")

    tbl = filt_metrics[
        ["employee_name", "attendance_pct", "wfh_pct", "sl_pct",
         "absence_pct", "risk_level", "risk_score"]
    ].copy()
    tbl.columns = ["Employee", "Attendance %", "WFH %", "SL %",
                   "Absence %", "Risk Level", "Score"]
    tbl = tbl.sort_values("Score", ascending=False).reset_index(drop=True)

    if lvl_filter != "All":
        tbl = tbl[tbl["Risk Level"] == lvl_filter]

    # Add emoji prefix to Risk Level column for visual clarity
    tbl["Risk Level"] = tbl["Risk Level"].map(
        {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}
    )
    st.dataframe(tbl, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 4 – Leaderboard
# ─────────────────────────────────────────────────────────────────────────────
def _tab_leaderboard(filt_metrics):
    st.markdown("### 🏆 Attendance Leaderboard")

    if filt_metrics.empty:
        st.warning("No data for current filter.")
        return

    ranked = (
        filt_metrics.sort_values("attendance_pct", ascending=False)
        .reset_index(drop=True)
    )

    # Podium
    if len(ranked) >= 3:
        st.markdown("#### Top 3 Performers")
        medal_cfg = [
            ("🥇", "#fef9c3", "#eab308"),
            ("🥈", "#f1f5f9", "#94a3b8"),
            ("🥉", "#fef3e2", "#cd7c3a"),
        ]
        pod_cols = st.columns(3)
        for i, (medal, bg, border) in enumerate(medal_cfg):
            row = ranked.iloc[i]
            pod_cols[i].markdown(
                f"""<div style="background:{bg};border:2px solid {border};
                                border-radius:14px;padding:20px;text-align:center;">
                  <div style="font-size:30px;">{medal}</div>
                  <div style="font-size:14px;font-weight:600;color:#0f172a;margin:8px 0 4px;">
                    {row['employee_name'][:18]}
                  </div>
                  <div style="font-size:26px;font-weight:700;color:#0f172a;">
                    {row['attendance_pct']:.1f}%
                  </div>
                  <div style="font-size:11px;color:#64748b;">Attendance</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        top10 = ranked.head(10)
        fig = px.bar(
            top10, x="attendance_pct", y="employee_name",
            orientation="h", color="attendance_pct",
            color_continuous_scale="Greens",
            labels={"attendance_pct": "Attendance %", "employee_name": ""},
        )
        _chart(fig, "Top 10 Attendance")
        fig.update_layout(coloraxis_showscale=False, height=340)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        bot10 = ranked.tail(10).sort_values("attendance_pct")
        fig2 = px.bar(
            bot10, x="attendance_pct", y="employee_name",
            orientation="h", color="attendance_pct",
            color_continuous_scale="Reds_r",
            labels={"attendance_pct": "Attendance %", "employee_name": ""},
        )
        _chart(fig2, "Bottom 10 Attendance")
        fig2.update_layout(coloraxis_showscale=False, height=340)
        fig2.update_yaxes(autorange="reversed")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Full Rankings")
    full_tbl = ranked[
        ["employee_name", "attendance_pct", "wfh_pct", "sl_pct", "total_working"]
    ].copy()
    full_tbl.columns = ["Employee", "Attendance %", "WFH %", "Sick Leave %", "Working Days"]
    full_tbl.insert(0, "Rank", range(1, len(full_tbl) + 1))
    st.dataframe(full_tbl, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 5 – Day-of-Week Analysis
# ─────────────────────────────────────────────────────────────────────────────
def _tab_day_analysis(df):
    st.markdown("### 📆 Day-of-Week Analysis")
    st.caption("Which weekday sees the most absences, WFH, or sick leave? Spot behavioural patterns.")

    weekday_df = df[df["day_of_week"].isin(DAY_ORDER)].copy()
    if weekday_df.empty:
        st.warning("No weekday data in the current filter.")
        return

    working_df = weekday_df[weekday_df["category"] != "Off"]

    # Count by day × category
    day_cat = (
        working_df.groupby(["day_of_week", "category"])
        .size()
        .reset_index(name="count")
    )
    day_cat["day_of_week"] = pd.Categorical(
        day_cat["day_of_week"], categories=DAY_ORDER, ordered=True
    )
    day_cat = day_cat.sort_values("day_of_week")

    col_l, col_r = st.columns(2)

    with col_l:
        fig = px.bar(
            day_cat, x="day_of_week", y="count", color="category",
            color_discrete_map=CAT_COLORS, barmode="stack",
            labels={"day_of_week": "Day", "count": "Occurrences", "category": "Status"},
        )
        _chart(fig, "Status Count by Day of Week")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        day_total = working_df.groupby("day_of_week").size().reset_index(name="total")
        pct_df = day_cat.merge(day_total, on="day_of_week")
        pct_df["pct"] = (pct_df["count"] / pct_df["total"] * 100).round(1)
        pct_df["day_of_week"] = pd.Categorical(
            pct_df["day_of_week"], categories=DAY_ORDER, ordered=True
        )
        pct_df = pct_df.sort_values("day_of_week")

        fig2 = px.bar(
            pct_df, x="day_of_week", y="pct", color="category",
            color_discrete_map=CAT_COLORS, barmode="stack",
            labels={"day_of_week": "Day", "pct": "Percentage (%)", "category": "Status"},
        )
        _chart(fig2, "Normalised Distribution (%) by Day")
        fig2.update_yaxes(range=[0, 100])
        st.plotly_chart(fig2, use_container_width=True)

    # Absence + SL focus line
    abs_sl = working_df[working_df["category"].isin(["Absent", "Sick Leave"])]
    if not abs_sl.empty:
        focus = (
            abs_sl.groupby(["day_of_week", "category"])
            .size()
            .reset_index(name="count")
        )
        focus["day_of_week"] = pd.Categorical(
            focus["day_of_week"], categories=DAY_ORDER, ordered=True
        )
        focus = focus.sort_values("day_of_week")
        fig3 = px.line(
            focus, x="day_of_week", y="count", color="category",
            color_discrete_map=CAT_COLORS, markers=True,
            labels={"day_of_week": "Day", "count": "Count"},
        )
        _chart(fig3, "Absence & Sick Leave by Weekday")
        st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 6 – Employee Profile
# ─────────────────────────────────────────────────────────────────────────────
def _tab_profile(df_long, emp_metrics, selected_employees):
    st.markdown("### 🔍 Employee Deep Dive")

    emp_list = sorted(df_long["employee_name"].unique())
    if selected_employees:
        emp_list = [e for e in emp_list if e in selected_employees] or emp_list

    chosen = st.selectbox("Select Employee", emp_list, key="profile_emp")

    row_df = emp_metrics[emp_metrics["employee_name"] == chosen]
    if row_df.empty:
        st.warning("No metrics found.")
        return

    row = row_df.iloc[0]
    emp_df = df_long[df_long["employee_name"] == chosen].copy()
    risk_c = RISK_COLORS.get(row["risk_level"], "#64748b")

    # Profile header
    init = _initials(chosen)
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:20px;padding:20px;
                        background:#f8fafc;border:1px solid #e2e8f0;
                        border-radius:14px;margin-bottom:20px;">
          <div style="width:58px;height:58px;border-radius:50%;background:#dbeafe;
                      display:flex;align-items:center;justify-content:center;
                      font-size:20px;font-weight:700;color:#1d4ed8;flex-shrink:0;">{init}</div>
          <div>
            <div style="font-size:20px;font-weight:700;color:#0f172a;">{chosen}</div>
            <div style="font-size:13px;color:#64748b;">AtliQ Technologies · Apr–Jun 2022</div>
            <div style="margin-top:6px;">{_risk_badge(row['risk_level'])}</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Attendance",  f"{row['attendance_pct']:.1f}%")
    c2.metric("WFH",         f"{row['wfh_pct']:.1f}%")
    c3.metric("Sick Leave",  f"{row['sl_pct']:.1f}%")
    c4.metric("Working Days", int(row["total_working"]))

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        cat_counts = (
            emp_df[emp_df["category"] != "Off"]["category"]
            .value_counts()
            .reset_index()
        )
        cat_counts.columns = ["Status", "Days"]
        fig = px.pie(
            cat_counts, names="Status", values="Days",
            color="Status", color_discrete_map=CAT_COLORS, hole=0.42,
        )
        _chart(fig, f"{chosen.split()[0]}'s Attendance Breakdown")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        mth = (
            emp_df.groupby("month")
            .agg(
                tw=("is_working", "sum"),
                p=("present_val", "sum"),
                wfh=("wfh_val", "sum"),
                sl=("sl_val", "sum"),
            )
            .reset_index()
        )
        mth["_ord"] = mth["month"].map(MONTH_ORDER)
        mth = mth.sort_values("_ord").drop("_ord", axis=1)
        mth["att_pct"] = (mth["p"]   / mth["tw"].replace(0, np.nan) * 100).round(1)
        mth["wfh_pct"] = (mth["wfh"] / mth["tw"].replace(0, np.nan) * 100).round(1)
        mth["sl_pct"]  = (mth["sl"]  / mth["tw"].replace(0, np.nan) * 100).round(1)

        fig2 = go.Figure()
        for col_key, label, color in [
            ("att_pct", "Attendance %", "#22c55e"),
            ("wfh_pct", "WFH %",        "#3b82f6"),
            ("sl_pct",  "SL %",         "#f59e0b"),
        ]:
            fig2.add_trace(go.Bar(
                x=mth["month"], y=mth[col_key],
                name=label, marker_color=color,
            ))
        _chart(fig2, "Month-by-Month Breakdown")
        fig2.update_layout(barmode="group")
        st.plotly_chart(fig2, use_container_width=True)

    # Timeline scatter
    st.markdown("#### Attendance Timeline")
    cat_y = {"Present": 4, "WFH": 3, "Sick Leave": 2, "Paid Leave": 1.5,
              "Leave": 1.5, "Absent": 1, "Off": 0}
    timeline = emp_df[emp_df["day_of_week"].isin(DAY_ORDER)].copy()
    timeline["y_val"] = timeline["category"].map(cat_y).fillna(0)

    fig3 = px.scatter(
        timeline, x="date", y="y_val",
        color="category", color_discrete_map=CAT_COLORS,
        hover_data={"date": True, "status": True, "category": True, "y_val": False},
        labels={"date": "Date", "y_val": ""},
    )
    _chart(fig3, "Daily Status — Apr to Jun 2022")
    fig3.update_layout(
        yaxis=dict(
            tickvals=[1, 1.5, 2, 3, 4],
            ticktext=["Absent", "Leave", "Sick Leave", "WFH", "Present"],
        ),
        height=260,
    )
    st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 7 – Trends & Forecast
# ─────────────────────────────────────────────────────────────────────────────
def _tab_forecast(df_long, selected_employees):
    st.markdown("### 📈 Trends & Attendance Forecast")
    st.caption(
        "Month-over-month trends for Apr–Jun 2022 with linear projection to July 2022."
    )

    monthly = compute_monthly_metrics(df_long, selected_employees)
    if monthly.empty or len(monthly) < 2:
        st.warning("At least 2 months of data required for trend analysis.")
        return

    months_list = monthly["month"].tolist()
    x = np.arange(1, len(months_list) + 1, dtype=float)
    x_f = float(len(months_list) + 1)

    def _forecast(y_arr):
        coeffs = np.polyfit(x, y_arr, 1)
        val = float(np.polyval(coeffs, x_f))
        return max(0.0, min(100.0, round(val, 1)))

    att_f = _forecast(monthly["attendance_pct"].values)
    wfh_f = _forecast(monthly["wfh_pct"].values)
    sl_f  = _forecast(monthly["sl_pct"].values)

    last_att = float(monthly["attendance_pct"].iloc[-1])
    last_wfh = float(monthly["wfh_pct"].iloc[-1])
    last_sl  = float(monthly["sl_pct"].iloc[-1])
    last_mo  = months_list[-1]

    fig = go.Figure()

    # Actual traces
    for col_key, label, color in [
        ("attendance_pct", "Attendance %", "#22c55e"),
        ("wfh_pct",        "WFH %",        "#3b82f6"),
        ("sl_pct",         "Sick Leave %", "#f59e0b"),
    ]:
        fig.add_trace(go.Scatter(
            x=months_list, y=monthly[col_key].tolist(),
            name=label, mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=9),
        ))

    # Forecast dashed bridges
    forecast_label = "July 2022 (Forecast)"
    for last_val, f_val, color in [
        (last_att, att_f, "#22c55e"),
        (last_wfh, wfh_f, "#3b82f6"),
        (last_sl,  sl_f,  "#f59e0b"),
    ]:
        fig.add_trace(go.Scatter(
            x=[last_mo, forecast_label],
            y=[last_val, f_val],
            mode="lines+markers",
            line=dict(color=color, width=2, dash="dash"),
            marker=dict(size=11, symbol="diamond"),
            showlegend=False,
        ))

    _chart(fig, "Monthly Trends with July 2022 Forecast")
    fig.update_yaxes(title_text="Percentage (%)")
    st.plotly_chart(fig, use_container_width=True)

    # Forecast cards
    st.markdown("#### July 2022 Projection")
    f1, f2, f3 = st.columns(3)
    f1.metric("Attendance %",  f"{att_f:.1f}%",
              delta=f"{att_f - last_att:+.1f}% from June")
    f2.metric("WFH %",         f"{wfh_f:.1f}%",
              delta=f"{wfh_f - last_wfh:+.1f}% from June")
    f3.metric("Sick Leave %",  f"{sl_f:.1f}%",
              delta=f"{sl_f - last_sl:+.1f}% from June",
              delta_color="inverse")

    st.info(
        "📌 Forecast is a simple linear extrapolation from 3 data points. "
        "Treat as directional signal, not a precise prediction.",
        icon="ℹ️",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tab 8 – Leave Breakdown
# ─────────────────────────────────────────────────────────────────────────────
def _tab_leave(df):
    st.markdown("### 🌿 Leave Breakdown Analysis")

    leave_cats = ["Sick Leave", "Paid Leave", "Leave"]
    leave_df = df[df["category"].isin(leave_cats)].copy()

    if leave_df.empty:
        st.info("No leave records in current filter selection.")
        return

    col_l, col_r = st.columns(2)

    with col_l:
        dist = leave_df.groupby("status").size().reset_index(name="count")
        dist = dist.sort_values("count", ascending=False)
        fig = px.pie(dist, names="status", values="count", hole=0.42)
        _chart(fig, "Leave Code Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        mth_leave = (
            df.groupby("month")
            .agg(
                sl=("sl_val", "sum"),
                lv=("leave_val", "sum"),
                tw=("is_working", "sum"),
            )
            .reset_index()
        )
        mth_leave["_ord"] = mth_leave["month"].map(MONTH_ORDER)
        mth_leave = mth_leave.sort_values("_ord").drop("_ord", axis=1)
        tw = mth_leave["tw"].replace(0, np.nan)
        mth_leave["sl_pct"] = (mth_leave["sl"] / tw * 100).round(1)
        mth_leave["lv_pct"] = (mth_leave["lv"] / tw * 100).round(1)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=mth_leave["month"], y=mth_leave["sl_pct"],
                              name="Sick Leave %",  marker_color="#f59e0b"))
        fig2.add_trace(go.Bar(x=mth_leave["month"], y=mth_leave["lv_pct"],
                              name="Other Leave %", marker_color="#8b5cf6"))
        _chart(fig2, "Monthly Leave Trends")
        fig2.update_layout(barmode="group")
        st.plotly_chart(fig2, use_container_width=True)

    # Top leave takers
    st.markdown("#### Top Employees by Leave Days")
    top_lv = (
        df.groupby("employee_name")
        .agg(sl=("sl_val", "sum"), lv=("leave_val", "sum"))
        .reset_index()
    )
    top_lv["total"] = (top_lv["sl"] + top_lv["lv"]).round(1)
    top_lv = top_lv.sort_values("total", ascending=False).head(15)

    fig3 = px.bar(
        top_lv, x="total", y="employee_name",
        orientation="h", color="sl",
        color_continuous_scale="Oranges",
        labels={"total": "Total Leave Days", "employee_name": "", "sl": "SL Days"},
    )
    _chart(fig3, "Top 15 by Leave Days (colour = Sick Leave days)")
    fig3.update_layout(height=420)
    fig3.update_yaxes(autorange="reversed")
    st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 9 – Alerts
# ─────────────────────────────────────────────────────────────────────────────
def _tab_alerts(filt_metrics, df):
    st.markdown("### 🚨 Absenteeism Alerts")
    st.caption("Configurable thresholds for flagging employees who need HR attention.")

    c_att, c_sl = st.columns(2)
    with c_att:
        att_thresh = st.slider("Flag below attendance %", 50, 95, 80, key="alert_att")
    with c_sl:
        sl_thresh = st.slider("Flag above sick leave %",  1,  20,  5, key="alert_sl")

    st.markdown("---")

    low_att  = filt_metrics[filt_metrics["attendance_pct"] < att_thresh].sort_values("attendance_pct")
    high_sl  = filt_metrics[filt_metrics["sl_pct"] > sl_thresh].sort_values("sl_pct", ascending=False)

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(f"#### ⬇️ Low Attendance  (< {att_thresh}%)")
        if low_att.empty:
            st.success("No employees below this threshold. 🎉")
        else:
            for _, r in low_att.iterrows():
                st.markdown(
                    f"""<div style="display:flex;justify-content:space-between;
                                    align-items:center;padding:10px 14px;
                                    margin-bottom:6px;border-radius:8px;
                                    background:#fef2f2;border-left:4px solid #ef4444;">
                      <span style="font-size:13px;color:#0f172a;">{r['employee_name']}</span>
                      <span style="font-size:13px;font-weight:700;color:#dc2626;">
                        {r['attendance_pct']:.1f}%</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

    with col_r:
        st.markdown(f"#### 🤒 High Sick Leave  (> {sl_thresh}%)")
        if high_sl.empty:
            st.success("No employees above this threshold. 🎉")
        else:
            for _, r in high_sl.iterrows():
                st.markdown(
                    f"""<div style="display:flex;justify-content:space-between;
                                    align-items:center;padding:10px 14px;
                                    margin-bottom:6px;border-radius:8px;
                                    background:#fffbeb;border-left:4px solid #f59e0b;">
                      <span style="font-size:13px;color:#0f172a;">{r['employee_name']}</span>
                      <span style="font-size:13px;font-weight:700;color:#d97706;">
                        {r['sl_pct']:.1f}%</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # Scatter with threshold zones
    if not filt_metrics.empty:
        st.markdown("---")
        st.markdown("#### Alert Zone Map")
        fig = px.scatter(
            filt_metrics,
            x="attendance_pct", y="sl_pct",
            hover_name="employee_name",
            color="risk_level", color_discrete_map=RISK_COLORS,
            labels={"attendance_pct": "Attendance %", "sl_pct": "Sick Leave %"},
        )
        fig.add_hline(y=sl_thresh,  line_dash="dash", line_color="#f59e0b",
                      annotation_text=f"SL > {sl_thresh}%")
        fig.add_vline(x=att_thresh, line_dash="dash", line_color="#ef4444",
                      annotation_text=f"Att < {att_thresh}%")
        _chart(fig, "Attendance vs Sick Leave — Alert Zones")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 10 – AI Insights
# ─────────────────────────────────────────────────────────────────────────────
def _tab_ai(df, filt_metrics):
    st.markdown("### 🤖 AI-Powered HR Insights")
    st.caption("Powered by Groq · llama-3.3-70b-versatile · Ask anything about your attendance data.")

    n_emp    = len(filt_metrics)
    avg_att  = filt_metrics["attendance_pct"].mean()
    avg_wfh  = filt_metrics["wfh_pct"].mean()
    avg_sl   = filt_metrics["sl_pct"].mean()
    high_risk = filt_metrics[filt_metrics["risk_level"] == "High"]["employee_name"].tolist()
    low_att   = filt_metrics[filt_metrics["attendance_pct"] < 80]["employee_name"].tolist()
    top3      = filt_metrics.nlargest(3, "attendance_pct")["employee_name"].tolist()

    context = (
        f"AtliQ Technologies HR Data (Apr–Jun 2022):\n"
        f"• Employees: {n_emp}\n"
        f"• Avg attendance: {avg_att:.1f}%  |  Avg WFH: {avg_wfh:.1f}%  |  Avg SL: {avg_sl:.1f}%\n"
        f"• High-risk employees: {', '.join(high_risk[:10]) or 'None'}\n"
        f"• Low attendance (<80%): {', '.join(low_att[:10]) or 'None'}\n"
        f"• Top 3 attendance: {', '.join(top3)}\n"
    )

    # Quick question buttons
    st.markdown("**Quick Insights**")
    q_cols = st.columns(4)
    quick_qs = [
        "What are the key attendance trends?",
        "Which employees need immediate HR attention?",
        "What does the WFH pattern suggest?",
        "Give me 3 actionable HR recommendations.",
    ]
    if "ai_q" not in st.session_state:
        st.session_state.ai_q = ""

    for i, q in enumerate(quick_qs):
        if q_cols[i].button(q, key=f"qbtn_{i}", use_container_width=True):
            st.session_state.ai_q = q

    st.markdown("**Or type your own question:**")
    user_q = st.text_area(
        "Question",
        value=st.session_state.ai_q,
        placeholder="e.g. Which employees show signs of burnout? Compare April vs June.",
        height=80,
        label_visibility="collapsed",
    )

    col_run, _ = st.columns([1, 4])
    run = col_run.button("🔍 Analyse", type="primary", use_container_width=True)

    if run and user_q.strip():
        groq_key = st.secrets.get("GROQ_API_KEY", "")
        if not groq_key:
            st.error("GROQ_API_KEY not found in Streamlit secrets.")
            return

        with st.spinner("Analysing data with AI..."):
            try:
                system_prompt = (
                    "You are a concise, professional HR analytics consultant. "
                    "Base every answer on the data provided. Use markdown bullet points where helpful."
                )
                user_prompt = (
                    f"Here is the HR attendance data summary:\n{context}\n\n"
                    f"Question: {user_q}\n\n"
                    "Respond with:\n"
                    "**Key Finding** (1–2 sentences)\n"
                    "**Analysis** (3–4 sentences)\n"
                    "**Recommended Actions** (3–5 bullet points)"
                )

                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": user_prompt},
                        ],
                        "max_tokens": 900,
                        "temperature": 0.35,
                    },
                    timeout=30,
                )

                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"]
                    st.markdown("---")
                    st.markdown("**📋 AI Analysis**")
                    st.markdown(
                        f'<div style="background:#f0f9ff;border:1px solid #bae6fd;'
                        f'border-radius:12px;padding:20px 24px;'
                        f'line-height:1.75;font-size:14px;">{answer}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(f"Groq API error {resp.status_code}: {resp.text[:300]}")

            except Exception as exc:
                st.error(f"Error calling Groq API: {exc}")

    elif run:
        st.warning("Please enter a question first.")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard(df_long, emp_metrics):
    if df_long is None or df_long.empty:
        st.error("No attendance data loaded. Ensure 'Attendance Sheet.xlsx' is in the app directory.")
        return

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🔧 Filters")

        all_months = sorted(df_long["month"].unique(), key=lambda m: MONTH_ORDER.get(m, 99))
        sel_months = st.multiselect("Month", all_months, default=list(all_months))
        if not sel_months:
            sel_months = list(all_months)

        all_emps = sorted(df_long["employee_name"].unique())
        sel_emps = st.multiselect("Employees", all_emps, default=list(all_emps))
        if not sel_emps:
            sel_emps = list(all_emps)

        st.markdown("---")
        st.markdown("## 📥 Export Data")

        filt_m = emp_metrics[emp_metrics["employee_name"].isin(sel_emps)].copy()

        csv_bytes = filt_m.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV",
            csv_bytes,
            "atliq_hr_report.csv",
            "text/csv",
            use_container_width=True,
        )

        xl_buf = io.BytesIO()
        with pd.ExcelWriter(xl_buf, engine="openpyxl") as writer:
            filt_m.to_excel(writer, sheet_name="HR Metrics", index=False)
        st.download_button(
            "⬇️ Download Excel",
            xl_buf.getvalue(),
            "atliq_hr_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        st.markdown("---")
        n_high = int((filt_m["risk_level"] == "High").sum())
        if n_high:
            st.warning(f"⚠️ {n_high} high-risk employee{'s' if n_high > 1 else ''}")
        else:
            st.success("✅ No high-risk employees")

        st.caption(
            f"v4.0 · {len(sel_emps)}/{len(all_emps)} employees · "
            f"{len(sel_months)} month{'s' if len(sel_months) != 1 else ''} selected"
        )

    # Apply filters
    df = df_long[
        df_long["month"].isin(sel_months) &
        df_long["employee_name"].isin(sel_emps)
    ].copy()

    filt_metrics = emp_metrics[emp_metrics["employee_name"].isin(sel_emps)].copy()

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "📊 Overview",
        "📅 Heatmap",
        "⚠️ Risk Radar",
        "🏆 Leaderboard",
        "📆 Day Analysis",
        "🔍 Employee Profile",
        "📈 Trends & Forecast",
        "🌿 Leave Breakdown",
        "🚨 Alerts",
        "🤖 AI Insights",
    ])

    with tabs[0]: _tab_overview(df, filt_metrics, sel_months)
    with tabs[1]: _tab_heatmap(df_long, sel_emps)
    with tabs[2]: _tab_risk(filt_metrics)
    with tabs[3]: _tab_leaderboard(filt_metrics)
    with tabs[4]: _tab_day_analysis(df)
    with tabs[5]: _tab_profile(df_long, emp_metrics, sel_emps)
    with tabs[6]: _tab_forecast(df_long, sel_emps)
    with tabs[7]: _tab_leave(df)
    with tabs[8]: _tab_alerts(filt_metrics, df)
    with tabs[9]: _tab_ai(df, filt_metrics)
