# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Executive Dashboard Coordinator Module
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import os
import sys
import subprocess

# Local systems layer imports
from database import get_db_connection, write_system_log
from settings import load_user_settings, save_user_settings
from theme import get_current_theme, apply_theme_styles
from parser import parse_transaction_text
from voice_input import capture_and_parse_voice
from ocr_scanner import execute_receipt_ocr
from predictor import calculate_analytical_forecasts
from reports import compile_pdf_report, compile_csv_report, compile_excel_report, compile_monthly_summary_pdf
from backup_manager import execute_database_backup, list_available_backups, execute_database_restore
from authentication import SessionManager

# Dynamic imports with protection
CALENDAR_SUPPORTED = False
try:
    from tkcalendar import Calendar
    CALENDAR_SUPPORTED = True
except ImportError:
    pass

ANALYTICS_CHARTS = []
try:
    from analytics import (
        render_category_pie_chart,
        render_monthly_bar_chart,
        render_expense_line_graph,
        render_top_categories_hbar,
        render_budget_utilization_chart,
        render_yearly_overview_chart
    )
except ImportError:
    pass


def launch_attachment_file(filepath):
    """
    Feature 16: Safe execution utility to trigger system-level viewing
    of local bills/invoices attachments on Windows, macOS, or Linux.
    """
    if not filepath or not os.path.exists(filepath):
        messagebox.showerror("Attachment Missing", "The associated bill or receipt attachment file does not exist on disk.")
        return
    try:
        if sys.platform.startswith('win'):
            os.startfile(filepath)
        elif sys.platform.startswith('darwin'):
            subprocess.call(['open', filepath])
        else:
            subprocess.call(['xdg-open', filepath])
    except Exception as err:
        messagebox.showerror("Error", f"Failed to launch native file viewer: {str(err)}")


class DashboardFrame(tk.Frame):
    """
    Breathtaking Single-Page desktop view swapper linking the sidebar triggers,
    budget banners, audit ledger tracking, and analytics dashboards.
    """
    def __init__(self, parent, logout_callback):
        super().__init__(parent)
        self.parent = parent
        self.logout_callback = logout_callback
        
        # Pull active configurations
        self.app_settings = load_user_settings()
        self.currency = self.app_settings.get("currency", "₹")
        
        # Load theme palette details
        _, self.colors = get_current_theme()
        
        self.pack(fill="both", expand=True)
        
        # Configure layout grids
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.pages = {}
        self.active_page_name = None

        self.setup_sidebar()
        self.setup_topbar()
        self.setup_main_panel()

        # Switch to dashboard home by default
        self.switch_to_page("Dashboard")
        self.start_clock_ticker()

    def setup_sidebar(self):
        sidebar = ttk.Frame(self, style="Sidebar.TFrame")
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", ipadx=15)
        self.grid_rowconfigure(0, weight=1)

        # Dashboard Brand Name
        brand_lbl = ttk.Label(sidebar, text="NeuraSpend", style="Sidebar.TLabel")
        brand_lbl.pack(padx=25, pady=(35, 5), anchor="w")
        
        tag_line = ttk.Label(sidebar, text="Financial Intelligence System", font=("Inter", 8, "bold"), foreground=self.colors["fg_muted"], background=self.colors["bg_sidebar"])
        tag_line.pack(padx=25, pady=(0, 30), anchor="w")

        # Ordered menu list matching all 20 advanced features
        menu_items = [
            ("Dashboard Overview", "Dashboard"),
            ("Add Expense Form", "Add Expense"),
            ("Ledger Database", "Transactions"),
            ("Interactive Calendar", "Calendar"),
            ("Analytics Dashboard", "Analytics"),
            ("Executive Reports", "Reports"),
            ("Microphone Parser", "Voice Entry"),
            ("Savings Goal Center", "Goal Center"),
            ("Recurring Due Center", "Recurring Center"),
        ]

        # Admin Dashboard User Manager visible ONLY to Admin role
        if SessionManager.get_role() == "Admin":
            menu_items.append(("User Manager Admin", "User Manager"))

        # Visual log and settings additions
        menu_items.extend([
            ("System Audit Logs", "Audit Logs"),
            ("Recovery Manager", "Backup Manager"),
            ("System Settings", "Settings"),
        ])

        self.sidebar_buttons = {}
        for text, page_id in menu_items:
            btn = ttk.Button(
                sidebar,
                text=f"  •  {text}",
                style="Sidebar.TButton",
                command=lambda p=page_id: self.switch_to_page(p)
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.sidebar_buttons[page_id] = btn

        # Spacer pushing logout to bottom
        spacer = tk.Label(sidebar, bg=self.colors["bg_sidebar"])
        spacer.pack(fill="both", expand=True)

        logout_btn = ttk.Button(
            sidebar,
            text="  ➔  Terminate Session",
            style="Sidebar.TButton",
            command=self.handle_logout
        )
        logout_btn.pack(fill="x", padx=12, pady=(0, 25))

    def setup_topbar(self):
        self.topbar = ttk.Frame(self, style="TopBar.TFrame")
        self.topbar.grid(row=0, column=1, sticky="ew")
        self.topbar.columnconfigure(2, weight=1)

        # Present authenticated username and role
        role = SessionManager.get_role()
        name = SessionManager.get_user()
        self.user_lbl = ttk.Label(
            self.topbar, 
            text=f"👤 Session: {name} ({role})", 
            style="TopBar.TLabel",
            padding=(25, 18)
        )
        self.user_lbl.grid(row=0, column=0, sticky="w")

        # Clock Ticker
        self.clock_lbl = ttk.Label(self.topbar, text="", style="TopBar.TLabel")
        self.clock_lbl.grid(row=0, column=1, sticky="w", padx=25)

        # Feature 13: Budget Utilization Alert Bar (Green, Yellow, Red)
        self.budget_banner = ttk.Frame(self.topbar, padding=2)
        self.budget_banner.grid(row=0, column=3, sticky="e", padx=25)
        
        self.budget_status_lbl = ttk.Label(self.budget_banner, text="Calculating Targets...")
        self.budget_status_lbl.pack(padx=12, pady=6)

    def setup_main_panel(self):
        self.content_container = ttk.Frame(self)
        self.content_container.grid(row=1, column=1, sticky="nsew", padx=30, pady=30)
        self.content_container.rowconfigure(0, weight=1)
        self.content_container.columnconfigure(0, weight=1)

    def switch_to_page(self, page_name):
        # Sidebar highlight sync
        for pid, button in self.sidebar_buttons.items():
            if pid == page_name:
                button.state(["selected"])
            else:
                button.state(["!selected"])

        # Safely destroy old frames to assure clean visual updates
        if self.active_page_name in self.pages:
            self.pages[self.active_page_name].destroy()
            del self.pages[self.active_page_name]

        page_class = self.get_page_class(page_name)
        if page_class:
            page_instance = page_class(self.content_container, self)
            self.pages[page_name] = page_instance
            page_instance.grid(row=0, column=0, sticky="nsew")
            self.active_page_name = page_name
            
        self.refresh_top_budget_banner()

    def get_page_class(self, page_name):
        mapping = {
            "Dashboard": OverviewPage,
            "Add Expense": AddExpensePage,
            "Transactions": TransactionsPage,
            "Calendar": CalendarPage,
            "Analytics": AnalyticsPage,
            "Reports": ReportsPage,
            "Voice Entry": VoiceEntryPage,
            "Goal Center": GoalPage,
            "Recurring Center": RecurringPage,
            "User Manager": UserManagerPage,
            "Audit Logs": AuditLogsPage,
            "Backup Manager": BackupPage,
            "Settings": SettingsPage
        }
        return mapping.get(page_name)

    def refresh_top_budget_banner(self):
        """
        Feature 13: Updates the budget warning alerts in real time.
        Visual highlights: Green (<80%), Yellow (>=80%), Red (>100%).
        """
        try:
            user_id = SessionManager.get_user_id()
            role = SessionManager.get_role()
            current_month = datetime.now().strftime("%Y-%m")

            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Fetch user-specific or admin-wide budget limits
                if role == "Admin":
                    cursor.execute("SELECT monthly_limit, warning_limit FROM budgets ORDER BY id DESC LIMIT 1")
                else:
                    cursor.execute("SELECT monthly_limit, warning_limit FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
                
                budget_row = cursor.fetchone()

                # Sum monthly expenses
                if role == "Admin":
                    cursor.execute("SELECT SUM(amount) FROM expenses WHERE transaction_date LIKE ?", (f"{current_month}%",))
                else:
                    cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND transaction_date LIKE ?", (user_id, f"{current_month}%"))
                
                sum_row = cursor.fetchone()
                total_spent = sum_row[0] if sum_row[0] is not None else 0.0

            if budget_row:
                limit = float(budget_row["monthly_limit"])
                warn = float(budget_row["warning_limit"])
            else:
                limit = float(self.app_settings.get("default_monthly_budget", 50000.0))
                warn = float(self.app_settings.get("default_warning_limit", 40000.0))

            if limit <= 0:
                self.budget_banner.configure(style="TFrame")
                self.budget_status_lbl.configure(text="No active budget set.", background="", foreground=self.colors["fg_body"], font=("Inter", 9))
                return

            remaining = limit - total_spent
            usage_pct = (total_spent / limit) * 100

            # Dynamic Visual styling allocations based on percentage parameters
            if total_spent > limit:
                self.budget_banner.configure(style="StatusRed.TFrame")
                self.budget_status_lbl.configure(
                    text=f"⚠️ CRITICAL: EXCEEDED BY {self.currency}{abs(remaining):,.2f} ({usage_pct:.1f}%)", 
                    style="StatusRed.TLabel"
                )
            elif total_spent >= warn:
                self.budget_banner.configure(style="StatusYellow.TFrame")
                self.budget_status_lbl.configure(
                    text=f"⚠️ WARNING: LIMIT NEAR. {self.currency}{remaining:,.2f} LEFT ({usage_pct:.1f}%)", 
                    style="StatusYellow.TLabel"
                )
            else:
                self.budget_banner.configure(style="StatusGreen.TFrame")
                self.budget_status_lbl.configure(
                    text=f"✓ HEALTHY: {self.currency}{remaining:,.2f} LEFT ({usage_pct:.1f}%)", 
                    style="StatusGreen.TLabel"
                )
        except Exception as banner_err:
            print(f"Top budget banner updates failed: {str(banner_err)}")

    def start_clock_ticker(self):
        def tick():
            if self.winfo_exists():
                time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.clock_lbl.configure(text=f"🕒 Time: {time_str}")
                self.parent.after(1000, tick)
        tick()

    def handle_logout(self):
        confirm = messagebox.askyesno("Log out Session", "Are you sure you want to end your current session?")
        if confirm:
            SessionManager.terminate_session()
            self.destroy()
            self.logout_callback()


# ==============================================================================
# SUB-PAGE MODULE IMPLEMENTATIONS
# ==============================================================================

class OverviewPage(ttk.Frame):
    """
    Feature 17: Renders 8 professional business analytics KPI cards:
    - Total Expenses, Monthly Expenses, Highest Expense, Average Expense, 
      Remaining Budget, Active Goals, Recurring Dues, Financial Health Score.
    Also displays dynamic statistical forecast calculations and health score status.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.currency = controller.currency
        self.colors = controller.colors

        # Scrolling Canvas coordinates
        canvas = tk.Canvas(self, bg=self.colors["bg_main"], bd=0, highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        
        self.scrollable = ttk.Frame(canvas)
        self.scrollable.columnconfigure(0, weight=1)

        self.scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Headings
        title_lbl = ttk.Label(self.scrollable, text="Executive Financial Intelligence Overview", font=("Outfit", 18, "bold"))
        title_lbl.pack(anchor="w", pady=(0, 20), padx=10)

        # Run database statistical queries
        metrics = self.calculate_summary_metrics()

        # Build 8 KPI Cards Grid
        grid_frame = ttk.Frame(self.scrollable)
        grid_frame.pack(fill="x", padx=10)
        for i in range(4):
            grid_frame.columnconfigure(i, weight=1)

        # Define 8 core cards configurations
        card_configs = [
            ("TOTAL OUTFLOW", f"{self.currency}{metrics['total_all']:.2f}", "Cumulative all-time spending.", 0, 0),
            ("MONTHLY OUTFLOW", f"{self.currency}{metrics['total_month']:.2f}", "Spends recorded this month.", 0, 1),
            ("REMAINING BUDGET", f"{self.currency}{metrics['remaining_budget']:.2f}", "Current budget surplus.", 0, 2),
            ("PEAK TRANSACTION", f"{self.currency}{metrics['max_expense']:.2f}", "Highest single outlay.", 0, 3),
            ("AVERAGE EXPENSE", f"{self.currency}{metrics['avg_expense']:.2f}", "Mathematical average cost.", 1, 0),
            ("ACTIVE SAVINGS GOALS", f"{metrics['goals_count']} Targets", "Active savings funds profiles.", 1, 1),
            ("RECURRING SCHEDULERS", f"{metrics['recurring_count']} Items", "Active billing schedules.", 1, 2),
            ("HEALTH SCORE DIAL", f"{metrics['health_score']}/100", f"Qualitative: {metrics['health_rating']}", 1, 3)
        ]

        for title, val, desc, r, c in card_configs:
            self.create_kpi_card(grid_frame, title, val, desc, r, c)

        # Business Insights Engine (Feature 3)
        insights_card = ttk.Frame(self.scrollable, style="Card.TFrame", padding=20)
        insights_card.pack(fill="x", padx=10, pady=(20, 0))
        
        ins_title = ttk.Label(insights_card, text="💡 Dynamic Business Intelligence Insights", style="CardTitle.TLabel")
        ins_title.pack(anchor="w", pady=(0, 10))

        insights_list = self.generate_spend_insights(metrics["expenses"], metrics["budget_limit"])
        for ins in insights_list:
            ins_lbl = ttk.Label(insights_card, text=f" • {ins}", style="CardBody.TLabel", wraplength=700)
            ins_lbl.pack(anchor="w", pady=3)

    def create_kpi_card(self, parent, title, val, desc, r, c):
        card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        card.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)

        lbl_title = ttk.Label(card, text=title, style="CardMuted.TLabel")
        lbl_title.pack(anchor="w", pady=(0, 6))

        lbl_val = ttk.Label(card, text=val, font=("Outfit", 20, "bold"), foreground=self.colors["primary"], background=self.colors["bg_card"])
        lbl_val.pack(anchor="w", pady=(0, 6))

        lbl_desc = ttk.Label(card, text=desc, style="CardMuted.TLabel")
        lbl_desc.pack(anchor="w")

    def calculate_summary_metrics(self):
        user_id = SessionManager.get_user_id()
        role = SessionManager.get_role()
        current_month = datetime.now().strftime("%Y-%m")

        metrics = {
            "total_all": 0.0,
            "total_month": 0.0,
            "remaining_budget": 0.0,
            "max_expense": 0.0,
            "avg_expense": 0.0,
            "goals_count": 0,
            "recurring_count": 0,
            "health_score": 100,
            "health_rating": "Excellent",
            "expenses": [],
            "budget_limit": 50000.0
        }

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Fetching user-specific or admin-wide expenses
                if role == "Admin":
                    cursor.execute("SELECT * FROM expenses")
                else:
                    cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
                
                expenses_rows = cursor.fetchall()
                expenses = [dict(row) for row in expenses_rows]
                metrics["expenses"] = expenses

                if expenses:
                    metrics["total_all"] = sum(float(e["amount"]) for e in expenses)
                    metrics["total_month"] = sum(float(e["amount"]) for e in expenses if e["transaction_date"].startswith(current_month))
                    metrics["max_expense"] = max(float(e["amount"]) for e in expenses)
                    metrics["avg_expense"] = metrics["total_all"] / len(expenses)

                # Goals count
                if role == "Admin":
                    cursor.execute("SELECT COUNT(*) FROM goals")
                else:
                    cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ?", (user_id,))
                metrics["goals_count"] = cursor.fetchone()[0]

                # Recurring count
                if role == "Admin":
                    cursor.execute("SELECT COUNT(*) FROM recurring_expenses")
                else:
                    cursor.execute("SELECT COUNT(*) FROM recurring_expenses WHERE user_id = ?", (user_id,))
                metrics["recurring_count"] = cursor.fetchone()[0]

                # Budget limits
                if role == "Admin":
                    cursor.execute("SELECT monthly_limit FROM budgets ORDER BY id DESC LIMIT 1")
                else:
                    cursor.execute("SELECT monthly_limit FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
                b_row = cursor.fetchone()
                limit = float(b_row[0]) if b_row else float(self.controller.app_settings.get("default_monthly_budget", 50000.0))
                metrics["budget_limit"] = limit
                metrics["remaining_budget"] = max(0.0, limit - metrics["total_month"])

            # Feature 1 & 2: Forecast calculations and Financial Health Score
            forecasts = calculate_analytical_forecasts(expenses, limit)
            metrics["health_score"] = forecasts["health_score"]
            metrics["health_rating"] = forecasts["health_rating"]

        except Exception as err:
            print(f"Metrics loading crashed: {str(err)}")
        return metrics

    def generate_spend_insights(self, expenses, budget_limit):
        """
        Feature 3: Dynamic Smart Insight Engine. Generates mathematical
        spending indicators and alerts based on ledger analytics.
        """
        insights = []
        if not expenses:
            return ["No transaction records available. Add expenses to view financial insights."]

        current_month = datetime.now().strftime("%Y-%m")
        prev_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m")

        # Group totals by category
        cat_sums_curr = collections.defaultdict(float)
        cat_sums_prev = collections.defaultdict(float)
        total_curr = 0.0

        for exp in expenses:
            amt = float(exp["amount"])
            date = exp["transaction_date"]
            cat = exp["category"]

            if date.startswith(current_month):
                cat_sums_curr[cat] += amt
                total_curr += amt
            elif date.startswith(prev_month):
                cat_sums_prev[cat] += amt

        # 1. Budget Adherence Insights
        if total_curr > budget_limit:
            insights.append(f"⚠️ Critical: Monthly target budget exceeded by {self.currency}{total_curr - budget_limit:,.2f}!")
        elif total_curr >= budget_limit * 0.8:
            insights.append(f"⚠️ Warning: Monthly spending has utilized {total_curr/budget_limit*100:.1f}% of target limits.")
        else:
            insights.append(f"✓ Compliant: Spending is currently within healthy margins ({total_curr/budget_limit*100:.1f}% utilized).")

        # 2. Category Growth Trends comparisons
        for cat, curr_val in cat_sums_curr.items():
            prev_val = cat_sums_prev.get(cat, 0.0)
            if prev_val > 0:
                diff_pct = ((curr_val - prev_val) / prev_val) * 100
                if diff_pct > 10:
                    insights.append(f"📈 Escalation: {cat} spending increased by {diff_pct:.1f}% compared to last month.")
                elif diff_pct < -10:
                    insights.append(f"📉 Improvement: {cat} spending decreased by {abs(diff_pct):.1f}% compared to last month.")

        # 3. Peak spending alert
        if expenses:
            peak_exp = max(expenses, key=lambda x: float(x["amount"]))
            insights.append(f"➔ Peak Transaction: Highest single outlay recorded this month was '{peak_exp['title']}' ({self.currency}{float(peak_exp['amount']):,.2f}).")

        return insights[:5]


class AddExpensePage(ttk.Frame):
    """
    Feature 6 & 7: Form layer integrating OCR scanners and SpeechRecognitions.
    Allows manual inputs, voice speech matching, and optical image character extractions.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.currency = controller.currency
        self.colors = controller.colors

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Title
        title_lbl = ttk.Label(self, text="Add New Transaction Entry", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Traditional Manual Form Card
        form_card = ttk.Frame(self, style="Card.TFrame", padding=25)
        form_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        self.setup_form_fields(form_card)

        # OCR & Speech Assistants Card
        assistant_card = ttk.Frame(self, style="Card.TFrame", padding=25)
        assistant_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        self.setup_assistants_panel(assistant_card)

    def setup_form_fields(self, container):
        fields = [
            ("Transaction Title", "title"),
            ("Description Details", "description"),
            ("Amount Outflow", "amount"),
            ("Category Channel", "category"),
            ("Payment Method", "payment_method"),
            ("Calendar Date (YYYY-MM-DD)", "transaction_date"),
            ("Attach Invoice/Bill File", "attachment")
        ]

        self.form_entries = {}
        row_idx = 0

        for label_text, var_name in fields:
            lbl = ttk.Label(container, text=label_text, style="CardTitle.TLabel", font=("Outfit", 9, "bold"))
            lbl.grid(row=row_idx, column=0, sticky="w", pady=(4, 2))

            if var_name == "category":
                entry = ttk.Combobox(container, values=["Food & Dining", "Electronics & Gadgets", "Travel & Transport", "Entertainment", "Others"])
                entry.set("Others")
                entry.grid(row=row_idx+1, column=0, sticky="ew", pady=(0, 10))
            elif var_name == "payment_method":
                entry = ttk.Combobox(container, values=["Cash", "Debit Card", "Credit Card", "UPI", "Bank Transfer", "Cheque"])
                entry.set("UPI")
                entry.grid(row=row_idx+1, column=0, sticky="ew", pady=(0, 10))
            elif var_name == "attachment":
                # Attachment browser row with select button
                row_frame = ttk.Frame(container, style="Card.TFrame")
                row_frame.grid(row=row_idx+1, column=0, sticky="ew", pady=(0, 10))
                row_frame.columnconfigure(0, weight=1)
                
                entry = ttk.Entry(row_frame, style="TEntry")
                entry.grid(row=0, column=0, sticky="ew", ipady=2, padx=(0, 10))
                
                browse_btn = ttk.Button(row_frame, text="📁 Browse", style="Secondary.TButton", command=self.browse_attachment)
                browse_btn.grid(row=0, column=1)
            else:
                entry = ttk.Entry(container, style="TEntry")
                entry.grid(row=row_idx+1, column=0, sticky="ew", pady=(0, 10))
                
            if var_name == "transaction_date":
                entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

            container.columnconfigure(0, weight=1)
            self.form_entries[var_name] = entry
            row_idx += 2

        # Save Button
        save_btn = ttk.Button(container, text="✓ COMMIT TRANSACTION", style="Primary.TButton", command=self.submit_expense_form)
        save_btn.grid(row=row_idx, column=0, sticky="ew", pady=(15, 0))

    def setup_assistants_panel(self, container):
        # 1. OCR Receipt Scanner Section (Feature 6)
        ocr_lbl = ttk.Label(container, text="Optical Character Recognition (OCR) Scanner", style="CardTitle.TLabel")
        ocr_lbl.pack(anchor="w", pady=(0, 5))
        
        ocr_desc = ttk.Label(container, text="Select an image file of your bill or receipt, and pytesseract will attempt to extract the merchant name and total amount automatically.", style="CardMuted.TLabel", wraplength=350)
        ocr_desc.pack(anchor="w", pady=(0, 15))

        ocr_btn = ttk.Button(container, text="📷 Upload & Scan Receipt Image", style="Secondary.TButton", command=self.trigger_ocr_scan)
        ocr_btn.pack(fill="x", ipady=4, pady=(0, 30))

        # 2. Voice Input Section (Feature 7)
        voice_lbl = ttk.Label(container, text="Voice Transcription & Parser Assistant", style="CardTitle.TLabel")
        voice_lbl.pack(anchor="w", pady=(0, 5))

        voice_desc = ttk.Label(container, text="Click microphone to describe a spending phrase (e.g. 'Spent 450 rupees on dinner'). The speech tokens will isolate amounts and categories.", style="CardMuted.TLabel", wraplength=350)
        voice_desc.pack(anchor="w", pady=(0, 15))

        self.voice_mic_btn = ttk.Button(container, text="🎙 Start Microphone Listen", style="Secondary.TButton", command=self.trigger_voice_capture)
        self.voice_mic_btn.pack(fill="x", ipady=4)

        self.voice_status_lbl = ttk.Label(container, text="Microphone service idle.", style="CardMuted.TLabel")
        self.voice_status_lbl.pack(anchor="center", pady=(15, 0))

    def browse_attachment(self):
        filepath = filedialog.askopenfilename(
            title="Attach Bill Receipt",
            filetypes=[("PDF Documents", "*.pdf"), ("Images", "*.png;*.jpg;*.jpeg"), ("All Files", "*.*")]
        )
        if filepath:
            self.form_entries["attachment"].delete(0, tk.END)
            self.form_entries["attachment"].insert(0, os.path.normpath(filepath))

    def trigger_ocr_scan(self):
        filepath = filedialog.askopenfilename(
            title="Select Receipt Image for OCR Scan",
            filetypes=[("Receipt Images", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not filepath:
            return

        # Show load progress box
        self.parent.config(cursor="watch")
        
        def run_ocr():
            result = execute_receipt_ocr(filepath)
            
            # Revert cursor
            self.parent.config(cursor="")
            
            if result["success"]:
                # Populate entries
                self.parent.after(0, lambda: self.apply_ocr_results(result, filepath))
            else:
                self.parent.after(0, lambda: messagebox.showerror("OCR Failed", result["error"]))

        threading.Thread(target=run_ocr, daemon=True).start()

    def apply_ocr_results(self, result, filepath):
        # Auto populate fields
        self.form_entries["title"].delete(0, tk.END)
        self.form_entries["title"].insert(0, result["merchant"])

        self.form_entries["description"].delete(0, tk.END)
        self.form_entries["description"].insert(0, "Extracted automatically via pytesseract OCR.")

        self.form_entries["amount"].delete(0, tk.END)
        if result["amount"] > 0:
            self.form_entries["amount"].insert(0, str(result["amount"]))

        self.form_entries["attachment"].delete(0, tk.END)
        self.form_entries["attachment"].insert(0, os.path.normpath(filepath))

        messagebox.showinfo(
            "OCR Process Completed",
            f"Successfully scanned invoice details:\n • Merchant: {result['merchant']}\n • Amount detected: {self.currency}{result['amount']:.2f}\n\nForm fields pre-filled."
        )

    def trigger_voice_capture(self):
        self.voice_mic_btn.configure(state="disabled")
        self.voice_status_lbl.configure(text="Activating microphone drivers...")
        
        def success_handler(success, parsed):
            self.voice_mic_btn.configure(state="normal")
            self.voice_status_lbl.configure(text="Microphone service idle.")

            if success:
                # Pre-fill
                self.form_entries["title"].delete(0, tk.END)
                self.form_entries["title"].insert(0, parsed["title"])

                self.form_entries["description"].delete(0, tk.END)
                self.form_entries["description"].insert(0, f"Speech capture: '{parsed['raw_text']}'")

                self.form_entries["amount"].delete(0, tk.END)
                if parsed["amount"] > 0:
                    self.form_entries["amount"].insert(0, str(parsed["amount"]))

                self.form_entries["category"].set(parsed["category"])

                messagebox.showinfo(
                    "Voice Parser Verified",
                    f"Isolate Speech values:\n • Title: {parsed['title']}\n • Category: {parsed['category']}\n • Amount: {self.currency}{parsed['amount']:.2f}"
                )
            else:
                messagebox.showerror("Speech Error", parsed)

        def progress_handler(status_text):
            self.voice_status_lbl.configure(text=status_text)

        capture_and_parse_voice(success_handler, progress_handler)

    def submit_expense_form(self):
        title = self.form_entries["title"].get().strip()
        description = self.form_entries["description"].get().strip()
        amount_str = self.form_entries["amount"].get().strip()
        category = self.form_entries["category"].get()
        payment_method = self.form_entries["payment_method"].get()
        date_str = self.form_entries["transaction_date"].get().strip()
        attachment = self.form_entries["attachment"].get().strip()

        if not title or not amount_str or not date_str:
            messagebox.showerror("Validation Error", "Transaction Title, Amount, and Date are mandatory.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Amount must be a positive numerical value.")
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Date must follow the YYYY-MM-DD pattern.")
            return

        user_id = SessionManager.get_user_id()

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO expenses (title, description, amount, category, payment_method, transaction_date, created_at, user_id, attachment_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, description, amount, category, payment_method, date_str, timestamp, user_id, attachment)
                )
                conn.commit()

            write_system_log("ADD_EXPENSE", f"Committed new expense: '{title}' for {self.currency}{amount}", user_id)
            messagebox.showinfo("Success", "Transaction record committed successfully.")
            
            # Reset
            self.form_entries["title"].delete(0, tk.END)
            self.form_entries["description"].delete(0, tk.END)
            self.form_entries["amount"].delete(0, tk.END)
            self.form_entries["attachment"].delete(0, tk.END)
            
            self.controller.refresh_top_budget_banner()
        except Exception as db_err:
            messagebox.showerror("Database Error", f"Failed to save record: {str(db_err)}")


class TransactionsPage(ttk.Frame):
    """
    Feature 16 & 18: Ledger viewport grid with advanced multi-parameter filtering
    (Category, Date Range, Amount Range, Payment Instrument, Title/Desc search).
    Also hooks up "View Attachment" commands.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.currency = controller.currency
        self.colors = controller.colors

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # Filters Card Grid
        filter_card = ttk.Frame(self, style="Card.TFrame", padding=15)
        filter_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        for i in range(5):
            filter_card.columnconfigure(i, weight=1)

        # Advanced Search parameters entries (Feature 18)
        # Row 1
        ttk.Label(filter_card, text="Search Words", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        self.search_entry = ttk.Entry(filter_card, style="TEntry")
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=3)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_ledger())

        ttk.Label(filter_card, text="Category Selection", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=0, column=1, sticky="w", padx=5)
        self.cat_combo = ttk.Combobox(filter_card, values=["All", "Food & Dining", "Electronics & Gadgets", "Travel & Transport", "Entertainment", "Others"])
        self.cat_combo.set("All")
        self.cat_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=3)
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_ledger())

        ttk.Label(filter_card, text="Payment Method", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=0, column=2, sticky="w", padx=5)
        self.pay_combo = ttk.Combobox(filter_card, values=["All", "Cash", "Debit Card", "Credit Card", "UPI", "Bank Transfer", "Cheque"])
        self.pay_combo.set("All")
        self.pay_combo.grid(row=1, column=2, sticky="ew", padx=5, pady=3)
        self.pay_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_ledger())

        # Row 2 (Ranges)
        ttk.Label(filter_card, text="Min Amount", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=0, column=3, sticky="w", padx=5)
        self.min_amt = ttk.Entry(filter_card, style="TEntry")
        self.min_amt.grid(row=1, column=3, sticky="ew", padx=5, pady=3)
        self.min_amt.bind("<KeyRelease>", lambda e: self.refresh_ledger())

        ttk.Label(filter_card, text="Max Amount", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=0, column=4, sticky="w", padx=5)
        self.max_amt = ttk.Entry(filter_card, style="TEntry")
        self.max_amt.grid(row=1, column=4, sticky="ew", padx=5, pady=3)
        self.max_amt.bind("<KeyRelease>", lambda e: self.refresh_ledger())

        # Row 3 Date Ranges
        ttk.Label(filter_card, text="Start Date (YYYY-MM-DD)", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=2, column=0, sticky="w", padx=5, pady=(10, 0))
        self.start_date = ttk.Entry(filter_card, style="TEntry")
        self.start_date.grid(row=3, column=0, sticky="ew", padx=5, pady=3)
        self.start_date.bind("<KeyRelease>", lambda e: self.refresh_ledger())

        ttk.Label(filter_card, text="End Date (YYYY-MM-DD)", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=2, column=1, sticky="w", padx=5, pady=(10, 0))
        self.end_date = ttk.Entry(filter_card, style="TEntry")
        self.end_date.grid(row=3, column=1, sticky="ew", padx=5, pady=3)
        self.end_date.bind("<KeyRelease>", lambda e: self.refresh_ledger())

        # Table Grid Treeview
        grid_frame = ttk.Frame(self)
        grid_frame.grid(row=2, column=0, sticky="nsew")
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        columns = ("id", "date", "title", "category", "payment", "amount", "attachment")
        self.tree = ttk.Treeview(grid_frame, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("title", text="Title Description")
        self.tree.heading("category", text="Category")
        self.tree.heading("payment", text="Payment Method")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("attachment", text="Bill Attached")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("title", width=220, anchor="w")
        self.tree.column("category", width=120, anchor="w")
        self.tree.column("payment", width=100, anchor="center")
        self.tree.column("amount", width=90, anchor="e")
        self.tree.column("attachment", width=100, anchor="center")

        scroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # Action panel with View Attachment
        action_bar = ttk.Frame(self)
        action_bar.grid(row=3, column=0, sticky="ew", pady=(15, 0))

        edit_btn = ttk.Button(action_bar, text="✏ Edit Selected", style="Secondary.TButton", command=self.trigger_edit)
        edit_btn.pack(side="left", padx=(0, 10))

        delete_btn = ttk.Button(action_bar, text="🗑 Delete Row", style="Danger.TButton", command=self.trigger_delete)
        delete_btn.pack(side="left", padx=(0, 10))

        view_attach_btn = ttk.Button(action_bar, text="📄 View Attached Bill File", style="Primary.TButton", command=self.trigger_view_attachment)
        view_attach_btn.pack(side="right")

        self.refresh_ledger()

    def refresh_ledger(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        user_id = SessionManager.get_user_id()
        role = SessionManager.get_role()

        # Retrieve filter parameters
        search = self.search_entry.get().strip().lower()
        cat_filter = self.cat_combo.get()
        pay_filter = self.pay_combo.get()
        min_str = self.min_amt.get().strip()
        max_str = self.max_amt.get().strip()
        start_str = self.start_date.get().strip()
        end_str = self.end_date.get().strip()

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Enforce multi-user rows restrictions
                if role == "Admin":
                    cursor.execute("SELECT * FROM expenses ORDER BY transaction_date DESC")
                else:
                    cursor.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY transaction_date DESC", (user_id,))
                
                rows = cursor.fetchall()

            for row in rows:
                r_dict = dict(row)
                amount = float(r_dict["amount"])
                date_str = r_dict["transaction_date"]

                # Apply live parameters search filters (Feature 18)
                if cat_filter != "All" and r_dict["category"] != cat_filter:
                    continue
                if pay_filter != "All" and r_dict["payment_method"] != pay_filter:
                    continue

                if search:
                    match_search = (
                        search in r_dict["title"].lower() or 
                        search in (r_dict["description"] or "").lower() or
                        search in r_dict["category"].lower() or
                        search in r_dict["payment_method"].lower()
                    )
                    if not match_search:
                        continue

                # Amount ranges
                if min_str:
                    try:
                        if amount < float(min_str): continue
                    except ValueError: pass
                if max_str:
                    try:
                        if amount > float(max_str): continue
                    except ValueError: pass

                # Date ranges
                if start_str:
                    try:
                        if date_str < start_str: continue
                    except ValueError: pass
                if end_str:
                    try:
                        if date_str > end_str: continue
                    except ValueError: pass

                # Attachment string details mapping
                has_file = "✓ Yes" if r_dict.get("attachment_path") else "No"

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        r_dict["id"],
                        r_dict["transaction_date"],
                        r_dict["title"],
                        r_dict["category"],
                        r_dict["payment_method"],
                        f"{self.currency}{amount:,.2f}",
                        has_file
                    )
                )
        except Exception as err:
            print(f"Failed to refresh ledger rows: {str(err)}")

    def trigger_view_attachment(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Missing", "Please select a ledger row first.")
            return

        row_id = self.tree.item(selected[0], "values")[0]

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT attachment_path FROM expenses WHERE id = ?", (row_id,))
                row = cursor.fetchone()
                path = row["attachment_path"] if row else None

            if path:
                launch_attachment_file(path)
            else:
                messagebox.showinfo("Attachment Blank", "This expense record does not have any attached bill files.")
        except Exception as err:
            messagebox.showerror("Error", f"Failed to retrieve attachment path: {str(err)}")

    def trigger_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Missing", "Please select a row to delete.")
            return

        confirm = messagebox.askyesno("Delete", "Delete this transaction record?")
        if not confirm:
            return

        item_values = self.tree.item(selected[0], "values")
        row_id = item_values[0]
        title = item_values[2]
        user_id = SessionManager.get_user_id()

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id = ?", (row_id,))
                conn.commit()

            write_system_log("DELETE_EXPENSE", f"Deleted expense row #{row_id}: '{title}'", user_id)
            messagebox.showinfo("Success", "Record deleted.")
            self.refresh_ledger()
            self.controller.refresh_top_budget_banner()
        except Exception as err:
            messagebox.showerror("Database Error", str(err))

    def trigger_edit(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Missing", "Please select a row to edit.")
            return

        row_id = self.tree.item(selected[0], "values")[0]

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM expenses WHERE id = ?", (row_id,))
                exp = dict(cursor.fetchone())
        except Exception as err:
            messagebox.showerror("Error", str(err))
            return

        # Modal
        modal = tk.Toplevel(self)
        modal.title(f"Edit Transaction #{row_id}")
        modal.geometry("380x560")
        modal.configure(bg=self.colors["bg_card"])
        modal.transient(self)
        modal.grab_set()

        # Center Dialog
        modal.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() - modal.winfo_width()) // 2
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")

        fields = [
            ("Transaction Title", "title"),
            ("Description Details", "description"),
            ("Amount Outflow", "amount"),
            ("Category", "category"),
            ("Payment Method", "payment_method"),
            ("Date (YYYY-MM-DD)", "transaction_date"),
            ("Attachment File", "attachment")
        ]

        entries = {}
        for label_text, var_name in fields:
            lbl = tk.Label(modal, text=label_text, font=("Outfit", 9, "bold"), bg=self.colors["bg_card"], fg=self.colors["fg_body"])
            lbl.pack(anchor="w", padx=25, pady=(8, 2))

            if var_name == "category":
                entry = ttk.Combobox(modal, values=["Food & Dining", "Electronics & Gadgets", "Travel & Transport", "Entertainment", "Others"])
                entry.set(exp[var_name])
                entry.pack(fill="x", padx=25)
            elif var_name == "payment_method":
                entry = ttk.Combobox(modal, values=["Cash", "Debit Card", "Credit Card", "UPI", "Bank Transfer", "Cheque"])
                entry.set(exp[var_name])
                entry.pack(fill="x", padx=25)
            elif var_name == "attachment":
                row_frame = ttk.Frame(modal, style="Card.TFrame")
                row_frame.pack(fill="x", padx=25)
                row_frame.columnconfigure(0, weight=1)
                
                entry = ttk.Entry(row_frame, style="TEntry")
                entry.insert(0, exp.get("attachment_path") or "")
                entry.grid(row=0, column=0, sticky="ew", ipady=2, padx=(0, 5))
                
                def modal_browse(ent=entry):
                    filepath = filedialog.askopenfilename(title="Select File", filetypes=[("All Files", "*.*")])
                    if filepath:
                        ent.delete(0, tk.END)
                        ent.insert(0, os.path.normpath(filepath))

                browse_btn = ttk.Button(row_frame, text="📁", style="Secondary.TButton", command=modal_browse)
                browse_btn.grid(row=0, column=1)
            else:
                entry = ttk.Entry(modal, style="TEntry")
                entry.insert(0, str(exp.get(var_name) or ""))
                entry.pack(fill="x", padx=25, ipady=3)
                
            entries[var_name] = entry

        def save_changes():
            t_val = entries["title"].get().strip()
            d_val = entries["description"].get().strip()
            a_val = entries["amount"].get().strip()
            c_val = entries["category"].get()
            p_val = entries["payment_method"].get()
            dt_val = entries["transaction_date"].get().strip()
            at_val = entries["attachment"].get().strip()

            if not t_val or not a_val or not dt_val:
                messagebox.showerror("Error", "Required fields cannot be empty.", parent=modal)
                return

            try:
                amt = float(a_val)
                if amt <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Amount must be a positive number.", parent=modal)
                return

            try:
                datetime.strptime(dt_val, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Date pattern must be YYYY-MM-DD.", parent=modal)
                return

            user_id = SessionManager.get_user_id()

            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE expenses
                        SET title = ?, description = ?, amount = ?, category = ?, payment_method = ?, transaction_date = ?, attachment_path = ?
                        WHERE id = ?
                        """,
                        (t_val, d_val, amt, c_val, p_val, dt_val, at_val, row_id)
                    )
                    conn.commit()

                write_system_log("UPDATE_EXPENSE", f"Edited expense row #{row_id}: '{t_val}'", user_id)
                messagebox.showinfo("Success", "Row edited.", parent=modal)
                modal.destroy()
                self.refresh_ledger()
                self.controller.refresh_top_budget_banner()
            except Exception as err:
                messagebox.showerror("Database Error", str(err), parent=modal)

        save_btn = ttk.Button(modal, text="✓ Save Transaction Changes", style="Primary.TButton", command=save_changes)
        save_btn.pack(fill="x", padx=25, pady=(20, 10), ipady=4)


class CalendarPage(ttk.Frame):
    """
    Feature 9: Interactive Calendar View. Integrates the `tkcalendar.Calendar`
    monthly widget. Highlight spending transaction registers and summarizes daily costs.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.currency = controller.currency
        self.colors = controller.colors

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        title_lbl = ttk.Label(self, text="Interactive Financial Calendar Ledger", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        if not CALENDAR_SUPPORTED:
            warn = ttk.Label(self, text="Calendar widget unavailable. Ensure the 'tkcalendar' package is active in python environment.", font=("Inter", 11))
            warn.grid(row=1, column=0, columnspan=2, pady=40)
            return

        # Left Column: tkcalendar Grid Card
        cal_card = ttk.Frame(self, style="Card.TFrame", padding=15)
        cal_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        # Visual customization for dark theme styles inside calendar
        self.cal = Calendar(
            cal_card, 
            selectmode="day", 
            date_pattern="yyyy-mm-dd",
            background=self.colors["bg_card"],
            foreground=self.colors["fg_body"],
            headersbackground=self.colors["bg_active"],
            headersforeground=self.colors["fg_title"],
            selectbackground=self.colors["primary"],
            selectforeground="#FFFFFF",
            normalbackground=self.colors["bg_card"],
            normalforeground=self.colors["fg_body"],
            weekendbackground=self.colors["bg_card"],
            weekendforeground=self.colors["danger"]
        )
        self.cal.pack(fill="both", expand=True)
        self.cal.bind("<<CalendarSelected>>", lambda e: self.update_daily_preview())

        # Right Column: Daily Summaries Previews Card
        self.preview_card = ttk.Frame(self, style="Card.TFrame", padding=20)
        self.preview_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        self.daily_total_lbl = ttk.Label(self.preview_card, text="Daily Outflow Total: ₹0.00", style="CardTitle.TLabel")
        self.daily_total_lbl.pack(anchor="w", pady=(0, 15))

        # Listbox detailing records
        self.daily_list = tk.Listbox(self.preview_card, bg=self.colors["bg_main"], fg=self.colors["fg_body"], bd=0, highlightthickness=0, font=("Inter", 10))
        self.daily_list.pack(fill="both", expand=True)

        self.update_daily_preview()

    def update_daily_preview(self):
        selected_date = self.cal.get_date()
        self.daily_list.delete(0, tk.END)

        user_id = SessionManager.get_user_id()
        role = SessionManager.get_role()
        total = 0.0

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if role == "Admin":
                    cursor.execute("SELECT title, amount, category FROM expenses WHERE transaction_date = ?", (selected_date,))
                else:
                    cursor.execute("SELECT title, amount, category FROM expenses WHERE user_id = ? AND transaction_date = ?", (user_id, selected_date))
                
                rows = cursor.fetchall()

            for row in rows:
                amt = float(row["amount"])
                total += amt
                self.daily_list.insert(tk.END, f" • [{row['category']}] {row['title']} - {self.currency}{amt:,.2f}")

            self.daily_total_lbl.configure(text=f"Selected Spend Date: {selected_date} | Total Outflow: {self.currency}{total:,.2f}")
            if not rows:
                self.daily_list.insert(tk.END, "No transaction records logged on this date.")
        except Exception as err:
            print(f"Calendar query failure: {str(err)}")


class AnalyticsPage(ttk.Frame):
    """
    Feature 8: Advanced Analytics Center. Embeds 6 visual Matplotlib charts:
    Pie (Category share), Bar (Monthly comparison), Line (Expense Trend),
    Top categories Hbar, Budget utilization progress, and Yearly spends.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.colors = controller.colors

        # Scrolling Canvas coordinates
        canvas = tk.Canvas(self, bg=self.colors["bg_main"], bd=0, highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        
        self.scrollable = ttk.Frame(canvas)
        self.scrollable.columnconfigure(0, weight=1)
        self.scrollable.columnconfigure(1, weight=1)

        self.scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Headings
        title_lbl = ttk.Label(self.scrollable, text="Advanced Analytical Visualizations Suite", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20), padx=10)

        # Pull database rows
        expenses = self.get_all_expenses()
        budget_limit, warning_limit = self.get_limits()

        if not expenses:
            no_data = ttk.Label(self.scrollable, text="Ledger registry is empty. Add transactions to generate analytics.", font=("Inter", 11))
            no_data.grid(row=1, column=0, columnspan=2, pady=40)
            return

        # Render 6 Charts into Canvas Grid Frame (Feature 8)
        # Row 1
        card1 = ttk.Frame(self.scrollable, style="Card.TFrame", padding=10)
        card1.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        w1 = render_category_pie_chart(card1, expenses, self.colors)
        w1.pack(fill="both", expand=True)

        card2 = ttk.Frame(self.scrollable, style="Card.TFrame", padding=10)
        card2.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        w2 = render_monthly_bar_chart(card2, expenses, self.colors)
        w2.pack(fill="both", expand=True)

        # Row 2
        card3 = ttk.Frame(self.scrollable, style="Card.TFrame", padding=10)
        card3.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        w3 = render_expense_line_graph(card3, expenses, self.colors)
        w3.pack(fill="both", expand=True)

        card4 = ttk.Frame(self.scrollable, style="Card.TFrame", padding=10)
        card4.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        w4 = render_top_categories_hbar(card4, expenses, self.colors)
        w4.pack(fill="both", expand=True)

        # Row 3
        card5 = ttk.Frame(self.scrollable, style="Card.TFrame", padding=10)
        card5.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        w5 = render_budget_utilization_chart(card5, expenses, budget_limit, warning_limit, self.colors)
        w5.pack(fill="both", expand=True)

        card6 = ttk.Frame(self.scrollable, style="Card.TFrame", padding=10)
        card6.grid(row=3, column=1, sticky="nsew", padx=10, pady=10)
        w6 = render_yearly_overview_chart(card6, expenses, self.colors)
        w6.pack(fill="both", expand=True)

    def get_all_expenses(self):
        user_id = SessionManager.get_user_id()
        role = SessionManager.get_role()
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if role == "Admin":
                    cursor.execute("SELECT * FROM expenses")
                else:
                    cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_limits(self):
        user_id = SessionManager.get_user_id()
        role = SessionManager.get_role()
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if role == "Admin":
                    cursor.execute("SELECT monthly_limit, warning_limit FROM budgets ORDER BY id DESC LIMIT 1")
                else:
                    cursor.execute("SELECT monthly_limit, warning_limit FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
                row = cursor.fetchone()
                if row:
                    return float(row["monthly_limit"]), float(row["warning_limit"])
        except Exception:
            pass
        return 50000.0, 40000.0


class ReportsPage(ttk.Frame):
    """
    Feature 10 & 19 & 20: Reports center triggering downloads for Excel Sheets,
    professional PDF cover page compilations, and concise Monthly Summary PDFs.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.colors = controller.colors

        title_lbl = ttk.Label(self, text="Executive Financial Reports & Exporter Suite", font=("Outfit", 18, "bold"))
        title_lbl.pack(anchor="w", pady=(0, 20))

        card = ttk.Frame(self, style="Card.TFrame", padding=30)
        card.pack(fill="x", expand=False)

        desc = ttk.Label(card, text="Select document format to compile financial ledgers, prediction parameters, and goals statistics.", style="CardBody.TLabel", font=("Inter", 11))
        desc.pack(anchor="w", pady=(0, 25))

        # Proportional Buttons spacing
        btn_grid = ttk.Frame(card, style="Card.TFrame")
        btn_grid.pack(fill="x")
        for i in range(4):
            btn_grid.columnconfigure(i, weight=1)

        # Action Buttons
        pdf_suite_btn = ttk.Button(btn_grid, text="📄 Compile PDF Report Suite", style="Primary.TButton", command=self.export_pdf_suite)
        pdf_suite_btn.grid(row=0, column=0, padx=8, ipady=10, sticky="ew")

        pdf_sum_btn = ttk.Button(btn_grid, text="📊 Export Monthly Summary PDF", style="Primary.TButton", command=self.export_monthly_summary)
        pdf_sum_btn.grid(row=0, column=1, padx=8, ipady=10, sticky="ew")

        excel_btn = ttk.Button(btn_grid, text="📈 Export Excel Sheet", style="Secondary.TButton", command=self.export_excel)
        excel_btn.grid(row=0, column=2, padx=8, ipady=10, sticky="ew")

        csv_btn = ttk.Button(btn_grid, text="🗂 Export CSV Database", style="Secondary.TButton", command=self.export_csv)
        csv_btn.grid(row=0, column=3, padx=8, ipady=10, sticky="ew")

        self.status_lbl = ttk.Label(card, text="", style="CardMuted.TLabel")
        self.status_lbl.pack(anchor="center", pady=(25, 0))

    def fetch_analytical_dependencies(self):
        user_id = SessionManager.get_user_id()
        role = SessionManager.get_role()
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if role == "Admin":
                    cursor.execute("SELECT * FROM expenses")
                    expenses = [dict(row) for row in cursor.fetchall()]
                    
                    cursor.execute("SELECT * FROM budgets ORDER BY id DESC LIMIT 1")
                    b_row = cursor.fetchone()
                    
                    cursor.execute("SELECT * FROM goals")
                    goals = [dict(row) for row in cursor.fetchall()]
                else:
                    cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
                    expenses = [dict(row) for row in cursor.fetchall()]
                    
                    cursor.execute("SELECT * FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
                    b_row = cursor.fetchone()

                    cursor.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
                    goals = [dict(row) for row in cursor.fetchall()]

                limit = float(b_row["monthly_limit"]) if b_row else float(self.controller.app_settings.get("default_monthly_budget", 50000.0))
                warn = float(b_row["warning_limit"]) if b_row else float(self.controller.app_settings.get("default_warning_limit", 40000.0))

            forecasts = calculate_analytical_forecasts(expenses, limit)
            return expenses, limit, warn, forecasts, goals
        except Exception as err:
            print("Failed to compile database report variables: %s", str(err))
            return [], 50000.0, 40000.0, {}, []

    def export_pdf_suite(self):
        expenses, limit, warn, forecasts, goals = self.fetch_analytical_dependencies()
        if not expenses:
            messagebox.showwarning("Ledger Empty", "Ledger registry has no entries to compile reports.")
            return

        export_dir = self.controller.app_settings.get("export_folder", os.path.join(os.path.dirname(__file__), "exports"))
        filepath = os.path.join(export_dir, "reports", "financial_report_suite.pdf")

        success = compile_pdf_report(filepath, expenses, limit, warn, forecasts, goals, self.controller.currency)
        if success:
            write_system_log("REPORT", f"Compiled Multi-Page PDF Suite: {filepath}", SessionManager.get_user_id())
            messagebox.showinfo("Export Successful", f"PDF Report Suite compiled and stored at:\n{filepath}")
            self.status_lbl.configure(text=f"✓ Last Compiled: {datetime.now().strftime('%H:%M:%S')} (PDF Suite)")
        else:
            messagebox.showerror("Export Failed", "ReportLab failed to write PDF. Ensure target file is closed in other viewers.")

    def export_monthly_summary(self):
        expenses, limit, _, forecasts, _ = self.fetch_analytical_dependencies()
        if not expenses:
            messagebox.showwarning("Ledger Empty", "No entries logged.")
            return

        export_dir = self.controller.app_settings.get("export_folder", os.path.join(os.path.dirname(__file__), "exports"))
        filepath = os.path.join(export_dir, "reports", "monthly_financial_summary.pdf")

        success = compile_monthly_summary_pdf(filepath, expenses, limit, forecasts, self.controller.currency)
        if success:
            write_system_log("REPORT", f"Generated Monthly PDF Summary: {filepath}", SessionManager.get_user_id())
            messagebox.showinfo("Summary Saved", f"Monthly Financial Summary PDF saved at:\n{filepath}")
            self.status_lbl.configure(text=f"✓ Last Compiled: {datetime.now().strftime('%H:%M:%S')} (Monthly Summary)")
        else:
            messagebox.showerror("Export Failed", "Failed to compile summary PDF.")

    def export_excel(self):
        expenses, limit, _, _, goals = self.fetch_analytical_dependencies()
        if not expenses:
            messagebox.showwarning("Ledger Empty", "No entries logged.")
            return

        export_dir = self.controller.app_settings.get("export_folder", os.path.join(os.path.dirname(__file__), "exports"))
        filepath = os.path.join(export_dir, "excel", "financial_registry.xlsx")

        success = compile_excel_report(filepath, expenses, limit, goals, self.controller.currency)
        if success:
            write_system_log("REPORT", f"Compiled Excel Worksheet: {filepath}", SessionManager.get_user_id())
            messagebox.showinfo("Spreadsheet Saved", f"Excel Workbook saved successfully at:\n{filepath}")
            self.status_lbl.configure(text=f"✓ Last Compiled: {datetime.now().strftime('%H:%M:%S')} (Excel)")
        else:
            messagebox.showerror("Export Failed", "Excel workbook writing failed.")

    def export_csv(self):
        expenses, _, _, _, _ = self.fetch_analytical_dependencies()
        if not expenses:
            messagebox.showwarning("Ledger Empty", "No entries logged.")
            return

        export_dir = self.controller.app_settings.get("export_folder", os.path.join(os.path.dirname(__file__), "exports"))
        filepath = os.path.join(export_dir, "csv", "transaction_ledger_export.csv")

        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
                fieldnames = ["id", "title", "description", "amount", "category", "payment_method", "transaction_date", "created_at", "user_id", "attachment_path"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for exp in expenses:
                    row = {key: exp.get(key, "") for key in fieldnames}
                    writer.writerow(row)

            write_system_log("REPORT", f"Generated CSV Ledger database: {filepath}", SessionManager.get_user_id())
            messagebox.showinfo("CSV Database Exported", f"CSV file successfully saved at:\n{filepath}")
            self.status_lbl.configure(text=f"✓ Last Compiled: {datetime.now().strftime('%H:%M:%S')} (CSV)")
        except Exception as err:
            messagebox.showerror("Export Failed", f"CSV compiling failed: {str(err)}")


class VoiceEntryPage(ttk.Frame):
    """
    Hands-free voice transcription trigger frame.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.currency = controller.currency
        self.colors = controller.colors

        card = ttk.Frame(self, style="Card.TFrame", padding=35)
        card.pack(fill="both", expand=True)

        lbl = ttk.Label(card, text="Asynchronous Voice Transcription Centre", font=("Outfit", 16, "bold"), background=self.colors["bg_card"])
        lbl.pack(anchor="center", pady=(20, 10))

        desc = ttk.Label(card, text="Describe your spending clearly (e.g. 'Spent 600 rupees on movie ticket'). The parsing engines will map forms automatically.", style="CardMuted.TLabel", wraplength=450, justify="center")
        desc.pack(anchor="center", pady=(0, 40))

        self.mic_btn = tk.Button(
            card,
            text="🎙",
            font=("Outfit", 48),
            bg=self.colors["primary"],
            fg="#FFFFFF",
            relief="flat",
            bd=0,
            padx=25,
            pady=15,
            command=self.trigger_voice_capture,
            cursor="hand2"
        )
        self.mic_btn.pack(anchor="center", pady=(0, 25))

        self.status_lbl = ttk.Label(card, text="Microphone service idle.", style="CardMuted.TLabel", font=("Inter", 10, "bold"))
        self.status_lbl.pack(anchor="center", pady=(0, 30))

        self.result_box = ttk.Frame(card, style="Card.TFrame")
        self.result_box.pack(fill="x", padx=40)
        self.result_lbl = ttk.Label(self.result_box, text="", style="CardBody.TLabel", font=("Inter", 11, "italic"), justify="center", wraplength=500)
        self.result_lbl.pack(anchor="center")

    def trigger_voice_capture(self):
        self.mic_btn.configure(state="disabled", bg=self.colors["bg_active"])
        self.status_lbl.configure(text="Activating microphone drivers...")
        
        def success_handler(success, parsed):
            self.mic_btn.configure(state="normal", bg=self.colors["primary"])
            self.status_lbl.configure(text="Microphone service idle.")

            if success:
                self.result_lbl.configure(text=f'Matched phrase: "{parsed["raw_text"]}"')
                
                confirm = messagebox.askyesno(
                    "Commit Voice Entry",
                    f"Isolate details:\n • Title: {parsed['title']}\n • Category: {parsed['category']}\n • Amount: {self.currency}{parsed['amount']:.2f}\n\nCommit to database ledger?"
                )
                
                if confirm:
                    try:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO expenses (title, description, amount, category, payment_method, transaction_date, created_at, user_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (parsed["title"], f"Speech capture: '{parsed['raw_text']}'", parsed["amount"], parsed["category"], "UPI", datetime.now().strftime("%Y-%m-%d"), timestamp, SessionManager.get_user_id())
                            )
                            conn.commit()
                        
                        write_system_log("ADD_EXPENSE", f"Committed voice transaction: '{parsed['title']}' for {self.currency}{parsed['amount']}", SessionManager.get_user_id())
                        messagebox.showinfo("Success", "Transaction record committed successfully.")
                        self.controller.refresh_top_budget_banner()
                    except Exception as err:
                        messagebox.showerror("Error", f"Database write crashed: {str(err)}")
            else:
                messagebox.showerror("Speech Error", parsed)

        def progress_handler(status_text):
            self.status_lbl.configure(text=status_text)

        capture_and_parse_voice(success_handler, progress_handler)


class GoalPage(ttk.Frame):
    """
    Feature 4: Goal Tracking Module. Displays, adds, edits, and deletes
    savings goals, tracking target amounts and showing visual progress bars.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.currency = controller.currency
        self.colors = controller.colors

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        title_lbl = ttk.Label(self, text="Savings Target Goals Coordinator", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Left Column: Add/Edit Goal form Card
        form_card = ttk.Frame(self, style="Card.TFrame", padding=20)
        form_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(form_card, text="Goal Name / Fund Title", style="CardTitle.TLabel", font=("Inter", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.goal_title = ttk.Entry(form_card, style="TEntry")
        self.goal_title.pack(fill="x", pady=(0, 15), ipady=3)

        ttk.Label(form_card, text="Absolute Target Amount Required", style="CardTitle.TLabel", font=("Inter", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.goal_target = ttk.Entry(form_card, style="TEntry")
        self.goal_target.pack(fill="x", pady=(0, 15), ipady=3)

        ttk.Label(form_card, text="Current Amount Saved Balance", style="CardTitle.TLabel", font=("Inter", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.goal_saved = ttk.Entry(form_card, style="TEntry")
        self.goal_saved.pack(fill="x", pady=(0, 25), ipady=3)

        add_btn = ttk.Button(form_card, text="✓ Create Savings Target", style="Primary.TButton", command=self.submit_goal)
        add_btn.pack(fill="x", ipady=4)

        # Right Column: Goals Grid List with Progress Bars
        self.list_card = ttk.Frame(self, style="Card.TFrame", padding=20)
        self.list_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        self.goals_container = ttk.Frame(self.list_card, style="Card.TFrame")
        self.goals_container.pack(fill="both", expand=True)

        self.refresh_goals_panel()

    def refresh_goals_panel(self):
        # Clear child containers
        for widget in self.goals_container.winfo_children():
            widget.destroy()

        user_id = SessionManager.get_user_id()
        role = SessionManager.get_role()

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if role == "Admin":
                    cursor.execute("SELECT * FROM goals")
                else:
                    cursor.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
                rows = cursor.fetchall()

            if not rows:
                lbl = ttk.Label(self.goals_container, text="No active savings goals targets. Set one today!", style="CardBody.TLabel")
                lbl.pack(anchor="center", pady=30)
                return

            for g in rows:
                g_dict = dict(g)
                saved = float(g_dict["saved"])
                target = float(g_dict["target"])
                pct = (saved / target * 100) if target > 0 else 0.0
                pct = min(100.0, pct)

                goal_row = ttk.Frame(self.goals_container, style="Card.TFrame", padding=10)
                goal_row.pack(fill="x", pady=6)

                info_frame = ttk.Frame(goal_row, style="Card.TFrame")
                info_frame.pack(fill="x")

                ttk.Label(info_frame, text=g_dict["title"], font=("Outfit", 10, "bold"), background=self.colors["bg_card"]).pack(side="left")
                ttk.Label(info_frame, text=f"{self.currency}{saved:,.2f} of {self.currency}{target:,.2f} ({pct:.1f}%)", style="CardMuted.TLabel").pack(side="right")

                # Visual dynamic Ttk Progressbar (Feature 4)
                bar = ttk.Progressbar(goal_row, orient="horizontal", mode="determinate")
                bar.pack(fill="x", pady=(5, 5))
                bar["value"] = pct

                btn_frame = ttk.Frame(goal_row, style="Card.TFrame")
                btn_frame.pack(fill="x")
                
                # Delete option
                del_btn = ttk.Button(btn_frame, text="Delete Target", style="Secondary.TButton", command=lambda gid=g_dict["id"]: self.delete_goal(gid))
                del_btn.pack(side="right")

        except Exception as err:
            print(f"Goal reloading crashed: {str(err)}")

    def submit_goal(self):
        title = self.goal_title.get().strip()
        target_str = self.goal_target.get().strip()
        saved_str = self.goal_saved.get().strip()

        if not title or not target_str:
            messagebox.showerror("Error", "Goal Title and Target are required.")
            return

        try:
            target = float(target_str)
            saved = float(saved_str) if saved_str else 0.0
            if target <= 0 or saved < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Numerical parameters must be positive bounds.")
            return

        user_id = SessionManager.get_user_id()

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO goals (title, target, saved, created_at, user_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (title, target, saved, timestamp, user_id)
                )
                conn.commit()

            write_system_log("ADD_GOAL", f"Set Savings Goal: '{title}' targeting {self.currency}{target}", user_id)
            messagebox.showinfo("Success", "Goal fund created.")
            
            self.goal_title.delete(0, tk.END)
            self.goal_target.delete(0, tk.END)
            self.goal_saved.delete(0, tk.END)
            self.refresh_goals_panel()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def delete_goal(self, goal_id):
        confirm = messagebox.askyesno("Delete", "Delete this savings goal?")
        if not confirm: return
        user_id = SessionManager.get_user_id()

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
                conn.commit()

            write_system_log("DELETE_GOAL", f"Deleted Savings Goal row #{goal_id}", user_id)
            self.refresh_goals_panel()
        except Exception as err:
            messagebox.showerror("Error", str(err))


class RecurringPage(ttk.Frame):
    """
    Feature 5: Recurring Expense Manager. Add, list, and monitor due dates
    for Daily, Weekly, and Monthly items (Rent, utilities, subscriptions).
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.currency = controller.currency
        self.colors = controller.colors

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        title_lbl = ttk.Label(self, text="Recurring Expenditures Scheduler Center", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Left Column form Card
        form_card = ttk.Frame(self, style="Card.TFrame", padding=20)
        form_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(form_card, text="Billing Subscription Title", style="CardTitle.TLabel", font=("Inter", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.rec_title = ttk.Entry(form_card, style="TEntry")
        self.rec_title.pack(fill="x", pady=(0, 15), ipady=3)

        ttk.Label(form_card, text="Standard Outflow Amount", style="CardTitle.TLabel", font=("Inter", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.rec_amount = ttk.Entry(form_card, style="TEntry")
        self.rec_amount.pack(fill="x", pady=(0, 15), ipady=3)

        ttk.Label(form_card, text="Schedule Frequency Period", style="CardTitle.TLabel", font=("Inter", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.rec_freq = ttk.Combobox(form_card, values=["Daily", "Weekly", "Monthly"])
        self.rec_freq.set("Monthly")
        self.rec_freq.pack(fill="x", pady=(0, 15))

        ttk.Label(form_card, text="Next Billing Date Due (YYYY-MM-DD)", style="CardTitle.TLabel", font=("Inter", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.rec_date = ttk.Entry(form_card, style="TEntry")
        self.rec_date.insert(0, (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))
        self.rec_date.pack(fill="x", pady=(0, 25), ipady=3)

        save_btn = ttk.Button(form_card, text="✓ Schedule Recurring Item", style="Primary.TButton", command=self.submit_recurring)
        save_btn.pack(fill="x", ipady=4)

        # Right Column List View Card
        self.list_card = ttk.Frame(self, style="Card.TFrame", padding=20)
        self.list_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        self.list_container = ttk.Frame(self.list_card, style="Card.TFrame")
        self.list_container.pack(fill="both", expand=True)

        self.refresh_recurring_list()

    def refresh_recurring_list(self):
        for widget in self.list_container.winfo_children():
            widget.destroy()

        user_id = SessionManager.get_user_id()
        role = SessionManager.get_role()

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if role == "Admin":
                    cursor.execute("SELECT * FROM recurring_expenses")
                else:
                    cursor.execute("SELECT * FROM recurring_expenses WHERE user_id = ?", (user_id,))
                rows = cursor.fetchall()

            if not rows:
                lbl = ttk.Label(self.list_container, text="No scheduled recurring dues logged.", style="CardBody.TLabel")
                lbl.pack(anchor="center", pady=30)
                return

            for r in rows:
                r_dict = dict(r)
                amount = float(r_dict["amount"])
                due_str = r_dict["next_due_date"]
                due_date = datetime.strptime(due_str, "%Y-%m-%d")

                # Compute remaining days
                days_rem = (due_date - datetime.now()).days
                due_text = f"Due in {days_rem} days" if days_rem > 0 else "🚨 Overdue!"

                row_row = ttk.Frame(self.list_container, style="Card.TFrame", padding=10)
                row_row.pack(fill="x", pady=5)

                info = ttk.Frame(row_row, style="Card.TFrame")
                info.pack(fill="x")

                ttk.Label(info, text=r_dict["title"], font=("Outfit", 10, "bold"), background=self.colors["bg_card"]).pack(side="left")
                ttk.Label(info, text=f"{self.currency}{amount:,.2f} ({r_dict['frequency']})", style="CardBody.TLabel").pack(side="right")

                date_info = ttk.Frame(row_row, style="Card.TFrame")
                date_info.pack(fill="x", pady=(3, 0))
                ttk.Label(date_info, text=f"Due Date: {due_str} | {due_text}", style="CardMuted.TLabel").pack(side="left")

                del_btn = ttk.Button(date_info, text="Cancel Item", style="Secondary.TButton", command=lambda rid=r_dict["id"]: self.delete_recurring(rid))
                del_btn.pack(side="right")

        except Exception as err:
            print(f"Recurring scheduler reloading failure: {str(err)}")

    def submit_recurring(self):
        title = self.rec_title.get().strip()
        amt_str = self.rec_amount.get().strip()
        freq = self.rec_freq.get()
        date_str = self.rec_date.get().strip()

        if not title or not amt_str or not date_str:
            messagebox.showerror("Error", "Title, Amount, and Due Date are required.")
            return

        try:
            amount = float(amt_str)
            if amount <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number.")
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date pattern must be YYYY-MM-DD.")
            return

        user_id = SessionManager.get_user_id()

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO recurring_expenses (title, amount, category, frequency, next_due_date, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (title, amount, "Others", freq, date_str, user_id)
                )
                conn.commit()

            write_system_log("ADD_RECURRING", f"Scheduled Recurring Due: '{title}' for {self.currency}{amount}", user_id)
            messagebox.showinfo("Success", "Recurring bill scheduled.")
            
            self.rec_title.delete(0, tk.END)
            self.rec_amount.delete(0, tk.END)
            self.refresh_recurring_list()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def delete_recurring(self, row_id):
        confirm = messagebox.askyesno("Delete", "Cancel this recurring item?")
        if not confirm: return
        user_id = SessionManager.get_user_id()

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recurring_expenses WHERE id = ?", (row_id,))
                conn.commit()

            write_system_log("DELETE_RECURRING", f"Deleted Recurring Scheduler row #{row_id}", user_id)
            self.refresh_recurring_list()
        except Exception as err:
            messagebox.showerror("Error", str(err))


class UserManagerPage(ttk.Frame):
    """
    Feature 14: Multi-User Administrator Console. Displays a grid
    listing all registered system user handles, roles, and creation dates.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.colors = controller.colors

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        title_lbl = ttk.Label(self, text="Multi-User Administrative Console", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Add user creation helper card
        add_card = ttk.Frame(self, style="Card.TFrame", padding=15)
        add_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        add_card.columnconfigure(0, weight=1)
        add_card.columnconfigure(1, weight=1)
        add_card.columnconfigure(2, weight=1)

        ttk.Label(add_card, text="Create Employee Account Username", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        self.new_username = ttk.Entry(add_card, style="TEntry")
        self.new_username.grid(row=1, column=0, sticky="ew", padx=5, pady=3)

        ttk.Label(add_card, text="Create Employee Security Password", style="CardTitle.TLabel", font=("Inter", 8, "bold")).grid(row=0, column=1, sticky="w", padx=5)
        self.new_password = ttk.Entry(add_card, style="TEntry", show="•")
        self.new_password.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        add_user_btn = ttk.Button(add_card, text="✓ Register Employee Account", style="Primary.TButton", command=self.register_new_employee)
        add_user_btn.grid(row=1, column=2, padx=5, pady=3)

        # Users grid
        grid_frame = ttk.Frame(self)
        grid_frame.grid(row=2, column=0, sticky="nsew")
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(grid_frame, columns=("id", "username", "role", "date"), show="headings")
        self.tree.heading("id", text="User ID")
        self.tree.heading("username", text="System Username")
        self.tree.heading("role", text="System Role Authority")
        self.tree.heading("date", text="Created At Date")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("username", width=250, anchor="w")
        self.tree.column("role", width=180, anchor="center")
        self.tree.column("date", width=200, anchor="center")

        scroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self.refresh_users_grid()

    def refresh_users_grid(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY id ASC")
                rows = cursor.fetchall()
            for r in rows:
                self.tree.insert("", "end", values=(r["id"], r["username"], r["role"], r["created_at"]))
        except Exception as err:
            print(f"Failed to load users: {str(err)}")

    def register_new_employee(self):
        username = self.new_username.get().strip()
        password = self.new_password.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Fields cannot be empty.")
            return

        import hashlib
        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, pwd_hash, "Employee", timestamp)
                )
                conn.commit()

            write_system_log("USER_CREATE", f"Registered Employee User Account: '{username}'", SessionManager.get_user_id())
            messagebox.showinfo("Success", "Employee registered.")
            
            self.new_username.delete(0, tk.END)
            self.new_password.delete(0, tk.END)
            self.refresh_users_grid()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists in system records.")
        except Exception as err:
            messagebox.showerror("Error", str(err))


class AuditLogsPage(ttk.Frame):
    """
    Feature 12: User Activity Audit Log viewer grid display. Displays logged
    events (Login, logout, creations, deletions, edits) from database.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.colors = controller.colors

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        title_lbl = ttk.Label(self, text="System Audit Activity Logs Viewer", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, sticky="w", pady=(0, 20))

        grid_frame = ttk.Frame(self)
        grid_frame.grid(row=1, column=0, sticky="nsew")
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(grid_frame, columns=("id", "time", "user", "type", "details"), show="headings")
        self.tree.heading("id", text="Log ID")
        self.tree.heading("time", text="Timestamp")
        self.tree.heading("user", text="User ID")
        self.tree.heading("type", text="Event Type")
        self.tree.heading("details", text="Event Details Description")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("time", width=140, anchor="center")
        self.tree.column("user", width=70, anchor="center")
        self.tree.column("type", width=120, anchor="center")
        self.tree.column("details", width=400, anchor="w")

        scroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self.refresh_audit_logs()

    def refresh_audit_logs(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, timestamp, user_id, event_type, details FROM audit_logs ORDER BY id DESC LIMIT 100")
                rows = cursor.fetchall()
            for r in rows:
                self.tree.insert("", "end", values=(r["id"], r["timestamp"], r["user_id"], r["event_type"], r["details"]))
        except Exception as err:
            print(f"Failed to load audits: {str(err)}")


class BackupPage(ttk.Frame):
    """
    Renders dated snapshots list and handles database restoration checks.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.colors = controller.colors

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        title_lbl = ttk.Label(self, text="System Backup & Recovery Coordinator", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Control card
        control_card = ttk.Frame(self, style="Card.TFrame", padding=20)
        control_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        desc = ttk.Label(control_card, text="Generate timestamped copies of your database, or recover previous registers.", style="CardBody.TLabel")
        desc.pack(side="left", padx=(0, 20))

        backup_btn = ttk.Button(control_card, text="⚙ Compile Backup Snapshot", style="Primary.TButton", command=self.trigger_backup)
        backup_btn.pack(side="right")

        # Table backups
        grid_frame = ttk.Frame(self)
        grid_frame.grid(row=2, column=0, sticky="nsew")
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(grid_frame, columns=("filename",), show="headings")
        self.tree.heading("filename", text="Available Historical Database Snapshots")
        self.tree.column("filename", width=400, anchor="w")

        scroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # Actions
        action_bar = ttk.Frame(self)
        action_bar.grid(row=3, column=0, sticky="ew", pady=(15, 0))

        restore_btn = ttk.Button(action_bar, text="✓ Restore Selected Snapshot", style="Secondary.TButton", command=self.trigger_restore)
        restore_btn.pack(side="left")

        self.refresh_backups()

    def refresh_backups(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        backups = list_available_backups()
        for filename in backups:
            self.tree.insert("", "end", values=(filename,))

    def trigger_backup(self):
        success, msg = execute_database_backup()
        if success:
            messagebox.showinfo("Backup Success", f"Database snapshot saved:\n{msg}")
            self.refresh_backups()
        else:
            messagebox.showerror("Backup Failure", msg)

    def trigger_restore(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Missing", "Please select a backup file.")
            return

        backup_filename = self.tree.item(selected[0], "values")[0]
        confirm = messagebox.askyesno("Restore", f"Restoring from '{backup_filename}' will overwrite current ledger records.\n\nProceed?")
        if not confirm:
            return

        success, msg = execute_database_restore(backup_filename)
        if success:
            messagebox.showinfo("Success", msg)
            self.controller.refresh_top_budget_banner()
        else:
            messagebox.showerror("Restore Failed", msg)


class SettingsPage(ttk.Frame):
    """
    App-wide configurations panel for themes and paths.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.colors = parent.winfo_toplevel().cget("bg")

        self.columnconfigure(0, weight=1)

        title_lbl = ttk.Label(self, text="Application System Settings", font=("Outfit", 18, "bold"))
        title_lbl.grid(row=0, column=0, sticky="w", pady=(0, 20))

        card = ttk.Frame(self, style="Card.TFrame", padding=25)
        card.grid(row=1, column=0, sticky="nsew")

        # 1. Visual Theme setting
        ttk.Label(card, text="Application Theme Mode", style="CardTitle.TLabel", font=("Outfit", 9, "bold")).pack(anchor="w", pady=(0, 5))
        self.theme_combo = ttk.Combobox(card, values=["Light", "Dark"])
        self.theme_combo.set(controller.app_settings.get("theme", "Dark"))
        self.theme_combo.pack(fill="x", pady=(0, 15), ipady=5)

        # 2. Currency symbol setting
        ttk.Label(card, text="Standard Currency Symbol", style="CardTitle.TLabel", font=("Outfit", 9, "bold")).pack(anchor="w", pady=(0, 5))
        self.currency_combo = ttk.Combobox(card, values=["₹", "$", "€", "£", "¥"])
        self.currency_combo.set(controller.app_settings.get("currency", "₹"))
        self.currency_combo.pack(fill="x", pady=(0, 15), ipady=5)

        # 3. Export folders pathway
        ttk.Label(card, text="Reports Export Target Directory", style="CardTitle.TLabel", font=("Outfit", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        path_row = ttk.Frame(card, style="Card.TFrame")
        path_row.pack(fill="x", pady=(0, 25))
        path_row.columnconfigure(0, weight=1)

        self.path_entry = ttk.Entry(path_row, style="TEntry")
        self.path_entry.insert(0, controller.app_settings.get("export_folder", ""))
        self.path_entry.grid(row=0, column=0, sticky="ew", ipady=5, padx=(0, 10))

        browse_btn = ttk.Button(path_row, text="📁 Browse", style="Secondary.TButton", command=self.browse_export_folder)
        browse_btn.grid(row=0, column=1)

        # Save settings
        save_btn = ttk.Button(card, text="✓ Save Settings", style="Primary.TButton", command=self.save_configurations)
        save_btn.pack(fill="x", ipady=5)

    def browse_export_folder(self):
        folder = filedialog.askdirectory(initialdir=self.path_entry.get())
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, os.path.normpath(folder))

    def save_configurations(self):
        theme_val = self.theme_combo.get()
        currency_val = self.currency_combo.get()
        path_val = self.path_entry.get().strip()

        if not path_val or not os.path.exists(path_val):
            messagebox.showerror("Validation Error", "Export folder must point to a valid, existing directory.")
            return

        new_settings = {
            "theme": theme_val,
            "currency": currency_val,
            "export_folder": path_val,
            "default_monthly_budget": self.controller.app_settings.get("default_monthly_budget", 50000.0),
            "default_warning_limit": self.controller.app_settings.get("default_warning_limit", 40000.0)
        }

        success = save_user_settings(new_settings)
        if success:
            user_id = SessionManager.get_user_id()
            write_system_log("SETTINGS_CHANGE", f"Settings modified. Theme: {theme_val}, Currency: {currency_val}", user_id)
            
            self.controller.app_settings = new_settings
            self.controller.currency = currency_val
            
            # Reapply style reloads instantly
            apply_theme_styles(self.controller.parent)
            
            confirm = messagebox.askyesno("Aesthetics Saved", "Configurations saved successfully.\n\nWould you like to instantly refresh UI elements?")
            if confirm:
                self.controller.switch_to_page("Settings")
        else:
            messagebox.showerror("Failure", "Failed to save settings.")
