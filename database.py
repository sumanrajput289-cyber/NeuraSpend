# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Enhanced Relational Database Persister
"""

import os
import sqlite3
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "expenses.db")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "system.log")


def initialize_directories():
    """
    Ensures that all required system directories exist in the local workspace.
    """
    folders = [
        DB_DIR,
        LOG_DIR,
        os.path.join(BASE_DIR, "assets"),
        os.path.join(BASE_DIR, "assets", "icons"),
        os.path.join(BASE_DIR, "exports"),
        os.path.join(BASE_DIR, "exports", "reports"),
        os.path.join(BASE_DIR, "exports", "csv"),
        os.path.join(BASE_DIR, "exports", "excel"),
        os.path.join(BASE_DIR, "backups")
    ]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)


# Initialize workspace structure immediately
initialize_directories()


def get_db_connection():
    """
    Establishes and returns a connection to the local SQLite database.
    Enables Row row factory.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def write_system_log(event_type, details, user_id=1):
    """
    Appends audit log records to the external system log file and
    inserts an equivalent record in the database audit_logs table.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [User #{user_id}] [{event_type}] {details}\n"
    
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(log_line)
    except Exception as log_error:
        print(f"Log writing failure: {str(log_error)}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (event_type, details, timestamp, user_id)
                VALUES (?, ?, ?, ?)
                """,
                (event_type, details, timestamp, user_id)
            )
            conn.commit()
    except Exception as db_log_error:
        print(f"Database logging failure: {str(db_log_error)}")


def initialize_database():
    """
    Generates all required database tables and inserts default users.
    Handles migrations using ALTER TABLE if tables already exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Users relation table (Roles: Admin, Employee)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # 2. Expenses relation table with user tracking and attachments
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                user_id INTEGER DEFAULT 1,
                attachment_path TEXT
            )
            """
        )

        # 3. Budgets relation table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monthly_limit REAL NOT NULL,
                warning_limit REAL NOT NULL,
                created_at TEXT NOT NULL,
                user_id INTEGER DEFAULT 1
            )
            """
        )

        # 4. Audit logs security ledger table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_id INTEGER DEFAULT 1
            )
            """
        )

        # 5. Recurring expenses automation table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                frequency TEXT NOT NULL,
                next_due_date TEXT NOT NULL,
                user_id INTEGER DEFAULT 1
            )
            """
        )

        # 6. Savings Goals table [NEW]
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                target REAL NOT NULL,
                saved REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                user_id INTEGER DEFAULT 1
            )
            """
        )

        # 7. Savings Rewards history ledger table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                month TEXT NOT NULL,
                savings REAL NOT NULL,
                reward_amount REAL NOT NULL,
                credited_at TEXT NOT NULL
            )
            """
        )

        # MIGRATION CHECKS (Safe column additions)
        # Adding user_id and attachment_path to expenses if missing
        try:
            cursor.execute("SELECT user_id FROM expenses LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER DEFAULT 1")
            cursor.execute("ALTER TABLE expenses ADD COLUMN attachment_path TEXT")

        try:
            cursor.execute("SELECT user_id FROM budgets LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE budgets ADD COLUMN user_id INTEGER DEFAULT 1")

        try:
            cursor.execute("SELECT user_id FROM audit_logs LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE audit_logs ADD COLUMN user_id INTEGER DEFAULT 1")

        try:
            cursor.execute("SELECT user_id FROM recurring_expenses LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE recurring_expenses ADD COLUMN user_id INTEGER DEFAULT 1")

        # Dynamic user migrations
        for col, col_type in [
            ("email", "TEXT"),
            ("full_name", "TEXT"),
            ("mobile", "TEXT"),
            ("security_question", "TEXT"),
            ("security_answer", "TEXT"),
            ("profile_photo", "TEXT"),
            ("last_login", "TEXT"),
            ("failed_login_count", "INTEGER DEFAULT 0")
        ]:
            try:
                cursor.execute(f"SELECT {col} FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")

        conn.commit()

        # Pre-populating default users
        # 1. First ensure sumansingh exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ("sumansingh",))
        if not cursor.fetchone():
            suman_pwd = "041976@"
            suman_hash = hashlib.sha256(suman_pwd.encode("utf-8")).hexdigest()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, full_name, email, mobile, security_question, security_answer, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("sumansingh", suman_hash, "Administrator", timestamp, "Suman Singh", "sumansingh@neuraspend.com", "9876543210", "What is your favorite color?", "blue", "/static/assets/default_avatar.svg")
            )
            conn.commit()
            write_system_log("USER_CREATE", "Default Administrator 'sumansingh' provisioned safely.")

        # 2. Pre-populate other mock users if empty for visual demo consistency
        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()[0] == 1:  # Only sumansingh exists
            # Hash password for admin
            admin_pwd = "password123"
            admin_hash = hashlib.sha256(admin_pwd.encode("utf-8")).hexdigest()
            
            # Hash password for employee
            emp_pwd = "password123"
            emp_hash = hashlib.sha256(emp_pwd.encode("utf-8")).hexdigest()
 
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert Admin
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, full_name, email, mobile, security_question, security_answer, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("admin", admin_hash, "Admin", timestamp, "Suman Administrator", "admin@neuraspend.com", "9876543210", "What is your favorite color?", "blue", "/static/assets/default_avatar.svg")
            )
            
            # Insert Employee
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, full_name, email, mobile, security_question, security_answer, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("employee", emp_hash, "Employee", timestamp, "Suman Employee", "employee@neuraspend.com", "9876543211", "What is your high school?", "vivacollege", "/static/assets/default_avatar.svg")
            )
            
            conn.commit()
            write_system_log("SYSTEM_INIT", "Mock Admin & Employee users provisioned.")

        # 3. Check and seed demo data for all users if they have fewer than 10 expenses.
        # This guarantees clean, complete data for Suman Singh and Admin out-of-the-box.
        cursor.execute("SELECT id, username FROM users")
        all_users = cursor.fetchall()
        for u in all_users:
            u_id = u['id']
            cursor.execute("SELECT COUNT(*) FROM expenses WHERE user_id = ?", (u_id,))
            exp_count = cursor.fetchone()[0]
            if exp_count < 10:
                # Purge any partial/legacy test data for this specific user
                cursor.execute("DELETE FROM expenses WHERE user_id = ?", (u_id,))
                cursor.execute("DELETE FROM budgets WHERE user_id = ?", (u_id,))
                cursor.execute("DELETE FROM goals WHERE user_id = ?", (u_id,))
                cursor.execute("DELETE FROM recurring_expenses WHERE user_id = ?", (u_id,))
                cursor.execute("DELETE FROM rewards WHERE user_id = ?", (u_id,))
                cursor.execute("DELETE FROM audit_logs WHERE user_id = ?", (u_id,))
                
                # Seed complete structured dataset
                seed_demo_data(cursor, u_id)
        conn.commit()


def seed_demo_data(cursor, user_id):
    """
    Auto-seeds comprehensive demonstration data for a user_id
    to facilitate high-fidelity final-year BCA project presentations.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # A. Seed Enterprise Budget limit (₹20,000 limit, ₹16,000 warning)
    cursor.execute(
        """
        INSERT INTO budgets (monthly_limit, warning_limit, created_at, user_id)
        VALUES (?, ?, ?, ?)
        """,
        (20000.0, 16000.0, timestamp, user_id)
    )

    # B. Seed savings goals (Laptop, Emergency, and Vacation Funds)
    goals = [
        ("Laptop Fund", 70000.0, 45000.0, "2026-01-10 12:00:00"),
        ("Emergency Fund", 50000.0, 32000.0, "2026-02-05 10:00:00"),
        ("Vacation Fund", 30000.0, 18000.0, "2026-03-20 15:30:00")
    ]
    for title, target, saved, date_str in goals:
        cursor.execute(
            """
            INSERT INTO goals (title, target, saved, created_at, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, target, saved, date_str, user_id)
        )

    # C. Seed monthly scheduled recurring obligations
    recurrings = [
        ("Flat Rent", 8000.0, "Housing", "Monthly", "2026-06-01"),
        ("High-Speed Internet", 899.0, "Utilities", "Monthly", "2026-06-05"),
        ("Netflix Standard", 199.0, "Entertainment", "Monthly", "2026-06-10"),
        ("Health Insurance Premium", 2500.0, "Health", "Monthly", "2026-06-15")
    ]
    for title, amount, category, frequency, due_date in recurrings:
        cursor.execute(
            """
            INSERT INTO recurring_expenses (title, amount, category, frequency, next_due_date, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, amount, category, frequency, due_date, user_id)
        )

    # D. Seed historical rewards credit ledgers (Optimized for Suman's exact profile targets: Total Savings = ₹42,500, Total Rewards = ₹1,250)
    rewards = [
        ("2025-12", 8000.0, 240.0, "2025-12-31 18:00:00"),
        ("2026-01", 10000.0, 290.0, "2026-01-31 18:00:00"),
        ("2026-02", 9000.0, 270.0, "2026-02-28 18:00:00"),
        ("2026-03", 6000.0, 200.0, "2026-03-31 18:00:00"),
        ("2026-04", 4500.0, 150.0, "2026-04-30 18:00:00"),
        ("2026-05", 5000.0, 100.0, "2026-05-23 18:00:00")
    ]
    for month, savings, reward_amt, date_str in rewards:
        cursor.execute(
            """
            INSERT INTO rewards (user_id, month, savings, reward_amount, credited_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, month, savings, reward_amt, date_str)
        )

    # E. Seed chronological expenses from Nov 2025 to May 2026 (Total All-Time: ₹85,420)
    # 1. May 2026 - Adds up to EXACTLY ₹12,300 spent!
    may_expenses = [
        ("Restaurant Dinner", "Office celebration dinner", 450.0, "Food & Dining", "UPI", "2026-05-02"),
        ("Cab Booking", "Uber commute to client site", 250.0, "Travel & Transport", "Cash", "2026-05-04"),
        ("Headphones", "Noise-cancelling office gear", 2000.0, "Shopping", "Credit Card", "2026-05-05"),
        ("Movie Ticket", "Imax weekend ticket", 500.0, "Entertainment", "UPI", "2026-05-08"),
        ("Grocery Shopping", "Monthly D-Mart supplies", 1250.0, "Food & Dining", "Debit Card", "2026-05-10"),
        ("Internet Bill", "Airtel Fiber monthly due", 899.0, "Utilities", "UPI", "2026-05-12"),
        ("Online Course", "BCA project tutorial course", 1500.0, "Education", "Credit Card", "2026-05-15"),
        ("Train Ticket", "Holiday commute ticketing", 2300.0, "Travel & Transport", "Bank Transfer", "2026-05-18"),
        ("Pharmacy", "Multi-vitamins and first-aid", 750.0, "Health", "Cash", "2026-05-20"),
        ("Home Supplies", "Cleaning tools and toiletries", 650.0, "Miscellaneous", "UPI", "2026-05-22"),
        ("Office stationery", "Pens, notebooks and files", 1751.0, "Miscellaneous", "UPI", "2026-05-24")
    ]

    # 2. April 2026 - Adds up to EXACTLY ₹11,300 spent!
    apr_expenses = [
        ("Burger meal", "Lunch with colleagues", 320.0, "Food & Dining", "UPI", "2026-04-02"),
        ("Mobile Recharge", "Airtel prepaid pack", 499.0, "Utilities", "UPI", "2026-04-05"),
        ("Metro ticket", "Local rail commute card", 280.0, "Travel & Transport", "Cash", "2026-04-08"),
        ("Electricity Bill", "MSEB power billing due", 2100.0, "Utilities", "Bank Transfer", "2026-04-10"),
        ("Internet Bill", "Airtel Fiber payment", 899.0, "Utilities", "UPI", "2026-04-12"),
        ("Wireless mouse", "Logitech keyboard accessories", 1200.0, "Shopping", "Credit Card", "2026-04-15"),
        ("Monthly Groceries", "Big Basket home grocery delivery", 2350.0, "Food & Dining", "Debit Card", "2026-04-18"),
        ("Bowling game", "Weekend hangout with class friends", 500.0, "Entertainment", "UPI", "2026-04-20"),
        ("Health Supplements", "Omega-3 and protein pack", 1150.0, "Health", "UPI", "2026-04-22"),
        ("Reference Books", "Visual basic programming text", 850.0, "Education", "Cash", "2026-04-25"),
        ("Mutual Fund SIP", "Index fund savings allocation", 1152.0, "Investments", "Bank Transfer", "2026-04-28")
    ]

    # 3. March 2026 - Adds up to EXACTLY ₹9,800 spent!
    mar_expenses = [
        ("Cafe Coffee", "Meeting at Starbucks cafe", 280.0, "Food & Dining", "Credit Card", "2026-03-02"),
        ("Mobile Recharge", "Monthly data pack", 499.0, "Utilities", "UPI", "2026-03-05"),
        ("Uber cab", "Commute to seminar hall", 420.0, "Travel & Transport", "UPI", "2026-03-08"),
        ("Water Bill", "Municipal corporation due", 350.0, "Utilities", "Cash", "2026-03-10"),
        ("Internet Bill", "Airtel Fiber", 899.0, "Utilities", "UPI", "2026-03-12"),
        ("Formal Shoes", "Bata black shoes for viva", 2500.0, "Shopping", "Debit Card", "2026-03-15"),
        ("Weekly Groceries", "Local market vegetables & milk", 1800.0, "Food & Dining", "Cash", "2026-03-18"),
        ("Standup Comedy", "Ticket for weekend theater show", 700.0, "Entertainment", "UPI", "2026-03-21"),
        ("Udemy Course", "Advanced Python boot camp certification", 450.0, "Education", "Credit Card", "2026-03-24"),
        ("Barber haircut", "Grooming session", 350.0, "Miscellaneous", "Cash", "2026-03-27"),
        ("Mutual Fund SIP", "Automated stock portfolio", 1552.0, "Investments", "Bank Transfer", "2026-03-30")
    ]

    # 4. February 2026 - Adds up to EXACTLY ₹10,200 spent!
    feb_expenses = [
        ("Pizza Night", "Dinner with high school friends", 550.0, "Food & Dining", "UPI", "2026-02-02"),
        ("Mobile Recharge", "Prepaid validity plan", 499.0, "Utilities", "UPI", "2026-02-04"),
        ("Auto Rickshaw", "Commute to viva mock centers", 150.0, "Travel & Transport", "Cash", "2026-02-08"),
        ("Electricity Bill", "MSEB power billing", 1850.0, "Utilities", "Bank Transfer", "2026-02-10"),
        ("Internet Bill", "Broadband internet due", 899.0, "Utilities", "UPI", "2026-02-12"),
        ("Valentines Gift", "Gold plated pendant purchase", 2200.0, "Shopping", "Credit Card", "2026-02-14"),
        ("Grocery Shopping", "Provisions from Reliance Smart", 1550.0, "Food & Dining", "Debit Card", "2026-02-16"),
        ("Gaming Arcade", "VR games and bowling alley", 600.0, "Entertainment", "UPI", "2026-02-18"),
        ("Dental checkup", "Root canal consultancy fee", 800.0, "Health", "Cash", "2026-02-21"),
        ("Home cleaning items", "Floor cleaner, detergents, mop", 1102.0, "Miscellaneous", "UPI", "2026-02-25")
    ]

    # 5. January 2026 - Adds up to EXACTLY ₹8,500 spent!
    jan_expenses = [
        ("Restaurant Lunch", "Burger and fries lunch", 350.0, "Food & Dining", "UPI", "2026-01-02"),
        ("Mobile Recharge", "Prepaid bundle recharge", 499.0, "Utilities", "UPI", "2026-01-05"),
        ("Cab Fare", "Local travel commute", 300.0, "Travel & Transport", "Cash", "2026-01-10"),
        ("Internet Bill", "Airtel broadband", 899.0, "Utilities", "UPI", "2026-01-12"),
        ("Winter Jacket", "Quilted polyester puffer jacket", 2450.0, "Shopping", "Credit Card", "2026-01-15"),
        ("Grocery Shopping", "Vegetables and pantry essentials", 1200.0, "Food & Dining", "Debit Card", "2026-01-18"),
        ("Movie Night", "Multiplex tickets for movie", 400.0, "Entertainment", "UPI", "2026-01-20"),
        ("Cough Syrup", "Painkillers and throat spray", 150.0, "Health", "Cash", "2026-01-22"),
        ("Gift for Friend", "Wireless earbud box", 1250.0, "Miscellaneous", "UPI", "2026-01-25"),
        ("Petrol refueling", "Bike fuel topup card", 1002.0, "Travel & Transport", "Debit Card", "2026-01-28")
    ]

    # 6. December 2025 - Adds up to EXACTLY ₹16,820 spent!
    dec_expenses = [
        ("Laptop Fund Allotment", "Savings goal starter deposit", 15000.0, "Investments", "Bank Transfer", "2025-12-10"),
        ("Winter Holiday Train", "Family holiday travel ticket", 1820.0, "Travel & Transport", "UPI", "2025-12-22")
    ]

    # 7. November 2025 - Adds up to EXACTLY ₹16,500 spent!
    nov_expenses = [
        ("Diwali Gifts & Shopping", "Gifts for family and close relatives", 10000.0, "Shopping", "Credit Card", "2025-11-10"),
        ("Festive Dinner", "Diwali family restaurant dinner", 3500.0, "Food & Dining", "UPI", "2025-11-12"),
        ("Home Decoration", "Diwali lighting and decorative items", 3000.0, "Miscellaneous", "Cash", "2025-11-14")
    ]

    # Batch insert all transactions
    all_expenses = may_expenses + apr_expenses + mar_expenses + feb_expenses + jan_expenses + dec_expenses + nov_expenses
    for title, desc, amt, cat, pm, date_str in all_expenses:
        cursor.execute(
            """
            INSERT INTO expenses (title, description, amount, category, payment_method, transaction_date, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, desc, amt, cat, pm, date_str, f"{date_str} 14:00:00", user_id)
        )

    # F. Insert descriptive audit logs inside system
    audit_events = [
        ("SYSTEM_INIT", "Enterprise visual Facelift seeded successfully.", "2026-05-01 10:00:00"),
        ("ADD_GOAL", "Created Laptop savings goal target (₹70,000).", "2026-05-05 11:30:00"),
        ("SETTINGS_CHANGE", "Visual settings preferences updated (Theme: Dark | Currency: INR)", "2026-05-12 09:00:00"),
        ("REWARD_CREDIT", "Credited simulated savings wallet rewards: ₹100.00 for May 2026.", "2026-05-23 18:05:00")
    ]
    for ev_type, details, log_time in audit_events:
        cursor.execute(
            """
            INSERT INTO audit_logs (event_type, details, timestamp, user_id)
            VALUES (?, ?, ?, ?)
            """,
            (ev_type, details, log_time, user_id)
        )


# Compile structural database tables
initialize_database()


