# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Security & Multi-User Authentication Center
"""

import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
from datetime import datetime
from database import get_db_connection, write_system_log


class SessionManager:
    """
    Maintains the current runtime session context of the authenticated user.
    Tracks user id, name, role, and login timestamp across the application.
    """
    _current_user_id = None
    _current_user = None
    _current_role = None
    _login_time = None

    @classmethod
    def start_session(cls, user_id, username, role):
        cls._current_user_id = user_id
        cls._current_user = username
        cls._current_role = role
        cls._login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_system_log("LOGIN", f"Session initiated: '{username}' ({role})", user_id)

    @classmethod
    def terminate_session(cls):
        if cls._current_user:
            write_system_log("LOGOUT", f"Session terminated: '{cls._current_user}'", cls._current_user_id)
        cls._current_user_id = None
        cls._current_user = None
        cls._current_role = None
        cls._login_time = None

    @classmethod
    def get_user_id(cls):
        return cls._current_user_id or 1

    @classmethod
    def get_user(cls):
        return cls._current_user or "Administrator"

    @classmethod
    def get_role(cls):
        return cls._current_role or "Admin"

    @classmethod
    def get_login_time(cls):
        return cls._login_time


class LoginFrame(tk.Frame):
    """
    Draws a modern, dark-themed login interface within a Tkinter window.
    Features modern flat components, secure locks counters, and credential mappings.
    """
    def __init__(self, parent, login_success_callback):
        # Premium obsidian dark theme background parameters
        bg_color = "#0F0F16"
        card_color = "#181824"
        accent_color = "#0A84FF"
        text_color = "#F2F2F7"
        muted_color = "#8E8E93"

        super().__init__(parent, bg=bg_color)
        self.parent = parent
        self.login_success_callback = login_success_callback
        self.failed_attempts = 0
        
        self.grid(row=0, column=0, sticky="nsew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        # Main login card layout
        self.card = tk.Frame(self, bg=card_color, padx=40, pady=40, bd=1, relief="solid", highlightthickness=0)
        self.card.configure(highlightbackground="#242433")
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        # Application Title Branding
        self.title_label = tk.Label(
            self.card, 
            text="NeuraSpend", 
            font=("Outfit", 26, "bold"), 
            bg=card_color, 
            fg=accent_color
        )
        self.title_label.pack(pady=(0, 5))

        self.tagline_label = tk.Label(
            self.card, 
            text="Enterprise Financial Intelligence Platform", 
            font=("Inter", 9), 
            bg=card_color, 
            fg=muted_color
        )
        self.tagline_label.pack(pady=(0, 30))

        # Username entry field
        self.username_label = tk.Label(
            self.card, 
            text="SECURITY USERNAME", 
            font=("Outfit", 8, "bold"), 
            bg=card_color, 
            fg=text_color
        )
        self.username_label.pack(anchor="w", pady=(0, 6))
        
        self.username_entry = tk.Entry(
            self.card, 
            font=("Inter", 11), 
            bg=bg_color, 
            fg=text_color, 
            bd=0, 
            insertbackground=text_color, 
            width=30
        )
        self.username_entry.pack(ipady=10, pady=(0, 20))
        self.username_entry.insert(0, "admin")  # Pre-fill for demonstration ease

        # Password entry field
        self.password_label = tk.Label(
            self.card, 
            text="SECURITY PASSWORD", 
            font=("Outfit", 8, "bold"), 
            bg=card_color, 
            fg=text_color
        )
        self.password_label.pack(anchor="w", pady=(0, 6))
        
        self.password_entry = tk.Entry(
            self.card, 
            font=("Inter", 11), 
            bg=bg_color, 
            fg=text_color, 
            show="•", 
            bd=0, 
            insertbackground=text_color, 
            width=30
        )
        self.password_entry.pack(ipady=10, pady=(0, 30))
        self.password_entry.bind("<Return>", lambda event: self.handle_login_attempt())

        # Error notification frame
        self.error_label = tk.Label(
            self.card, 
            text="", 
            font=("Inter", 9), 
            bg=card_color, 
            fg="#FF453A"
        )
        self.error_label.pack(pady=(0, 10))

        # Sign-in Action Button
        self.login_button = tk.Button(
            self.card,
            text="SECURE LOGIN",
            font=("Outfit", 11, "bold"),
            bg=accent_color,
            fg="#FFFFFF",
            activebackground="#0056b3",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            command=self.handle_login_attempt,
            cursor="hand2"
        )
        self.login_button.pack(fill="x", ipady=12)

    def handle_login_attempt(self):
        """
        Authenticates entered credentials against user profiles in SQLite.
        Monitors security locks by counting consecutive operational failures.
        """
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.config(text="Please fill in all security fields.")
            return

        if self.failed_attempts >= 5:
            self.error_label.config(text="System locked due to excessive failed attempts.")
            write_system_log("SECURITY_ALERT", f"Brute-force security lock triggered on username: '{username}'.", 1)
            messagebox.showerror("Security Lockout", "This interface has been suspended for security reasons.")
            return

        try:
            # Hash entered password
            hasher = hashlib.sha256()
            hasher.update(password.encode("utf-8"))
            computed_hash = hasher.hexdigest()

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, username, password_hash, role
                    FROM users
                    WHERE username = ?
                    """,
                    (username,)
                )
                user_row = cursor.fetchone()

            if user_row:
                db_id = user_row["id"]
                db_hash = user_row["password_hash"]
                db_role = user_row["role"]

                if computed_hash == db_hash:
                    # Access granted
                    self.failed_attempts = 0
                    self.error_label.config(text="")
                    
                    # Establish context session
                    SessionManager.start_session(db_id, username, db_role)
                    
                    # Destroy authentication container and trigger main panel callback
                    self.destroy()
                    self.login_success_callback()
                else:
                    self.register_failed_login(username)
            else:
                self.register_failed_login(username)

        except Exception as auth_err:
            print("Security login operation failed: %s", str(auth_err))
            self.error_label.config(text="Authentication failure: Database unreachable.")

    def register_failed_login(self, username):
        """
        Increments failed attempt counts and updates notifications appropriately.
        """
        self.failed_attempts += 1
        remaining_chances = 5 - self.failed_attempts
        self.error_label.config(text=f"Invalid username or password. ({remaining_chances} tries left)")
        
        # Log unauthorized login attempts
        write_system_log("LOGIN_FAILED", f"Failed login attempt for user '{username}'. Failure index: {self.failed_attempts}", 1)
        
        # Flash password field empty
        self.password_entry.delete(0, tk.END)
