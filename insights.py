import streamlit as st
import google.generativeai as genai
import pandas as pd


def render_ai_insights(df: pd.DataFrame):
    st.header("🤖 AI-Powered HR Insights")
    st.caption("Gemini analyzes your attendance data and generates actionable HR observations.")
    st.divider()

    total_emp = df["Employee Code"].nunique()
    months = sorted(df["Month"].unique())

    work_df = df[~df["Status"].isin(["WO", "HO"])]
    emp_att = (
        work_df.groupby(["Employee Code", "Name"])
        .agg(present=("Status", lambda x: x.isin(["P", "WFH"]).sum()),
             total=("Status", "count"))
        .reset_index()
    )
    emp_att["att_pct"] = (emp_att["present"] / emp_att["total"] * 100).round(1)
    low_att = emp_att[emp_att["att_pct"] < 70][["Name", "att_pct"]].to_dict("records")

    monthly = (
        df.groupby("Month").agg(
            present_pct=("Status", lambda x: round((x == "P").sum() / max(len(x), 1) * 100, 1)),
            wfh_pct=("Status", lambda x: round((x == "WFH").sum() / max(len(x), 1) * 100, 1)),
            sl_pct=("Status", lambda x: round((x == "SL").sum() / max(len(x), 1) * 100, 1)),
        ).reset_index()
    )

    emp_sl = work_df.groupby("Name")["Status"].apply(
        lambda x: x.isin(["SL", "HSL"]).sum()
    ).nlargest(5)

    prompt = f"""You are an expert HR Analytics consultant. Analyze AtliQ Technologies 
attendance data (Apr–Jun 2022, {total_emp} employees) and give clear, actionable insights.

MONTHLY COMPANY STATS:
{monthly.to_string(index=False)}

EMPLOYEES WITH LOW ATTENDANCE (< 70%):
{low_att if low_att else "None"}

TOP 5 SICK LEAVE TAKERS:
{emp_sl.to_string()}

WFH % BY MONTH:
{df.groupby("Month")["Status"].apply(lambda x: round((x=="WFH").sum()/len(x)*100,1)).to_string()}

Provide:
1. **3 Key Observations** about attendance trends
2. **2 Warning Signals** HR should act on immediately
3. **3 Actionable Recommendations** for improving attendance/productivity
4. **1 Positive Highlight** — something the company is doing well

Format with bold headers. Keep it concise and professional."""

    col1, col2 = st.columns([3, 1])
    with col1:
        focus_area = st.selectbox("Focus Area", [
            "Overall Analysis", "WFH Patterns",
            "Sick Leave Concerns", "Absenteeism Risk"
        ])
    with col2:
        st.write("")
        st.write("")
        run_btn = st.button("✨ Generate Insights", type="primary", use_container_width=True)

    focus_map = {
        "WFH Patterns": "Focus specifically on Work From Home trends. Are employees over-using WFH?",
        "Sick Leave Concerns": "Focus on sick leave patterns. Any concerning spikes or abuse?",
        "Absenteeism Risk": "Focus on absenteeism risk. Which employees show disengagement patterns?",
    }
    if focus_area != "Overall Analysis":
        prompt += f"\n\nSPECIAL FOCUS: {focus_map[focus_area]}"

    if run_btn:
        with st.spinner("Gemini is analyzing your HR data..."):
            try:
                # Get API key from Streamlit secrets
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                insights_text = response.text

                st.success("✅ Analysis Complete!")
                st.divider()
                st.markdown(
                    f"""<div style="background:linear-gradient(135deg,#f5f7fa,#c3cfe2);
                    padding:24px;border-radius:12px;border-left:4px solid #667eea;
                    font-size:15px;line-height:1.7;color:#2d3748;">
                    {insights_text.replace(chr(10), '<br>')}
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.divider()
                st.download_button("📥 Download Insights as .txt",
                                   data=insights_text, file_name="hr_insights.txt",
                                   mime="text/plain")
            except Exception as e:
                st.error(f"Error calling AI: {str(e)}")
                st.info("Make sure GEMINI_API_KEY is set in Streamlit secrets.")
    else:
        st.info("👆 Click **Generate Insights** to get AI-powered analysis of your data.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Employees Analyzed", total_emp)
        c2.metric("Months Covered", len(months))
        c3.metric("Avg Attendance %", f"{emp_att['att_pct'].mean():.1f}%")
