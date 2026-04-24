# 🏢 AtliQ HR Analytics — Streamlit App

A full-featured HR Attendance Analytics dashboard with secure login/signup,
built from your AtliQ Power BI project data.

---

## 📁 Project Structure

```
atliq_hr_app/
├── app.py                                   ← Entry point
├── auth.py                                  ← Login / Sign-up logic
├── data_loader.py                           ← Excel data processing
├── dashboard.py                             ← Charts & dashboard UI
├── requirements.txt                         ← Python dependencies
├── users.json                               ← Auto-created on first run
└── Attendance_Sheet_2022-2023_Masked.xlsx   ← ⚠️ Copy here!
```

---

## ⚙️ Setup (one time)

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy your Excel file into this folder
cp /path/to/Attendance_Sheet_2022-2023_Masked.xlsx .
```

---

## ▶️ Run the App

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 🔐 Default Credentials

| Username | Password  |
|----------|-----------|
| admin    | admin123  |

You can create new accounts from the **Sign Up** page.
All accounts are stored locally in `users.json`.

---

## 📊 Dashboard Features

| Tab | Contents |
|-----|----------|
| **Overview** | KPI cards, monthly trend, attendance distribution, top employees, leave breakdown, WFH scatter, day-of-week analysis |
| **Employee Deep Dive** | Individual attendance strip chart, category donut, metrics, raw data |
| **Attendance Heatmap** | 2D heatmap of presence per employee per day |
| **Raw Data** | Filterable table with CSV export |

### Sidebar Filters
- **Month** — filter by April / May / June 2022
- **Employee** — narrow all charts to one person
- **Logout** button

---

## 🎨 Attendance Code Reference

| Code | Meaning |
|------|---------|
| P    | Present |
| WFH  | Work From Home |
| PL / HPL | Paid Leave (half) |
| SL / HSL | Sick Leave (half) |
| FFL  | Floating Festival Leave |
| BL   | Birthday Leave |
| LWP  | Leave Without Pay |
| BRL  | Bereavement Leave |
| ML   | Menstrual Leave |
| WO   | Weekly Off |
| HO   | Holiday Off |
