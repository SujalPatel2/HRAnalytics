import pandas as pd
import streamlit as st

ATTENDANCE_SHEETS = ["Apr 2022", "May 2022", "Jun 2022"]


@st.cache_data(show_spinner="Loading attendance data...")
def load_attendance(file_path: str) -> pd.DataFrame:
    all_months = []

    for sheet in ATTENDANCE_SHEETS:
        try:
            raw = pd.read_excel(file_path, sheet_name=sheet, header=None)
        except Exception as e:
            st.warning(f"Could not read sheet '{sheet}': {e}")
            continue

        date_row = raw.iloc[0]
        data = raw.iloc[2:].copy()
        data.columns = range(len(data.columns))

        date_cols = {}
        for col_idx in range(2, min(33, len(date_row))):
            val = date_row[col_idx]
            if pd.notna(val) and hasattr(val, "date"):
                date_cols[col_idx] = val.date()
            elif pd.notna(val) and isinstance(val, str) and "=" not in val:
                try:
                    date_cols[col_idx] = pd.to_datetime(val).date()
                except Exception:
                    pass

        records = []
        for _, row in data.iterrows():
            emp_code = row[0]
            emp_name = row[1]
            if pd.isna(emp_code) or not str(emp_code).startswith("Atq"):
                continue

            for col_idx, date in date_cols.items():
                status = row[col_idx]
                if pd.isna(status) or str(status).strip() == "":
                    continue
                status_str = str(status).strip()
                if status_str.startswith("="):
                    continue

                records.append({
                    "Employee Code": str(emp_code).strip(),
                    "Name": str(emp_name).strip() if pd.notna(emp_name) else "Unknown",
                    "Month": sheet,
                    "Date": pd.Timestamp(date),
                    "Status": status_str,
                })

        if records:
            all_months.append(pd.DataFrame(records))

    if not all_months:
        st.error("No data loaded. Check your Excel file path and sheet names.")
        return pd.DataFrame()

    df = pd.concat(all_months, ignore_index=True)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values(["Employee Code", "Date"]).reset_index(drop=True)


def get_summary_stats(df: pd.DataFrame) -> dict:
    work = df[~df["Status"].isin(["WO", "HO"])]
    total = max(len(work), 1)
    return {
        "total_employees": df["Employee Code"].nunique(),
        "total_records": len(df),
        "attendance_pct": round(work["Status"].isin(["P"]).sum() / total * 100, 1),
        "wfh_pct": round(work["Status"].isin(["WFH", "HWFH"]).sum() / total * 100, 1),
        "sick_leave_pct": round(work["Status"].isin(["SL", "HSL"]).sum() / total * 100, 1),
    }