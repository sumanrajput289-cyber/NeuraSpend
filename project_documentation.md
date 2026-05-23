# PROJECT DOCUMENTATION
## NEURASPEND: INTELLIGENT ENTERPRISE EXPENSE MANAGEMENT & ANALYTICS SYSTEM

---

### TABLE OF CONTENTS
1. **Chapter 1: Introduction**
   - 1.1 Abstract
   - 1.2 Problem Statement
   - 1.3 System Objectives
   - 1.4 Scope of the System
2. **Chapter 2: System Analysis & Design**
   - 2.1 System Architecture
   - 2.2 Functional Requirements (20 Advanced Features)
   - 2.3 Non-Functional Requirements
   - 2.4 Software & Hardware Specifications
3. **Chapter 3: Database Design**
   - 3.1 Schema Descriptions (6 Tables)
   - 3.2 Relational Data Structure
4. **Chapter 4: Methodology & Processing Flows**
   - 4.1 System Processing Methodology
   - 4.2 Architectural Flowcharts
   - 4.3 Optical Character Recognition & Voice Tokenization
5. **Chapter 5: Implementation Module Descriptions**
   - 5.1 System Modules Breakdown
6. **Chapter 6: System Testing & Results**
   - 6.1 Testing Summary Matrix
   - 6.2 Implementation Results Showcase
7. **Chapter 7: Future Scope & Conclusion**
   - 7.1 Future Scope
   - 7.2 Conclusion
8. **Chapter 8: References**

---

## CHAPTER 1: INTRODUCTION

### 1.1 Abstract
This project documents the development of **NeuraSpend**, a high-fidelity desktop financial tracking and analytical platform engineered for local-first enterprise environments. Traditional expense tracking software often suffers from complex manual input systems, high dependencies on online cloud backends, and inadequate visual data representation. **NeuraSpend** addresses these shortcomings by integrating a highly-engineered suite of **20 advanced features**: deterministic natural language parsing (NLP) and threaded audio signal transcriptions to simplify data entry, alongside an offline optical character recognition (OCR) receipt scanner powered by `pytesseract` and `Pillow`.

Operating strictly offline, the system utilizes SQLite3 for local relational persistence, JSON databases for configuration preferences, and a custom Tkinter/Ttk styling engine to present an obsidian dark/light visual interface. Business intelligence dashboards are generated dynamically using Matplotlib to embed six interactive charts inside Tkinter using `FigureCanvasTkAgg`. Additionally, a statistical forecasting engine evaluates monthly variances to project upcoming monthly and annual expenditures, and computes a qualitative **Financial Health Score** (0-100) based on budget compliance, spending volatility, saving ratios, and category distributions. The result is a robust, production-ready desktop tool suitable for university curriculum evaluations, BCA/B.Tech portfolios, and professional administrative demonstrations.

### 1.2 Problem Statement
Modern personal and corporate financial administration is plagued by several critical challenges:
1. **High Friction in Transaction Recording**: Manual data entry forms containing multiple dropdowns and numerical boxes discourage users from maintaining daily spending records.
2. **Cloud Dependency and Data Leakage Risks**: Most modern applications route sensitive financial databases through external public servers, exposing organizations to security risks and requiring constant internet access.
3. **Hardware Integration & Codec Complexities**: Desktop voice capture packages frequently fail due to missing local audio compilers, requiring safe exception containment so the system never crashes.
4. **Lack of Actionable Planning and Analytics**: Raw spreadsheets fail to synthesize analytical patterns or calculate cumulative growth rates, leaving users unaware of spending trends or budget status.

### 1.3 System Objectives
To address the aforementioned challenges, **NeuraSpend** is developed with the following primary objectives:
- **Zero Cloud Footprint**: Ensure absolute data isolation by running entirely offline inside the local host machine.
- **Microphone & OCR Data Entry Interface**: Create a regex-based NLP parser, threaded microphone transcription tool, and pytesseract receipt scanner to extract amounts and categories from plain text, speech, or images automatically.
- **Dynamic Visual Insights**: Deliver an interactive GUI displaying real-time budget warnings and six analytical charts that update immediately as new transaction rows are saved.
- **Savings Goals & Schedulers**: Build goal tracking modules and recurring expense lists to automate monthly billing cycles.
- **Comprehensive Portability**: Enable automated backup creation, restore tools, and multi-format document exporting (PDF, Excel, CSV) inside user-defined directories.

### 1.4 Scope of the System
**NeuraSpend** is designed as a desktop-first administrative tool. Its functional boundaries cover:
- Individual and micro-enterprise ledger management.
- Multi-user authentication gates using offline SHA-256 cryptosystems (Roles: Admin, Employee).
- Automated generation of professional ReportLab PDFs, openpyxl sheets, and standard CSV databases.
- Recurring monthly payments tracking and scheduling notification alerts.
- Offline database recovery via timestamped snapshot cloning.

---

## CHAPTER 2: SYSTEM ANALYSIS & DESIGN

### 2.1 System Architecture
The software is constructed using a robust three-tier desktop application design pattern:

1. **Presentation Layer (GUI Front-End)**: Developed using standard Python `tkinter`, styled `ttk` widget libraries, and `tkcalendar`. Implements modular, card-based navigation frames and a centralized coordinate layout swapper.
2. **Business Logic Layer (Analytical Engine)**: Coordinates the regex tokenization parser (`parser.py`), threaded speech capturers (`voice_input.py`), pytesseract OCR engines (`ocr_scanner.py`), statistical trend calculators (`predictor.py`), and visualization controllers (`analytics.py`).
3. **Data Persistence Layer (Database and Export)**: Coordinates SQLite3 file systems, JSON user configurations, and automated file-writing compilers (`reports.py` and `backup_manager.py`).

### 2.2 Functional Requirements (20 Advanced Features)
- **FR-1 (Predictions)**: Calculate average monthly, growth trend, next month, and yearly spends using statistics (Feature 1).
- **FR-2 (Health Score)**: Multi-factor score (0-100) based on budget adherence, consistency, saving ratios, and category spreads (Feature 2).
- **FR-3 (Smart Insights)**: Dynamic dashboard insights alerts (Feature 3).
- **FR-4 (Goals Tracker)**: Savings goal funds progress monitoring and progress bar indicators (Feature 4).
- **FR-5 (Recurring Scheduler)**: Daily, weekly, monthly billing due alerts and monitoring (Feature 5).
- **FR-6 (Receipt OCR)**: Image text processing via pytesseract and Pillow to pre-fill forms (Feature 6).
- **FR-7 (Speech Capture)**: Threaded speech-to-text NLP parser input (Feature 7).
- **FR-8 (Analytics Center)**: 6 Matplotlib charts embedded in Tkinter via FigureCanvasTkAgg (Feature 8).
- **FR-9 (tkcalendar View)**: Monthly visual calendars showing daily spends and transaction previews (Feature 9).
- **FR-10 (Excel Export)**: Multi-sheet openpyxl workbooks saved to `/exports/excel/` (Feature 10).
- **FR-11 (Backup & Recovery)**: Timestamped database snapshots and restoration controls (Feature 11).
- **FR-12 (Audit Logs)**: Security Activity log viewer screen (Feature 12).
- **FR-13 (Smart Budget Banner)**: Dynamic Color alerts (Green/Yellow/Red) showing budget utilization (Feature 13).
- **FR-14 (Multi-User Support)**: Role authorizations (Admin/Employee) and User-specific database views (Feature 14).
- **FR-15 (Theme Switching)**: Obsidian Dark Mode and Steel Light Mode instant switches (Feature 15).
- **FR-16 (Attachment System)**: Link file paths to expenses and click "View Attachment" to launch them (Feature 16).
- **FR-17 (Dashboard KPIs)**: Modern cards layout presenting 8 KPI metrics (Feature 17).
- **FR-18 (Search Engine)**: Live filters matching category, date range, amount bounds, payment, and text (Feature 18).
- **FR-19 (Summary PDF)**: Exports a concise single-page PDF financial summary (Feature 19).
- **FR-20 (PDF Suite)**: Compiles multi-page PDF reports containing Cover pages, Executive summaries, and charts (Feature 20).

### 2.3 Non-Functional Requirements
- **NFR-1 (Obsidian Style)**: Curated color schemes, professional Outfit/Inter typography, rounded card layouts, and hover effects.
- **NFR-2 (Offline Integrity)**: 100% offline functionality without external web dependencies.
- **NFR-3 (Crash Firewalls)**: Wrap all database, OCR, voice, and file exports operations in try-except blocks to prevent unexpected termination.

---

## CHAPTER 3: DATABASE DESIGN

### 3.1 Schema Descriptions
**NeuraSpend** structures its relational tables inside `database/expenses.db` automatically at startup:

```
    ┌────────────────────────┐         ┌────────────────────────┐         ┌────────────────────────┐
    │         users          │         │        expenses        │         │        budgets         │
    ├────────────────────────┤         ├────────────────────────┤         ├────────────────────────┤
    │ id (INTEGER)       [PK]│         │ id (INTEGER)       [PK]│         │ id (INTEGER)       [PK]│
    │ username (TEXT)        │         │ title (TEXT)           │         │ monthly_limit (REAL)   │
    │ password_hash (TEXT)   │         │ description (TEXT)     │         │ warning_limit (REAL)   │
    │ role (TEXT)            │         │ amount (REAL)          │         │ created_at (TEXT)      │
    │ created_at (TEXT)      │         │ category (TEXT)        │         │ user_id (INTEGER)      │
    └────────────────────────┘         │ payment_method (TEXT)  │         └────────────────────────┘
                                       │ transaction_date (TEXT)│
    ┌────────────────────────┐         │ created_at (TEXT)      │         ┌────────────────────────┐
    │         goals          │         │ user_id (INTEGER)      │         │   recurring_expenses   │
    ├────────────────────────┤         │ attachment_path (TEXT) │         ├────────────────────────┤
    │ id (INTEGER)       [PK]│         └────────────────────────┘         │ id (INTEGER)       [PK]│
    │ title (TEXT)           │                                            │ title (TEXT)           │
    │ target (REAL)          │         ┌────────────────────────┐         │ amount (REAL)          │
    │ saved (REAL)           │         │       audit_logs       │         │ category (TEXT)        │
    │ created_at (TEXT)      │         ├────────────────────────┤         │ frequency (TEXT)       │
    │ user_id (INTEGER)      │         │ id (INTEGER)       [PK]│         │ next_due_date (TEXT)   │
    └────────────────────────┘         │ event_type (TEXT)      │         │ user_id (INTEGER)      │
                                       │ details (TEXT)         │         └────────────────────────┘
                                       │ timestamp (TEXT)       │
                                       │ user_id (INTEGER)      │
                                       └────────────────────────┘
```

---

## CHAPTER 4: METHODOLOGY & PROCESSING FLOWS

### 4.1 System Processing Methodology
The application integrates visual inputs, mathematical modeling, and local storage:

1. **Authentication Process**: The system loads the login frame (`LoginFrame`). The user enters a password, which is hashed via SHA-256 and verified against the user database (`database/expenses.db`).
2. **Dashboard Initialization**: Once authenticated, the user's specific session is created, and the main dashboard opens (`DashboardFrame`), displaying the 8 KPI cards and insights.
3. **Data Logging (Add Expense)**: Transactions are entered manually, parsed from text, or scanned from images via pytesseract OCR.
4. **Real-Time Visual Updates**: Matplotlib clears active chart figures and recreates them, updating the Canvas container. The warning status bar is also refreshed.

### 4.2 Architectural Flowcharts

#### OCR Receipt Processing & Field population Workflow
```
[User Selects Receipt Image] ➔ [Load via Pillow Image.open]
                                       │
                      [Tesseract extracts text string]
                                       │
                     [Apply regex amount/merchant matches]
                                       │
                  [Auto-populate Form Fields: Title, Amount, Cat]
                                       │
                       [User saves to SQLite databases]
```

#### User-Specific Session Authorization & Ledger Viewing
```
[User Authenticates] ➔ [Is role Admin?]
                              │
               (Yes) ─────────┴───────── (No, Employee)
                 ▼                         ▼
    [Query all transactions]    [Query user_id specific rows]
                 │                         │
                 ▼                         ▼
         [Render Treeview]         [Render Restricted Treeview]
```

---

## CHAPTER 5: IMPLEMENTATION MODULE DESCRIPTIONS

### 5.1 System Modules Breakdown

- **`main.py`**: Bootstrap launcher centering screens, setting dimension grids, and managing login transitions.
- **`database.py`**: SQLite database driver. Coordinates automated folder creation, table schemas, and migrations.
- **`authentication.py`**: Manages secure sessions, SHA-256 credential hashing, login attempts, and password-masking.
- **`settings.py`**: JSON preferences manager.
- **`theme.py`**: Global styling configuration. Defines color palettes and widget dimensions for Obsidian Dark and Steel Light modes.
- **`parser.py`**: Deterministic text parser. Uses regular expressions to extract transactional variables.
- **`voice_input.py`**: Speech recognition processor. Captures audio via threads, handles errors, and returns transcripts.
- **`ocr_scanner.py`**: Optical Receipt scanner. Loads Pillow images and processes text via pytesseract.
- **`analytics.py`**: Data visualization generator. Creates 6 Matplotlib figures and embeds them in Tkinter canvases.
- **`predictor.py`**: Statistical forecasting engine. Computes spending predictions and the multi-factor **Financial Health Score**.
- **`reports.py`**: Document compiler. Generates multi-page PDFs, Excel workbooks, and CSV files.
- **`dashboard.py`**: Main application interface. Handles sidebar navigation, statistics cards, calendars, and savings goal trackers.

---

## CHAPTER 6: SYSTEM TESTING & RESULTS

### 6.1 Testing Summary Matrix
The desktop application underwent extensive testing to ensure offline stability, safety, and functionality:
| Module Tested | Testing Method | Input Vectors | Expected Output | Actual Results |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication**| White-box boundary test | `admin` / `password123` | Open admin dashboard frame | Verified |
| **OCR Receipt** | Codec safety test | Upload blurred receipt | Catch error, inform user, don't crash | Verified |
| **Search Engine** | Query boundary test | Min: `100`, Max: `1000` | Treeview filters rows correctly | Verified |
| **tkcalendar** | Selection callback test | Click Date: `2026-05-23` | Load listbox with daily spend total | Verified |
| **Matplotlib Canvas**| Redraw test | Save transaction record | Redraw 6 figures instantly | Verified |
| **PDF Suite** | Image integration test | Trigger PDF compilation | Render cover page, goals, and pie chart | Verified |
| **Audit Logging** | File writing test | Delete expense row | Log activity in SQLite and system.log | Verified |

---

## CHAPTER 7: FUTURE SCOPE & CONCLUSION

### 7.1 Future Scope
Planned enhancements include:
1. **Fully Local Offline Transcription**: Integrating lightweight offline model servers like Whisper.cpp.
2. **Receipt OCR Advancements**: Implementing local deep learning OCR engines to extract transaction data from complex receipts.
3. **Advanced Predictions**: Applying advanced statistical regressions to model complex spending behaviors.

### 7.2 Conclusion
The **NeuraSpend** project successfully provides a secure, fully offline desktop expense tracker and analytics application. By integrating a highly-engineered suite of **20 advanced features** (including tkcalendar views, pytesseract OCR, and ReportLab PDF suites), it delivers an intuitive and comprehensive financial intelligence platform. This project achieves all system design requirements and is fully prepared for final university project submissions.

---

## CHAPTER 8: REFERENCES
1. *Python Standard GUI Programming Cookbook (2nd Edition)* - Tkinter and Ttk manual references.
2. *SQLite Documentation* - ACID transactional compliance manuals.
3. *Matplotlib Integration Guide* - Embedding figures inside Tkinter widgets via Canvas.
4. *ReportLab User Guide* - Creating PDFs dynamically with Flowable elements.
5. *Openpyxl Workbook Sheets Manual* - Managing Excel worksheets with openpyxl.
