import pandas as pd
import numpy as np
import streamlit as st
import os

VERSION = "v4.0"  # bump this to bust st.cache_data

MONTH_SHEETS = [
    ("April 2022", "Attendance Sheet Apr 2022"),
    ("May 2022",   "Attendance Sheet May 2022"),
    ("June 2022",  "June 2022"),
]

PRESENT_CODES = {"P", "P-BL", "P-PL", "P-HO", "P-WO", "PA"}
WFH_CODES     = {"WFH", "HWFH"}
SL_CODES      = {"SL", "HSL"}
PL_CODES      = {"PL", "HPL"}
LEAVE_CODES   = {"PL", "HPL", "BL", "ML", "LWP", "HLWP", "FFL", "COMP OFF", "BRL"}
OFF_CODES     = {"WO", "HO", "WFH-WO", "WEEK OFF"}

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
MONTH_ORDER = {"April 2022": 1, "May 2022": 2, "June 2022": 3}


def classify_status(raw):
    """Return (is_working, present_val, wfh_val, sl_val, leave_val, category)."""
    if pd.isna(raw):
        return 0, 0.0, 0.0, 0.0, 0.0, "Off"
    s = str(raw).strip().upper()
    if not s or s in ("NAN", ""):
        return 0, 0.0, 0.0, 0.0, 0.0, "Off"

    if s in OFF_CODES:
        return 0, 0.0, 0.0, 0.0, 0.0, "Off"
    if s in PRESENT_CODES:
        return 1, 1.0, 0.0, 0.0, 0.0, "Present"
    if s == "WFH":
        return 1, 0.0, 1.0, 0.0, 0.0, "WFH"
    if s == "HWFH":
        return 1, 0.5, 0.5, 0.0, 0.0, "WFH"
    if s == "SL":
        return 1, 0.0, 0.0, 1.0, 0.0, "Sick Leave"
    if s == "HSL":
        return 1, 0.5, 0.0, 0.5, 0.0, "Sick Leave"
    if s in PL_CODES:
        return 1, 0.0, 0.0, 0.0, 1.0, "Paid Leave"
    if s in LEAVE_CODES:
        return 1, 0.0, 0.0, 0.0, 1.0, "Leave"
    # Unknown → treat as absent on a working day
    return 1, 0.0, 0.0, 0.0, 0.0, "Absent"


@st.cache_data(show_spinner=False)
def load_data(version=VERSION):
    """
    Load all 3 monthly sheets from Attendance Sheet.xlsx.
    Returns (df_long, emp_metrics) or (None, None) if file not found.
    """
    file_path = "Attendance Sheet.xlsx"
    if not os.path.exists(file_path):
        return None, None

    records = []

    for month_label, sheet_name in MONTH_SHEETS:
        try:
            raw = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception:
            continue

        if raw.empty:
            continue

        # Split columns into date columns vs employee-info columns
        date_cols = []
        emp_cols = []
        for col in raw.columns:
            try:
                dt = pd.to_datetime(col)
                date_cols.append((col, dt))
            except Exception:
                emp_cols.append(col)

        if not emp_cols or not date_cols:
            continue

        name_col = emp_cols[0]

        for _, row in raw.iterrows():
            raw_name = row[name_col]
            if pd.isna(raw_name):
                continue
            emp_name = str(raw_name).strip()
            if (
                not emp_name
                or emp_name.lower() in ("nan", "employee name", "name", "employee")
                or emp_name.lower().startswith("attendance")
            ):
                continue

            for date_col, dt in date_cols:
                w, p, wfh, sl, lv, cat = classify_status(row[date_col])
                status_raw = (
                    str(row[date_col]).strip().upper()
                    if pd.notna(row[date_col])
                    else "WO"
                )
                records.append(
                    {
                        "employee_name": emp_name,
                        "month": month_label,
                        "date": dt,
                        "day_of_week": dt.strftime("%A"),
                        "week_num": int(dt.strftime("%U")),
                        "day_num": dt.weekday(),  # 0=Mon 4=Fri
                        "status": status_raw,
                        "category": cat,
                        "is_working": w,
                        "present_val": p,
                        "wfh_val": wfh,
                        "sl_val": sl,
                        "leave_val": lv,
                    }
                )

    if not records:
        return None, None

    df_long = pd.DataFrame(records)
    df_long["date"] = pd.to_datetime(df_long["date"])
    df_long = df_long.sort_values(["employee_name", "date"]).reset_index(drop=True)

    emp_metrics = compute_employee_metrics(df_long)
    return df_long, emp_metrics


def compute_employee_metrics(df_long):
    """Per-employee aggregate stats + risk scoring."""
    g = (
        df_long.groupby("employee_name")
        .agg(
            total_working=("is_working", "sum"),
            total_present=("present_val", "sum"),
            total_wfh=("wfh_val", "sum"),
            total_sl=("sl_val", "sum"),
            total_leave=("leave_val", "sum"),
        )
        .reset_index()
    )

    tw = g["total_working"].replace(0, np.nan)
    g["attendance_pct"] = (g["total_present"] / tw * 100).round(1)
    g["wfh_pct"]        = (g["total_wfh"]     / tw * 100).round(1)
    g["sl_pct"]         = (g["total_sl"]       / tw * 100).round(1)
    g["leave_pct"]      = (g["total_leave"]    / tw * 100).round(1)
    g["absence_pct"]    = (
        100 - g["attendance_pct"] - g["wfh_pct"] - g["sl_pct"] - g["leave_pct"]
    ).clip(lower=0).round(1)

    def _risk(row):
        score = 0
        att = row["attendance_pct"] if pd.notna(row["attendance_pct"]) else 100
        sl  = row["sl_pct"]         if pd.notna(row["sl_pct"])         else 0
        if att < 75:  score += 4
        elif att < 85: score += 2
        elif att < 92: score += 1
        if sl > 6:    score += 3
        elif sl > 3:  score += 1
        return score

    g["risk_score"] = g.apply(_risk, axis=1)
    g["risk_level"] = g["risk_score"].apply(
        lambda s: "High" if s >= 5 else ("Medium" if s >= 2 else "Low")
    )
    return g.fillna(0)


def compute_monthly_metrics(df_long, employees=None):
    """Month-wise aggregate metrics, sorted chronologically."""
    df = df_long.copy()
    if employees:
        df = df[df["employee_name"].isin(employees)]

    g = (
        df.groupby("month")
        .agg(
            total_working=("is_working", "sum"),
            total_present=("present_val", "sum"),
            total_wfh=("wfh_val", "sum"),
            total_sl=("sl_val", "sum"),
        )
        .reset_index()
    )

    tw = g["total_working"].replace(0, np.nan)
    g["attendance_pct"] = (g["total_present"] / tw * 100).round(1)
    g["wfh_pct"]        = (g["total_wfh"]     / tw * 100).round(1)
    g["sl_pct"]         = (g["total_sl"]       / tw * 100).round(1)

    g["_ord"] = g["month"].map(MONTH_ORDER)
    g = g.sort_values("_ord").drop("_ord", axis=1)
    return g
