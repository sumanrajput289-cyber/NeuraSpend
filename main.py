# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Principal Web Bootstrapper Server
"""

import os
import sys
import threading
import time
import webbrowser
import logging
from datetime import datetime

# Flask Web framework imports
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename

# Internal business logic and database drivers
import database
from database import get_db_connection, write_system_log
from settings import load_user_settings, save_user_settings
from parser import parse_transaction_text
from predictor import calculate_analytical_forecasts
from ocr_scanner import execute_receipt_ocr
from reports import compile_pdf_report, compile_excel_report, compile_monthly_summary_pdf
from backup_manager import execute_database_backup, list_available_backups, execute_database_restore

app = Flask(__name__)
app.secret_key = "neuraspend_offline_web_key_7788"

# Enforce secure user session variables locally
USER_SESSION = {
    "user_id": 1,
    "username": "sumansingh",
    "role": "Administrator",
    "full_name": "Suman Singh",
    "email": "sumansingh@neuraspend.com",
    "mobile": "9876543210",
    "profile_photo": "/static/assets/default_avatar.svg",
    "logged_in": False
}


def start_browser_auto_launch():
    """
    Spawns a delayed background thread to automatically open the default
    web browser once the local Flask server port becomes active.
    """
    def open_browser():
        time.sleep(1.5)  # Wait for Flask thread to boot up fully
        logging.info("Auto-launching default system browser to: http://127.0.0.1:5000")
        webbrowser.open("http://127.0.0.1:5000")

    launch_thread = threading.Thread(target=open_browser)
    launch_thread.daemon = True
    launch_thread.start()


# --------------------------------------------------------------------------
# 1. VIEW TEMPLATE CONTROLLERS
# --------------------------------------------------------------------------
@app.route("/")
@app.route("/login")
def render_login():
    if USER_SESSION["logged_in"]:
        return redirect("/dashboard")
    return render_template("login.html")


@app.route("/dashboard")
def render_dashboard():
    if not USER_SESSION["logged_in"]:
        return redirect("/login")
    return render_template("dashboard.html")


# --------------------------------------------------------------------------
# 2. AUTHENTICATION, REGISTRATION & RECOVERY APIS (Feature 14)
# --------------------------------------------------------------------------
@app.route("/login", methods=["POST"])
def handle_web_login():
    username_or_email = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username_or_email or not password:
        return jsonify({"success": False, "message": "Username/Email and password are required."}), 400

    try:
        import hashlib
        computed_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Support login via both username or email
            cursor.execute(
                """
                SELECT id, username, email, password_hash, role, full_name, mobile, profile_photo, failed_login_count 
                FROM users 
                WHERE username = ? OR email = ?
                """, 
                (username_or_email, username_or_email)
            )
            user_row = cursor.fetchone()

        if user_row:
            db_id = user_row["id"]
            db_username = user_row["username"]
            db_email = user_row["email"]
            db_hash = user_row["password_hash"]
            db_role = user_row["role"]
            db_full_name = user_row["full_name"] or db_username
            db_mobile = user_row["mobile"] or ""
            db_photo = user_row["profile_photo"] or "/static/assets/default_avatar.png"
            failed_count = user_row["failed_login_count"] or 0

            # Enforce Account lockout check (Feature 14 counter check)
            if failed_count >= 5:
                write_system_log("SECURITY_ALERT", f"Attempted login on locked account: '{db_username}'", db_id)
                return jsonify({"success": False, "message": "Account suspended. Excess wrong login attempts reached."}), 403

            if computed_hash == db_hash:
                # Reset failed login count and update last login
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET failed_login_count = 0, last_login = ? WHERE id = ?", (timestamp, db_id))
                    conn.commit()

                # Establish current session states
                USER_SESSION["user_id"] = db_id
                USER_SESSION["username"] = db_username
                USER_SESSION["role"] = db_role
                USER_SESSION["full_name"] = db_full_name
                USER_SESSION["email"] = db_email
                USER_SESSION["mobile"] = db_mobile
                USER_SESSION["profile_photo"] = db_photo
                USER_SESSION["logged_in"] = True
                
                write_system_log("LOGIN", f"Web Session initiated for: '{db_username}' ({db_role})", db_id)
                return jsonify({
                    "success": True, 
                    "user": {
                        "username": db_username, 
                        "role": db_role, 
                        "full_name": db_full_name,
                        "profile_photo": db_photo
                    }
                })
            else:
                # Increment failed count
                new_failed = failed_count + 1
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET failed_login_count = ? WHERE id = ?", (new_failed, db_id))
                    conn.commit()

                write_system_log("LOGIN_FAILED", f"Invalid password for user: '{db_username}'. Fail count: {new_failed}", db_id)
                remaining = max(0, 5 - new_failed)
                return jsonify({"success": False, "message": f"Invalid credentials. {remaining} attempts remaining."}), 401
            
        write_system_log("LOGIN_FAILED", f"Failed login for non-existent profile: '{username_or_email}'", 1)
        return jsonify({"success": False, "message": "Username or Email does not exist."}), 401
    except Exception as err:
        logging.error("Security login API failure: %s", str(err))
        return jsonify({"success": False, "message": "Database server unreachable."}), 500


@app.route("/register", methods=["POST"])
def handle_web_register():
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    mobile = request.form.get("mobile", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    security_question = request.form.get("security_question", "").strip()
    security_answer = request.form.get("security_answer", "").strip()

    if not full_name or not username or not email or not password or not security_question or not security_answer:
        return jsonify({"success": False, "message": "All required validation parameters must be filled."}), 400

    if password != confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match."}), 400

    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters long."}), 400

    try:
        # Check uniqueness
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Username or Email already registered."}), 400

        # Handle Profile Photo Upload (Feature 16 / Avatar System)
        profile_photo_path = "/static/assets/default_avatar.png"
        if "profile_photo" in request.files:
            file = request.files["profile_photo"]
            if file and file.filename:
                save_dir = os.path.join(app.root_path, "static", "assets", "avatars")
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                filename = secure_filename(f"avatar_{username}_{int(time.time())}_{file.filename}")
                filepath = os.path.join(save_dir, filename)
                file.save(filepath)
                profile_photo_path = f"/static/assets/avatars/{filename}"

        # Hash Password
        import hashlib
        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, full_name, email, mobile, security_question, security_answer, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (username, pwd_hash, "Employee", timestamp, full_name, email, mobile, security_question, security_answer, profile_photo_path)
            )
            conn.commit()

        write_system_log("USER_CREATE", f"New Employee registered: '{username}' via web interface", 1)
        return jsonify({"success": True, "message": "Account created successfully. You can now login!"})
    except Exception as err:
        logging.error("Registration endpoint failed: %s", str(err))
        return jsonify({"success": False, "message": f"Server registration error: {str(err)}"}), 500


@app.route("/api/forgot/question", methods=["POST"])
def handle_forgot_question():
    username_or_email = request.form.get("username", "").strip()
    if not username_or_email:
        return jsonify({"success": False, "message": "Username or Email is required."}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT security_question FROM users WHERE username = ? OR email = ?", (username_or_email, username_or_email))
            row = cursor.fetchone()
        
        if row:
            return jsonify({"success": True, "question": row["security_question"]})
        return jsonify({"success": False, "message": "No account linked to this identifier."}), 404
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/api/forgot/verify", methods=["POST"])
def handle_forgot_verify():
    username_or_email = request.form.get("username", "").strip()
    answer = request.form.get("security_answer", "").strip().lower()
    new_password = request.form.get("new_password", "")

    if not username_or_email or not answer or not new_password:
        return jsonify({"success": False, "message": "All password recovery params required."}), 400

    if len(new_password) < 8:
        return jsonify({"success": False, "message": "New password must be at least 8 characters long."}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, security_answer FROM users WHERE username = ? OR email = ?", (username_or_email, username_or_email))
            row = cursor.fetchone()

        if row:
            db_id = row["id"]
            db_answer = row["security_answer"].strip().lower()

            if answer == db_answer:
                # Answer verified, hash new password and reset lockouts
                import hashlib
                pwd_hash = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET password_hash = ?, failed_login_count = 0 WHERE id = ?", (pwd_hash, db_id))
                    conn.commit()

                write_system_log("PASSWORD_RESET", f"Password reset successfully via Security Question challenge for user ID #{db_id}", db_id)
                return jsonify({"success": True, "message": "Password updated successfully!"})
            else:
                return jsonify({"success": False, "message": "Security answer verification failed."}), 401
        return jsonify({"success": False, "message": "Identifier match failed."}), 404
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/logout", methods=["POST"])
def handle_web_logout():
    user_id = USER_SESSION["user_id"]
    user = USER_SESSION["username"]
    
    # Reset local session
    USER_SESSION["user_id"] = 1
    USER_SESSION["username"] = "sumansingh"
    USER_SESSION["role"] = "Administrator"
    USER_SESSION["full_name"] = "Suman Singh"
    USER_SESSION["email"] = "sumansingh@neuraspend.com"
    USER_SESSION["mobile"] = "9876543210"
    USER_SESSION["profile_photo"] = "/static/assets/default_avatar.svg"
    USER_SESSION["logged_in"] = False
    
    write_system_log("LOGOUT", f"Web Session terminated for: '{user}'", user_id)
    return jsonify({"success": True})


# --------------------------------------------------------------------------
# 3. CORE BUSINESS INTELLIGENCE METRICS & FORECASTS (Feature 1, 2, 17)
# --------------------------------------------------------------------------
# 3. CORE BUSINESS INTELLIGENCE METRICS & FORECASTS (Feature 1, 2, 17)
# --------------------------------------------------------------------------
@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_summary():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]
    role = USER_SESSION["role"]
    username = USER_SESSION["username"]
    current_month = datetime.now().strftime("%Y-%m")
    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        # Load user configurations
        settings = load_user_settings()
        currency = settings.get("currency", "₹")

        # Query databases
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Fetch expenses (Multi-user roles specific, Feature 14)
            if role in ("Admin", "Administrator"):
                cursor.execute("SELECT * FROM expenses ORDER BY transaction_date DESC")
            elif role == "Manager":
                # Manager can view all expenses for audits
                cursor.execute("SELECT * FROM expenses ORDER BY transaction_date DESC")
            else:
                cursor.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY transaction_date DESC", (user_id,))
            expenses = [dict(row) for row in cursor.fetchall()]

            # 2. Fetch goals
            if role in ("Admin", "Administrator") or role == "Manager":
                cursor.execute("SELECT * FROM goals ORDER BY id DESC")
            else:
                cursor.execute("SELECT * FROM goals WHERE user_id = ? ORDER BY id DESC", (user_id,))
            goals = [dict(row) for row in cursor.fetchall()]

            # 3. Fetch recurring
            if role in ("Admin", "Administrator") or role == "Manager":
                cursor.execute("SELECT * FROM recurring_expenses ORDER BY next_due_date ASC")
            else:
                cursor.execute("SELECT * FROM recurring_expenses WHERE user_id = ? ORDER BY next_due_date ASC", (user_id,))
            recurring = [dict(row) for row in cursor.fetchall()]

            # 4. Fetch budget target limit
            if role in ("Admin", "Administrator") or role == "Manager":
                cursor.execute("SELECT monthly_limit, warning_limit FROM budgets ORDER BY id DESC LIMIT 1")
            else:
                cursor.execute("SELECT monthly_limit, warning_limit FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
            b_row = cursor.fetchone()
            budget = dict(b_row) if b_row else {
                "monthly_limit": settings.get("default_monthly_budget", 50000.0),
                "warning_limit": settings.get("default_warning_limit", 40000.0)
            }

            # 5. Fetch persistent rewards wallet and history (Feature 9)
            cursor.execute("SELECT SUM(reward_amount) as total_rewards FROM rewards WHERE user_id = ?", (user_id,))
            rewards_sum_row = cursor.fetchone()
            total_rewards = rewards_sum_row["total_rewards"] if rewards_sum_row and rewards_sum_row["total_rewards"] else 0.0

            cursor.execute("SELECT * FROM rewards WHERE user_id = ? ORDER BY month DESC", (user_id,))
            rewards_history = [dict(row) for row in cursor.fetchall()]

        # Calculate KPI statistics cards (Feature 17)
        total_all = sum(float(e["amount"]) for e in expenses)
        total_month = sum(float(e["amount"]) for e in expenses if e["transaction_date"].startswith(current_month))
        today_spend = sum(float(e["amount"]) for e in expenses if e["transaction_date"] == today_str)
        remaining = max(0.0, float(budget["monthly_limit"]) - total_month)
        count = len(expenses)
        max_expense = max([float(e["amount"]) for e in expenses]) if expenses else 0.0
        avg_expense = total_all / count if count > 0 else 0.0

        # Calculate prediction forecasts & Financial Health Score (Feature 1 & 2)
        predictor_results = calculate_analytical_forecasts(expenses, float(budget["monthly_limit"]))

        # Dynamic Saver Level Determination
        saver_level = "Bronze Saver"
        if total_rewards >= 2000.0:
            saver_level = "Diamond Saver"
        elif total_rewards >= 1000.0:
            saver_level = "Platinum Saver"
        elif total_rewards >= 500.0:
            saver_level = "Gold Saver"
        elif total_rewards >= 200.0:
            saver_level = "Silver Saver"

        # Dynamic Achievements System
        achievements = []
        # Achievement 1: First Savings
        if total_rewards > 0:
            achievements.append({"id": "badge_first_savings", "title": "First Savings", "desc": "Earned your first savings reward!", "unlocked": True})
        else:
            achievements.append({"id": "badge_first_savings", "title": "First Savings", "desc": "Earn your first savings reward", "unlocked": False})
            
        # Achievement 2: Budget Master
        if count > 0 and total_month <= float(budget["monthly_limit"]):
            achievements.append({"id": "badge_budget_master", "title": "Budget Master", "desc": "Kept monthly spend within limits!", "unlocked": True})
        else:
            achievements.append({"id": "badge_budget_master", "title": "Budget Master", "desc": "Keep spending under budget", "unlocked": False})

        # Achievement 3: Goal Achiever
        has_completed_goal = any(float(g["saved"]) >= float(g["target"]) for g in goals)
        achievements.append({
            "id": "badge_goal_achiever", 
            "title": "Goal Achiever", 
            "desc": "Fully completed a savings target!", 
            "unlocked": has_completed_goal
        })

        # Achievement 4: Financial Champion
        achievements.append({
            "id": "badge_financial_champion", 
            "title": "Financial Champion", 
            "desc": "Scored 85+ Financial Health rating!", 
            "unlocked": predictor_results["health_score"] >= 85
        })

        # Achievement 5: Streak Master (Consistent Logging)
        achievements.append({
            "id": "badge_streak_master", 
            "title": "Streak Master", 
            "desc": "Logged more than 10 expenses!", 
            "unlocked": count >= 10
        })

        # Calculate exactly 12 specific FinTech counting KPI cards metrics dynamically
        savings_balance = max(0.0, float(budget["monthly_limit"]) - total_month)
        completed_goals = sum(1 for g in goals if float(g["saved"]) >= float(g["target"]))
        active_goals = sum(1 for g in goals if float(g["saved"]) < float(g["target"]))
        transaction_count = count
        health_score = predictor_results["health_score"]
        goals_count = len(goals)

        metrics = {
            "total_all": total_all,
            "total_month": total_month,
            "today_spend": today_spend,
            "max_expense": max_expense,
            "avg_expense": avg_expense,
            "remaining_budget": remaining,
            "health_score": health_score,
            "total_rewards": total_rewards,
            "savings_balance": savings_balance,
            "completed_goals": completed_goals,
            "active_goals": active_goals,
            "transaction_count": transaction_count,
            "goals_count": goals_count,
            "recurring_count": len(recurring),
            "saver_level": saver_level
        }

        # Dynamic user package for display
        user_profile = {
            "username": USER_SESSION["username"],
            "full_name": USER_SESSION["full_name"],
            "email": USER_SESSION["email"],
            "mobile": USER_SESSION["mobile"],
            "profile_photo": USER_SESSION["profile_photo"],
            "role": USER_SESSION["role"]
        }

        return jsonify({
            "success": True,
            "currency": currency,
            "role": role,
            "user": user_profile,
            "metrics": metrics,
            "expenses": expenses,
            "goals": goals,
            "recurring": recurring,
            "budget": budget,
            "rewards_history": rewards_history,
            "achievements": achievements,
            "total_month": total_month,
            "predictor": predictor_results
        })
    except Exception as err:
        logging.error("Dashboard API failed: %s", str(err))
        return jsonify({"success": False, "message": str(err)}), 500


# --------------------------------------------------------------------------
# EXTRA ENTERPRISE UTILITY ROUTES (Features 3, 9, 10, 16)
# --------------------------------------------------------------------------
@app.route("/api/expenses/duplicate", methods=["POST"])
def handle_expense_duplicate():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]
    exp_id = int(request.form.get("id", 0))

    if exp_id <= 0:
        return jsonify({"success": False, "message": "Invalid ID"}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (exp_id,))
            row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "Expense not found."}), 404

        # Duplicate values
        title = f"{row['title']} (Copy)"
        description = row['description'] or ""
        amount = row['amount']
        category = row['category']
        payment_method = row['payment_method']
        transaction_date = row['transaction_date']
        attachment_path = row['attachment_path'] or ""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO expenses (title, description, amount, category, payment_method, transaction_date, created_at, user_id, attachment_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, description, amount, category, payment_method, transaction_date, timestamp, user_id, attachment_path)
            )
            conn.commit()

        write_system_log("DUPLICATE_EXPENSE", f"Duplicated record #{exp_id} as '{title}'", user_id)
        return jsonify({"success": True})
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/api/expenses/bulk_delete", methods=["POST"])
def handle_expense_bulk_delete():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]
    ids_str = request.form.get("ids", "")
    if not ids_str:
        return jsonify({"success": False, "message": "No transaction indices specified."}), 400

    try:
        ids = [int(i.strip()) for i in ids_str.split(",") if i.strip()]
        if not ids:
            return jsonify({"success": False, "message": "Parse failure."}), 400

        placeholders = ",".join("?" for _ in ids)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Bulk delete query
            cursor.execute(f"DELETE FROM expenses WHERE id IN ({placeholders})", ids)
            conn.commit()

        write_system_log("BULK_DELETE", f"Permanently purged transactions: {ids_str}", user_id)
        return jsonify({"success": True, "count": len(ids)})
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/api/expenses/bulk_import", methods=["POST"])
def handle_expense_bulk_import():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]
    file = request.files.get("csv_file")
    if not file or not file.filename:
        return jsonify({"success": False, "message": "CSV sheet file not uploaded."}), 400

    try:
        import csv
        import io
        stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        csv_reader = csv.reader(stream)
        
        # Skip header if present
        header = next(csv_reader, None)
        
        # Validate column headers
        imported_count = 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            for row in csv_reader:
                if not row or len(row) < 3:
                    continue
                # Template columns: Title, Amount, Category, PaymentMethod, Date, Description
                title = row[0].strip()
                try:
                    amount = float(row[1])
                except ValueError:
                    continue
                category = row[2].strip() if len(row) > 2 and row[2].strip() else "Others"
                payment_method = row[3].strip() if len(row) > 3 and row[3].strip() else "UPI"
                transaction_date = row[4].strip() if len(row) > 4 and row[4].strip() else datetime.now().strftime("%Y-%m-%d")
                description = row[5].strip() if len(row) > 5 else ""

                cursor.execute(
                    """
                    INSERT INTO expenses (title, description, amount, category, payment_method, transaction_date, created_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, description, amount, category, payment_method, transaction_date, timestamp, user_id)
                )
                imported_count += 1
            conn.commit()

        write_system_log("BULK_IMPORT", f"Successfully imported {imported_count} transactional entries via CSV upload.", user_id)
        return jsonify({"success": True, "count": imported_count})
    except Exception as err:
        logging.error("Bulk CSV import crashed: %s", str(err))
        return jsonify({"success": False, "message": f"CSV Parse error: {str(err)}"}), 500


@app.route("/api/profile/update", methods=["POST"])
def handle_profile_update():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    mobile = request.form.get("mobile", "").strip()
    password = request.form.get("password", "")

    if not full_name or not email:
        return jsonify({"success": False, "message": "Full Name and Email fields are required."}), 400

    try:
        # Check uniqueness against other users
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?", (email, email, user_id))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Email already registered to another user."}), 400

        # Handle optional avatar image
        avatar_path = USER_SESSION["profile_photo"]
        if "profile_photo" in request.files:
            file = request.files["profile_photo"]
            if file and file.filename:
                save_dir = os.path.join(app.root_path, "static", "assets", "avatars")
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                filename = secure_filename(f"avatar_{user_id}_{int(time.time())}_{file.filename}")
                filepath = os.path.join(save_dir, filename)
                file.save(filepath)
                avatar_path = f"/static/assets/avatars/{filename}"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET full_name = ?, email = ?, mobile = ?, profile_photo = ?
                WHERE id = ?
                """,
                (full_name, email, mobile, avatar_path, user_id)
            )
            
            if password and len(password) >= 8:
                import hashlib
                pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id))
            
            conn.commit()

        # Update session cache
        USER_SESSION["full_name"] = full_name
        USER_SESSION["email"] = email
        USER_SESSION["mobile"] = mobile
        USER_SESSION["profile_photo"] = avatar_path

        write_system_log("PROFILE_UPDATE", f"User profile details updated successfully.", user_id)
        return jsonify({"success": True})
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/api/rewards/credit", methods=["POST"])
def handle_rewards_credit():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]
    month = request.form.get("month", "").strip() # e.g. "2026-05"

    if not month:
        return jsonify({"success": False, "message": "Target credit month required."}), 400

    try:
        # Load user configurations
        settings = load_user_settings()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if already credited
            cursor.execute("SELECT id FROM rewards WHERE user_id = ? AND month = ?", (user_id, month))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Savings reward already credited for this month."}), 400

            # Calculate spending and budget for this month
            cursor.execute("SELECT amount FROM expenses WHERE user_id = ? AND transaction_date LIKE ?", (user_id, f"{month}%"))
            month_spend = sum(float(row["amount"]) for row in cursor.fetchall())

            cursor.execute("SELECT monthly_limit FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
            b_row = cursor.fetchone()
            limit = float(b_row["monthly_limit"]) if b_row else settings.get("default_monthly_budget", 50000.0)

        savings = limit - month_spend
        if savings <= 0:
            return jsonify({"success": False, "message": f"Credit failed. No savings detected for {month} (Spends: {currency_symbol}{month_spend:.2f} | Budget: {currency_symbol}{limit:.2f})"}), 400

        # Reward credit is 2% of savings
        reward_amount = savings * 0.02
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO rewards (user_id, month, savings, reward_amount, credited_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, month, savings, reward_amount, timestamp)
            )
            conn.commit()

        write_system_log("REWARD_CREDIT", f"Credited simulated savings wallet rewards: {reward_amount:.2f} based on monthly savings of {savings:.2f}", user_id)
        return jsonify({"success": True, "reward_amount": reward_amount})
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


# --------------------------------------------------------------------------
# 4. LEDGER CRUD & ATTACHMENTS FILE MANAGER (Feature 16 & 18)
# --------------------------------------------------------------------------
@app.route("/api/expenses", methods=["POST", "PUT", "DELETE"])
def handle_expenses_api():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]

    try:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            amount = float(request.form.get("amount", 0))
            category = request.form.get("category", "Others")
            payment_method = request.form.get("payment_method", "UPI")
            transaction_date = request.form.get("transaction_date", "").strip()
            
            # Handle receipt file attachment (Feature 16)
            attachment_path = ""
            if "attachment" in request.files:
                file = request.files["attachment"]
                if file and file.filename:
                    # Save local copy inside assets/icons/ or static/assets/
                    save_dir = os.path.join(app.root_path, "static", "assets")
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    filename = secure_filename(f"receipt_{int(time.time())}_{file.filename}")
                    filepath = os.path.join(save_dir, filename)
                    file.save(filepath)
                    attachment_path = filepath

            if not title or amount <= 0 or not transaction_date:
                return jsonify({"success": False, "message": "Validation constraints failed."}), 400

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO expenses (title, description, amount, category, payment_method, transaction_date, created_at, user_id, attachment_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, description, amount, category, payment_method, transaction_date, timestamp, user_id, attachment_path)
                )
                conn.commit()

            write_system_log("ADD_EXPENSE", f"Committed: '{title}' for {amount}", user_id)
            return jsonify({"success": True})

        elif request.method == "PUT":
            exp_id = int(request.form.get("id", 0))
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            amount = float(request.form.get("amount", 0))
            category = request.form.get("category", "Others")
            payment_method = request.form.get("payment_method", "UPI")
            transaction_date = request.form.get("transaction_date", "").strip()
            
            # Handle attachment update
            attachment_path = request.form.get("attachment_path", "")
            if "attachment" in request.files:
                file = request.files["attachment"]
                if file and file.filename:
                    save_dir = os.path.join(app.root_path, "static", "assets")
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    filename = secure_filename(f"receipt_{int(time.time())}_{file.filename}")
                    filepath = os.path.join(save_dir, filename)
                    file.save(filepath)
                    attachment_path = filepath

            if exp_id <= 0 or not title or amount <= 0 or not transaction_date:
                return jsonify({"success": False, "message": "Validation constraints failed."}), 400

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE expenses
                    SET title = ?, description = ?, amount = ?, category = ?, payment_method = ?, transaction_date = ?, attachment_path = ?
                    WHERE id = ?
                    """,
                    (title, description, amount, category, payment_method, transaction_date, attachment_path, exp_id)
                )
                conn.commit()

            write_system_log("UPDATE_EXPENSE", f"Modified row #{exp_id}: '{title}'", user_id)
            return jsonify({"success": True})

        elif request.method == "DELETE":
            exp_id = int(request.args.get("id", 0))
            if exp_id <= 0:
                return jsonify({"success": False, "message": "Invalid ID"}), 400

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT title FROM expenses WHERE id = ?", (exp_id,))
                row = cursor.fetchone()
                title = row["title"] if row else "N/A"

                cursor.execute("DELETE FROM expenses WHERE id = ?", (exp_id,))
                conn.commit()

            write_system_log("DELETE_EXPENSE", f"Deleted row #{exp_id}: '{title}'", user_id)
            return jsonify({"success": True})

    except Exception as err:
        logging.error("Expenses API failed: %s", str(err))
        return jsonify({"success": False, "message": str(err)}), 500


# --------------------------------------------------------------------------
# 5. RECEIPT OCR IMAGE SCANNER & NLP PARSER (Feature 6 & 7)
# --------------------------------------------------------------------------
@app.route("/api/ocr", methods=["POST"])
def handle_receipt_ocr():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]
    file = request.files.get("receipt_image")
    
    if not file or not file.filename:
        return jsonify({"success": False, "message": "No receipt image uploaded."}), 400

    try:
        # Save temp file
        temp_dir = os.path.join(app.root_path, "logs")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        temp_filepath = os.path.join(temp_dir, f"temp_ocr_{file.filename}")
        file.save(temp_filepath)

        # Run optical receipt parser
        result = execute_receipt_ocr(temp_filepath)
        
        # Clean up temp file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

        if result["success"]:
            # Populate attachment path in response as well
            result["attachment_path"] = temp_filepath
            write_system_log("OCR_SCAN", f"Processed receipt image OCR scan successfully: detected merchant '{result['merchant']}'", user_id)
            return jsonify({"success": True, "data": result})
        else:
            return jsonify({"success": False, "message": result["error"]})
    except Exception as err:
        logging.error("OCR scan crashed: %s", str(err))
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/api/parser", methods=["POST"])
def handle_web_nlp_parser():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    text = request.form.get("text", "").strip()
    parsed = parse_transaction_text(text)
    return jsonify({"success": True, "data": parsed})


# --------------------------------------------------------------------------
# 6. SAVINGS GOALS & RECURRING SCHEDULERS APIS (Feature 4 & 5)
# --------------------------------------------------------------------------
@app.route("/api/goals", methods=["POST", "DELETE"])
def handle_goals_api():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]

    try:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            target = float(request.form.get("target", 0))
            saved = float(request.form.get("saved", 0))

            if not title or target <= 0 or saved < 0:
                return jsonify({"success": False, "message": "Validation constraints failed."}), 400

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

            write_system_log("ADD_GOAL", f"Set Savings Goal: '{title}' targeting {target}", user_id)
            return jsonify({"success": True})

        elif request.method == "DELETE":
            goal_id = int(request.args.get("id", 0))
            if goal_id <= 0:
                return jsonify({"success": False, "message": "Invalid identifier."}), 400

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
                conn.commit()

            write_system_log("DELETE_GOAL", f"Deleted Savings Goal row #{goal_id}", user_id)
            return jsonify({"success": True})

    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/api/recurring", methods=["POST", "DELETE"])
def handle_recurring_api():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]

    try:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            amount = float(request.form.get("amount", 0))
            frequency = request.form.get("frequency", "Monthly")
            next_due_date = request.form.get("next_due_date", "").strip()

            if not title or amount <= 0 or not next_due_date:
                return jsonify({"success": False, "message": "Validation constraints failed."}), 400

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO recurring_expenses (title, amount, category, frequency, next_due_date, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (title, amount, "Others", frequency, next_due_date, user_id)
                )
                conn.commit()

            write_system_log("ADD_RECURRING", f"Scheduled Recurring Due: '{title}' for {amount}", user_id)
            return jsonify({"success": True})

        elif request.method == "DELETE":
            row_id = int(request.args.get("id", 0))
            if row_id <= 0:
                return jsonify({"success": False, "message": "Invalid ID"}), 400

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recurring_expenses WHERE id = ?", (row_id,))
                conn.commit()

            write_system_log("DELETE_RECURRING", f"Deleted Recurring due row #{row_id}", user_id)
            return jsonify({"success": True})

    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


# --------------------------------------------------------------------------
# 7. SYSTEM CONFIGS & snap RECOVERIES APIS (Feature 11 & 12 & 15)
# --------------------------------------------------------------------------
@app.route("/api/budget", methods=["POST"])
def handle_budget_post():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    user_id = USER_SESSION["user_id"]
    try:
        limit = float(request.form.get("monthly_limit", 0))
        warn = float(request.form.get("warning_limit", 0))

        if limit <= 0 or warn <= 0 or warn > limit:
            return jsonify({"success": False, "message": "Validation constraints failed."}), 400

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO budgets (monthly_limit, warning_limit, created_at, user_id)
                VALUES (?, ?, ?, ?)
                """,
                (limit, warn, timestamp, user_id)
            )
            conn.commit()

        write_system_log("SET_BUDGET", f"Set monthly budget limit: {limit} (warn: {warn})", user_id)
        return jsonify({"success": True})
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/api/settings", methods=["GET", "POST"])
def handle_settings_api():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    if request.method == "GET":
        settings = load_user_settings()
        return jsonify({"success": True, "settings": settings})
        
    elif request.method == "POST":
        theme = request.form.get("theme", "Dark")
        currency = request.form.get("currency", "₹")
        export_folder = request.form.get("export_folder", "").strip()

        if not export_folder or not os.path.exists(export_folder):
            return jsonify({"success": False, "message": "Invalid export directory."}), 400

        settings = load_user_settings()
        settings["theme"] = theme
        settings["currency"] = currency
        settings["export_folder"] = export_folder

        success = save_user_settings(settings)
        if success:
            write_system_log("SETTINGS_CHANGE", f"Settings modified. Theme: {theme}, Currency: {currency}", USER_SESSION["user_id"])
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Settings storage failed."}), 500


@app.route("/api/backup", methods=["GET", "POST"])
def handle_backup_api():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    if request.method == "GET":
        backups = list_available_backups()
        return jsonify({"success": True, "backups": backups})
        
    elif request.method == "POST":
        success, msg = execute_database_backup()
        if success:
            return jsonify({"success": True, "filename": msg})
        return jsonify({"success": False, "message": msg}), 500


@app.route("/api/backup/restore", methods=["POST"])
def handle_restore_api():
    if not USER_SESSION["logged_in"]:
        return jsonify({"success": False, "message": "Access Denied"}), 403

    filename = request.form.get("filename", "")
    if not filename:
        return jsonify({"success": False, "message": "Backup filename missing."}), 400

    success, msg = execute_database_restore(filename)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": msg}), 500


@app.route("/api/audit", methods=["GET"])
def handle_audit_logs_api():
    if not USER_SESSION["logged_in"] or USER_SESSION["role"] not in ("Admin", "Administrator"):
        return jsonify({"success": False, "message": "Access Denied"}), 403

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, user_id, event_type, details FROM audit_logs ORDER BY id DESC LIMIT 100")
            rows = [dict(row) for row in cursor.fetchall()]
        return jsonify({"success": True, "audits": rows})
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


@app.route("/api/users", methods=["GET", "POST"])
def handle_users_admin_api():
    if not USER_SESSION["logged_in"] or USER_SESSION["role"] not in ("Admin", "Administrator"):
        return jsonify({"success": False, "message": "Access Denied"}), 403

    try:
        if request.method == "GET":
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY id ASC")
                users = [dict(row) for row in cursor.fetchall()]
            return jsonify({"success": True, "users": users})
            
        elif request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            if not username or not password:
                return jsonify({"success": False, "message": "All fields are required."}), 400

            import hashlib
            pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

            write_system_log("USER_CREATE", f"Registered Employee User Account: '{username}'", USER_SESSION["user_id"])
            return jsonify({"success": True})

    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."}), 400
    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


# --------------------------------------------------------------------------
# 8. MULTI-FORMAT REPORT DOWNLOAD APIS (Feature 10 & 19 & 20)
# --------------------------------------------------------------------------
@app.route("/api/reports", methods=["GET"])
def handle_reports_api():
    if not USER_SESSION["logged_in"]:
        return redirect("/login")

    user_id = USER_SESSION["user_id"]
    role = USER_SESSION["role"]
    format_type = request.args.get("format", "pdf").lower()
    
    try:
        settings = load_user_settings()
        export_dir = settings.get("export_folder", os.path.join(app.root_path, "exports"))
        currency = settings.get("currency", "₹")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch user-specific or admin-wide expenses
            if role in ("Admin", "Administrator"):
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

            limit = float(b_row["monthly_limit"]) if b_row else float(settings.get("default_monthly_budget", 50000.0))
            warn = float(b_row["warning_limit"]) if b_row else float(settings.get("default_warning_limit", 40000.0))

        pred_data = calculate_analytical_forecasts(expenses, limit)

        if format_type == "pdf":
            filepath = os.path.join(export_dir, "reports", "financial_report_suite.pdf")
            compile_pdf_report(filepath, expenses, limit, warn, pred_data, goals, currency)
            return send_file(filepath, as_attachment=True, download_name="financial_report_suite.pdf")
            
        elif format_type == "summary":
            filepath = os.path.join(export_dir, "reports", "monthly_financial_summary.pdf")
            compile_monthly_summary_pdf(filepath, expenses, limit, pred_data, currency)
            return send_file(filepath, as_attachment=True, download_name="monthly_financial_summary.pdf")
            
        elif format_type == "excel":
            filepath = os.path.join(export_dir, "excel", "financial_registry.xlsx")
            compile_excel_report(filepath, expenses, limit, goals, currency)
            return send_file(filepath, as_attachment=True, download_name="financial_registry.xlsx")
            
        elif format_type == "csv":
            filepath = os.path.join(export_dir, "csv", "transaction_ledger_export.csv")
            with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
                fieldnames = ["id", "title", "description", "amount", "category", "payment_method", "transaction_date", "created_at", "user_id", "attachment_path"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for exp in expenses:
                    row = {key: exp.get(key, "") for key in fieldnames}
                    writer.writerow(row)
            return send_file(filepath, as_attachment=True, download_name="transaction_ledger_export.csv")

        return "Invalid format.", 400
    except Exception as err:
        logging.error("Reports compile route failed: %s", str(err))
        return f"Analytical report compilation failed: {str(err)}", 500


# --------------------------------------------------------------------------
# 9. SERVER ROOT MAIN STARTUP RUNNER
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # Ensure offline directory checks are verified
    database.initialize_directories()

    # Configure server-side warning logs
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(database.LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Launch browser auto-open routine
    start_browser_auto_launch()

    try:
        logging.info("Starting NeuraSpend local web host server on port 5000...")
        app.run(host="127.0.0.1", port=5000, debug=False)
    except Exception as runtime_err:
        logging.critical("Web server failed to boot: %s", str(runtime_err))
        sys.exit(1)
