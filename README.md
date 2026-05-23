# NeuraSpend: Intelligent Enterprise Expense Management & Analytics System

NeuraSpend is a state-of-the-art, desktop-based financial intelligence and analytics platform designed for local-first enterprise environments. Built in Python 3.9+ using SQLite3, Matplotlib, ReportLab, openpyxl, tkcalendar, and pytesseract OCR, the system delivers comprehensive transaction tracking, deterministic natural language parsing, hands-free voice inputs, automated budgeting, advanced data visualizations, predictive spending forecasts, and savings goals tracking.

This project is meticulously designed to serve as a high-fidelity academic final year showcase (BCA/BSc Computer Science/B.Tech), college laboratory demonstration, viva-voce portfolio, or resume capstone.

---

## Technical Architecture Overview

NeuraSpend operates entirely in an offline sandboxed environment to guarantee maximum data privacy and integrity. The architectural layout consists of the following key subsystems:

```
                  ┌──────────────────────────────────────────────┐
                  │                 USER INTERFACE               │
                  │        (Modern Tkinter / Ttk Engine)         │
                  │   • Card KPI Widgets    • tkcalendar Grid    │
                  └──────┬────────────────────────────────┬──────┘
                         │                                │
                         ▼                                ▼
       ┌──────────────────────────────────┐     ┌──────────────────────────────────┐
       │      DATA ACQUISITION LAYER      │     │    BUSINESS INTELLIGENCE LAYER   │
       │  • pytesseract OCR Scanner       │     │  • Statistical Predictor         │
       │  • Threaded Voice Capturer       │     │  • Matplotlib Analytics Engine   │
       └─────────────────┬────────────────┘     └─────────────────┬────────────────┘
                         │                                │
                         ▼                                ▼
                  ┌──────────────────────────────────────────────┐
                  │               PERSISTENCE LAYER              │
                  │   • SQLite Database (database/expenses.db)   │
                  │   • Local JSON preferences database          │
                  │   • Multi-Format Reports (PDF/Excel/CSV)     │
                  └──────────────────────────────────────────────┘
```

---

## Core Features List (20 Advanced Subsystems)

1. **Spending Prediction Engine**: Calculates average monthly spends, spending growth trends, predicted next month spends, and projected yearly spends using statistics (Feature 1).
2. **Financial Health Score**: Dynamic qualitative score (0-100) based on budget adherence, spending consistency, saving ratios, and category distributions (Feature 2).
3. **Smart Insight Engine**: Automatically compiles mathematical spending trends (e.g. "Food spending increased by 15%") on the dashboard (Feature 3).
4. **Goal Tracking Module**: Savings goals CRUD panel featuring visual Progress Bar indicators and completion percentages (Feature 4).
5. **Recurring Expense Management**: Dues date monitoring with auto-reminders for Daily, Weekly, and Monthly bills (Rent, subscriptions) (Feature 5).
6. **Receipt OCR Scanner**: Optical receipt upload and text processing via Pillow and `pytesseract` to pre-fill merchant details and transaction amounts (Feature 6).
7. **Enhanced Voice Entry**: Asynchronous audio recording using the `SpeechRecognition` library which isolates amounts and categories without locking the UI (Feature 7).
8. **Advanced Analytics Center**: Directly embeds 6 visual Matplotlib plots into Ttk frames using `FigureCanvasTkAgg` (Feature 8).
9. **Interactive Calendar View**: Integrates the `tkcalendar.Calendar` widget, letting users click dates to view daily spend totals and registries (Feature 9).
10. **Excel Export System**: Beautifully formatted multi-sheet workbooks using `openpyxl` saved to `/exports/excel/` (Feature 10).
11. **Backup & Restore Manager**: Generates timestamped SQLite snapshots inside `backups/` and triggers database restoration (Feature 11).
12. **User Activity Audit Log**: Tracks security actions inside SQLite table `audit_logs` and local file `logs/system.log` (Feature 12).
13. **Smart Budget Alert System**: Color-coded banners (Green <80%, Yellow >=80%, Red exceeded) indicating budget status in real time (Feature 13).
14. **Multi-User Support**: User registration and role authorizations (`Admin` / `Employee`) with encrypted SHA-256 databases (Feature 14).
15. **Dark/Light Theme Engine**: Instant graphical toggle between curated Obsidian Dark Mode and Steel Light Mode configurations saved in JSON (Feature 15).
16. **Expense Attachment System**: Link local bill or receipt files to transaction logs and click the "View Attachment" button to launch them in native system viewers (Feature 16).
17. **Dashboard KPI Cards**: Grid layout presenting 8 administrative KPI cards to summarize finances in real time (Feature 17).
18. **Advanced Search Engine**: Live filters matching categories, date ranges, amount bounds, payment methods, and descriptions (Feature 18).
19. **Monthly Summary PDF**: Auto-synthesizes structural financial metrics and exports a concise single-page summary PDF (Feature 19).
20. **Professional PDF Suite**: Renders a gorgeous, multi-page ReportLab PDF including Cover Pages, Executive Summaries, predictive dials, savings tables, and visual charts (Feature 20).

---

## Installation & Environment Setup

### Prerequisites
- Python 3.9 or higher.
- Tesseract OCR software (Only required if optical receipt image scanning is desired).
  - *Windows*: Download and run the Tesseract installer, then add `C:\Program Files\Tesseract-OCR` to your System Environment variables PATH.
  - *macOS*: `brew install tesseract`
  - *Linux*: `sudo apt install tesseract-ocr`

### Setup Instructions
1. Navigate to the project directory:
   ```bash
   cd "expense tracker"
   ```
2. Install the certified requirements:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: The system contains built-in exception firewalls. If Tesseract or microphone components are missing, the application will still launch and execute perfectly, bypassing OCR/Voice features gracefully).*

---

## Execution Guide

To launch the desktop application, run the main bootstrap file:

```bash
python main.py
```

### Certified Test Accounts
- **Administrator Role**:
  - **Username**: `admin`
  - **Password**: `password123`
- **Employee Role**:
  - **Username**: `employee`
  - **Password**: `password123`

*Upon successful authentication, the security engine logs the event and loads the dynamic dashboard workspace.*
