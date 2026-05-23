# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Breathtaking System Style & Theme Engine
"""

import tkinter as tk
from tkinter import ttk
from settings import load_user_settings

#Curated corporate aesthetic palettes (Vibrant, high-contrast, premium layouts)
THEME_PALETTES = {
    "Dark": {
        "bg_main": "#0F0F16",          # Midnight obsidian black
        "bg_card": "#181824",          # Deep violet-blue elevated card panels
        "bg_sidebar": "#09090D",       # Dark carbon side navigation base
        "bg_active": "#242436",        # Slate carbon select highlights
        "fg_title": "#0A84FF",         # Electric neon blue titles
        "fg_body": "#F2F2F7",          # Crisp slate white text
        "fg_muted": "#8E8E93",         # Modern low-contrast grey text
        "primary": "#0A84FF",          # Bright energetic brand action blue
        "success": "#30D158",          # Compliant state indicator green
        "warning": "#FFD60A",          # Vigilant boundary alert orange-yellow
        "danger": "#FF453A",           # Violation alert crimson red
        "border": "#242433"            # Soft border lines
    },
    "Light": {
        "bg_main": "#F4F6F9",          # Modern soft light grey-blue
        "bg_card": "#FFFFFF",          # Flat white cards
        "bg_sidebar": "#E5E9F0",       # Clean steel-slate blue
        "bg_active": "#D8DEE9",        # Steel focus selects
        "fg_title": "#007AFF",         # Vibrant royal blue headings
        "fg_body": "#2E3440",          # Dark charcoal text
        "fg_muted": "#8E8E93",         # Carbon muted comments
        "primary": "#007AFF",          # Deep royal blue buttons
        "success": "#34C759",          # Verified transaction marker green
        "warning": "#FFCC00",          # Cautious budget zone orange-yellow
        "danger": "#FF3B30",           # Critical threshold alert red
        "border": "#E5E9F0"            # Soft steel grid separators
    }
}


def get_current_theme():
    """
    Looks up and retrieves the active user theme preference from the setting persister.
    """
    settings = load_user_settings()
    theme_name = settings.get("theme", "Dark")
    if theme_name not in THEME_PALETTES:
        theme_name = "Dark"
    return theme_name, THEME_PALETTES[theme_name]


def apply_theme_styles(root=None):
    """
    Configures the global Ttk style manager based on the active visual theme.
    Establishes flat cards, beautiful rounded styles, custom lists, and button pads.
    """
    theme_name, colors = get_current_theme()
    style = ttk.Style(root)
    
    # Apply standard theme shell reset
    style.theme_use("clam")

    # Font hierarchies
    title_font = ("Outfit", 12, "bold")
    body_font = ("Inter", 10)
    button_font = ("Outfit", 10, "bold")

    # Global Style definitions
    style.configure(".",
                    background=colors["bg_main"],
                    foreground=colors["fg_body"],
                    font=body_font)

    # Sidebar style settings
    style.configure("Sidebar.TFrame",
                    background=colors["bg_sidebar"],
                    borderwidth=0)
    
    style.configure("Sidebar.TLabel",
                    background=colors["bg_sidebar"],
                    foreground=colors["fg_title"],
                    font=("Outfit", 15, "bold"))

    style.configure("Sidebar.TButton",
                    background=colors["bg_sidebar"],
                    foreground=colors["fg_body"],
                    font=button_font,
                    borderwidth=0,
                    relief="flat",
                    anchor="w",
                    padding=(20, 12))
    style.map("Sidebar.TButton",
              background=[("active", colors["bg_active"]), ("selected", colors["primary"])],
              foreground=[("active", colors["fg_body"]), ("selected", "#FFFFFF")])

    # TopBar style settings
    style.configure("TopBar.TFrame",
                    background=colors["bg_card"],
                    relief="solid",
                    borderwidth=0)
    
    style.configure("TopBar.TLabel",
                    background=colors["bg_card"],
                    foreground=colors["fg_body"],
                    font=body_font)

    # Dynamic Card layout
    style.configure("Card.TFrame",
                    background=colors["bg_card"],
                    relief="flat",
                    borderwidth=0)

    # Typography classes
    style.configure("CardTitle.TLabel",
                    background=colors["bg_card"],
                    foreground=colors["fg_title"],
                    font=title_font)
    
    style.configure("CardBody.TLabel",
                    background=colors["bg_card"],
                    foreground=colors["fg_body"],
                    font=body_font)

    style.configure("CardMuted.TLabel",
                    background=colors["bg_card"],
                    foreground=colors["fg_muted"],
                    font=("Inter", 9))

    # Corporate Action Buttons
    style.configure("Primary.TButton",
                    background=colors["primary"],
                    foreground="#FFFFFF",
                    font=button_font,
                    borderwidth=0,
                    relief="flat",
                    padding=(15, 8))
    style.map("Primary.TButton",
              background=[("active", colors["bg_active"])])

    style.configure("Secondary.TButton",
                    background=colors["bg_active"],
                    foreground=colors["fg_body"],
                    font=button_font,
                    borderwidth=0,
                    relief="flat",
                    padding=(15, 8))
    style.map("Secondary.TButton",
              background=[("active", colors["bg_main"])])
              
    style.configure("Danger.TButton",
                    background=colors["danger"],
                    foreground="#FFFFFF",
                    font=button_font,
                    borderwidth=0,
                    relief="flat",
                    padding=(15, 8))
    style.map("Danger.TButton",
              background=[("active", colors["bg_active"])])

    # Dynamic inputs
    style.configure("TEntry",
                    fieldbackground=colors["bg_main"],
                    foreground=colors["fg_body"],
                    insertcolor=colors["fg_body"],
                    bordercolor=colors["border"],
                    lightcolor=colors["border"],
                    darkcolor=colors["border"],
                    font=body_font)
                    
    style.configure("TCombobox",
                    fieldbackground=colors["bg_main"],
                    foreground=colors["fg_body"],
                    background=colors["bg_card"],
                    font=body_font)

    # Dynamic ledger tables (Treeview)
    style.configure("Treeview",
                    background=colors["bg_card"],
                    fieldbackground=colors["bg_card"],
                    foreground=colors["fg_body"],
                    rowheight=32,
                    font=body_font)
    
    style.configure("Treeview.Heading",
                    background=colors["bg_active"],
                    foreground=colors["fg_title"],
                    font=button_font,
                    padding=(8, 8))
    
    style.map("Treeview",
              background=[("selected", colors["primary"])],
              foreground=[("selected", "#FFFFFF")])

    # Budget alert status bands
    style.configure("StatusGreen.TFrame", background=colors["success"])
    style.configure("StatusYellow.TFrame", background=colors["warning"])
    style.configure("StatusRed.TFrame", background=colors["danger"])
    
    style.configure("StatusGreen.TLabel", background=colors["success"], foreground="#FFFFFF", font=button_font)
    style.configure("StatusYellow.TLabel", background=colors["warning"], foreground="#09090D", font=button_font)
    style.configure("StatusRed.TLabel", background=colors["danger"], foreground="#FFFFFF", font=button_font)

    return colors
