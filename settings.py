# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - System Configuration Persister
"""

import os
import json
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, "database", "settings.json")

# Default application preferences
DEFAULT_SETTINGS = {
    "theme": "Dark",
    "currency": "$",
    "export_folder": os.path.join(BASE_DIR, "exports"),
    "default_monthly_budget": 5000.0,
    "default_warning_limit": 4500.0
}


def load_user_settings():
    """
    Reads the configuration file from disk. If the file is missing or corrupted,
    it regenerates the default setting structures and returns them safely.
    """
    if not os.path.exists(SETTINGS_PATH):
        save_user_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as settings_file:
            loaded_data = json.load(settings_file)
            
            # Ensuring all default keys are present in loaded settings
            restored_settings = DEFAULT_SETTINGS.copy()
            for key, val in loaded_data.items():
                restored_settings[key] = val
            return restored_settings
    except (json.JSONDecodeError, IOError) as read_error:
        logging.error("Failed to parse settings JSON. Reverting to default configuration state: %s", str(read_error))
        save_user_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()


def save_user_settings(settings_dict):
    """
    Saves the user preferences dictionary back to the local settings JSON database.
    """
    try:
        # Guarantee parent folder existence
        parent_dir = os.path.dirname(SETTINGS_PATH)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
            
        with open(SETTINGS_PATH, "w", encoding="utf-8") as settings_file:
            json.dump(settings_dict, settings_file, indent=4)
        return True
    except IOError as write_error:
        logging.error("Settings storage operation failed: %s", str(write_error))
        return False
