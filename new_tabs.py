"""
new_tabs.py  —  Drop-in new tabs for Sujal's HR Analytics Streamlit app
Add these 3 tabs to your existing dashboard.py:
  1. Leave Breakdown  📊
  2. Absenteeism Alerts  🚨
  3. Month-wise Trends  📅
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ═══════════════════════════════════════════════════════════════
# 1.  LEAVE BREAKDOWN TAB
# ═══════════════════════════════════════════════════════════════
def render_leave_breakdown(df: pd.DataFrame):
    st.header("📊 Leave Breakdown Analysis")
    st.caption("Detailed view of leave types across employees and months.")

    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox(
            "Select Month", ["All Months"] + sorted(df["Month"].unique().tolist())
        )
    with col2:
        view_by = st.radio("View by", ["Company-wide", "Per Employee"], horizontal=True)

    filtered = df if selected_month == "All Months" else df[df["Month"] == selected_month]

    leave_codes = {
        "SL": "Sick Leave", "HSL": "Half Sick Leave",
        "PL": "Paid Leave", "HPL": "Half Paid Leave",
        "WFH": "Work From Home", "HWFH": "Half WFH",
        "FFL": "Festival Leave", "HFFL": "Half Festival Leave",
        "LWP": "Leave Without Pay", "HLWP": "Half LWP",
        "BL ": "Birthday Leave", "BRL ": "Bereavement Leave",
        "ML": "Menstrual Leave",
    }

    leave_mask = filtered["Status"].isin(list(leave_codes.keys()))
    leave_df = filtered[leave_mask].copy()
    leave_df["Leave Type"] = leave_df["Status"].map(leave_codes)

    if leave_df.empty:
        st.warning("No leave records found for selected filters.")
        return

    st.divider()

    if view_by == "Company-wide":
        leave_counts = leave_df["Leave Type"].value_counts().reset_index()
        leave_counts.columns = ["Leave Type", "Count"]

        fig_pie = px.pie(
            leave_counts, names="Leave Type", values="Count",
            title=f"Leave Distribution — {selected_month}",
            color_discrete_sequence=px.colors.qualitative.Set3, hole=0.4,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=420)
        st.plotly_chart(fig_pie, use_container_width=True)

        monthly_leave = df[df["Status"].isin(list(leave_codes.keys()))].copy()
        monthly_leave["Leave Type"] = monthly_leave["Status"].map(leave_codes)
        monthly_grp = monthly_leave.groupby(["Month", "Leave Type"]).size().reset_index(name="Count")

        fig_bar = px.bar(
            monthly_grp, x="Month", y="Count", color="Leave Type",
            title="Leave Counts by Month (All Types)", barmode="stack",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    else:
        emp_leave = leave_df.groupby(["Name", "Leave Type"]).size().reset_index(name="Days")
        top_emp = emp_leave.groupby("Name")["Days"].sum().nlargest(15).index
        emp_leave = emp_leave[emp_leave["Name"].isin(top_emp)]

        fig_emp = px.bar(
            emp_leave, x="Name", y="Days", color="Leave Type",
            title=f"Top 15 Employees — Leave Breakdown ({selected_month})",
            barmode="stack", color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_emp.update_layout(height=450, xaxis_tickangle=-35)
        st.plotly_chart(fig_emp, use_container_width=True)

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Leave Days", len(leave_df))
    m2.metric("Most Common Leave", leave_df["Leave Type"].value_counts().index[0])
    m3.metric("Sick Leave Days", leave_df["Status"].isin(["SL", "HSL"]).sum())
    m4.metric("WFH Days", leave_df["Status"].isin(["WFH", "HWFH"]).sum())


# ═══════════════════════════════════════════════════════════════
# 2.  ABSENTEEISM ALERTS TAB
# ═══════════════════════════════════════════════════════════════
def render_absenteeism_alerts(df: pd.DataFrame):
    st.header("🚨 Absenteeism Alerts")
    st.caption("Identify employees who may need HR intervention based on attendance patterns.")

    col1, col2 = st.columns([2, 1])
    with col1:
        threshold = st.slider(
            "Attendance Alert Threshold (%)", min_value=50, max_value=95,
            value=75, step=5, help="Employees below this % will be flagged",
        )
    with col2:
        selected_month = st.selectbox(
            "Month", ["All Months"] + sorted(df["Month"].unique().tolist()), key="alert_month"
        )

    filtered = df if selected_month == "All Months" else df[df["Month"] == selected_month]
    work_days = filtered[~filtered["Status"].isin(["WO", "HO"])]

    emp_stats = (
        work_days.groupby(["Employee Code", "Name"])
        .agg(
            Present=("Status", lambda x: x.isin(["P", "WFH"]).sum()),
            Sick=("Status", lambda x: x.isin(["SL", "HSL"]).sum()),
            LWP=("Status", lambda x: x.isin(["LWP", "HLWP"]).sum()),
            Total_Working=("Status", "count"),
        )
        .reset_index()
    )
    emp_stats["Attendance %"] = (emp_stats["Present"] / emp_stats["Total_Working"] * 100).round(1)

    at_risk = emp_stats[emp_stats["Attendance %"] < threshold].sort_values("Attendance %")
    safe = emp_stats[emp_stats["Attendance %"] >= threshold]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Employees", len(emp_stats))
    c2.metric(f"🔴 Below {threshold}%", len(at_risk),
              delta=f"{len(at_risk)/max(len(emp_stats),1)*100:.0f}% of workforce",
              delta_color="inverse")
    c3.metric("✅ Above Threshold", len(safe))
    c4.metric("Avg Attendance", f"{emp_stats['Attendance %'].mean():.1f}%")

    st.divider()

    if at_risk.empty:
        st.success(f"✅ No employees below {threshold}% attendance! Great job.")
    else:
        st.subheader(f"🔴 At-Risk Employees ({len(at_risk)} flagged)")

        def color_attendance(val):
            if val < 60:
                return "background-color: #ff4d4d; color: white; font-weight: bold"
            elif val < threshold:
                return "background-color: #ffa500; color: white"
            return ""

        display_df = at_risk[["Name", "Employee Code", "Attendance %", "Sick", "LWP", "Total_Working"]].copy()
        display_df.columns = ["Name", "Emp Code", "Attendance %", "Sick Days", "LWP Days", "Working Days"]
        st.dataframe(
            display_df.style.map(color_attendance, subset=["Attendance %"]),
            use_container_width=True, hide_index=True,
        )

        fig = px.bar(
            at_risk.head(20), x="Attendance %", y="Name", orientation="h",
            color="Attendance %", color_continuous_scale=["red", "orange", "yellow"],
            title=f"At-Risk Employees — Attendance % (below {threshold}%)", text="Attendance %",
        )
        fig.add_vline(x=threshold, line_dash="dash", line_color="blue",
                      annotation_text=f"Threshold: {threshold}%")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(height=max(350, len(at_risk) * 28), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

        st.download_button(
            "📥 Export At-Risk List as CSV",
            data=at_risk.to_csv(index=False),
            file_name=f"at_risk_employees_{selected_month.replace(' ', '_')}.csv",
            mime="text/csv",
        )

    st.divider()
    st.subheader("📈 Attendance Distribution")
    fig_hist = px.histogram(
        emp_stats, x="Attendance %", nbins=20,
        color_discrete_sequence=["#667eea"],
        title="How attendance is spread across all employees",
    )
    fig_hist.add_vline(x=threshold, line_dash="dash", line_color="red",
                       annotation_text=f"Alert line: {threshold}%")
    fig_hist.update_layout(height=320)
    st.plotly_chart(fig_hist, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# 3.  MONTH-WISE TREND COMPARISON TAB
# ═══════════════════════════════════════════════════════════════
def render_monthly_trends(df: pd.DataFrame):
    st.header("📅 Month-wise Trend Comparison")
    st.caption("Compare attendance, WFH, and leave patterns across April, May, and June 2022.")

    months = sorted(df["Month"].unique())
    work_df = df[~df["Status"].isin(["WO", "HO"])].copy()

    monthly_kpi = []
    for m in months:
        mdf = work_df[work_df["Month"] == m]
        total = max(len(mdf), 1)
        monthly_kpi.append({
            "Month": m,
            "Attendance %": round(mdf["Status"].isin(["P"]).sum() / total * 100, 1),
            "WFH %": round(mdf["Status"].isin(["WFH", "HWFH"]).sum() / total * 100, 1),
            "Sick Leave %": round(mdf["Status"].isin(["SL", "HSL"]).sum() / total * 100, 1),
            "Paid Leave %": round(mdf["Status"].isin(["PL", "HPL"]).sum() / total * 100, 1),
            "LWP %": round(mdf["Status"].isin(["LWP", "HLWP"]).sum() / total * 100, 1),
        })
    kpi_df = pd.DataFrame(monthly_kpi)

    # KPI cards
    cols = st.columns(len(months))
    for i, row in kpi_df.iterrows():
        with cols[i]:
            st.markdown(f"""
                <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                border-radius:12px;padding:18px;text-align:center;color:white;">
                    <div style="font-size:18px;font-weight:bold;">{row['Month']}</div>
                    <div style="font-size:32px;font-weight:800;margin:8px 0;">{row['Attendance %']}%</div>
                    <div style="font-size:13px;">Attendance</div>
                    <div style="margin-top:10px;font-size:13px;">
                        WFH: {row['WFH %']}% &nbsp;|&nbsp; SL: {row['Sick Leave %']}%
                    </div>
                </div>""", unsafe_allow_html=True)

    st.divider()

    # Line chart
    fig_line = go.Figure()
    colors = {"Attendance %": "#00b894", "WFH %": "#0984e3",
              "Sick Leave %": "#e17055", "Paid Leave %": "#fdcb6e"}
    for metric, color in colors.items():
        fig_line.add_trace(go.Scatter(
            x=kpi_df["Month"], y=kpi_df[metric], mode="lines+markers+text",
            name=metric, text=[f"{v}%" for v in kpi_df[metric]],
            textposition="top center", line=dict(color=color, width=3), marker=dict(size=10),
        ))
    fig_line.update_layout(title="Month-wise Trends: Attendance, WFH & Leaves",
                           yaxis_title="Percentage (%)", height=420)
    st.plotly_chart(fig_line, use_container_width=True)

    # Grouped bar
    melted = kpi_df.melt(id_vars="Month", var_name="Metric", value_name="Value")
    fig_bar = px.bar(melted, x="Month", y="Value", color="Metric", barmode="group",
                     title="Side-by-Side Monthly Comparison",
                     color_discrete_sequence=px.colors.qualitative.Set1, text_auto=".1f")
    fig_bar.update_layout(height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    st.subheader("📋 Summary Table")
    st.dataframe(
        kpi_df.set_index("Month").style.highlight_max(color="lightgreen").highlight_min(color="#ffcccc"),
        use_container_width=True,
    )
