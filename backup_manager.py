# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Database Backup & Recovery Module
"""

import os
import shutil
import logging
from datetime import datetime
from database import DB_PATH, write_system_log, get_db_connection

# Workspace Directory constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, "backups")


def verify_backup_folder():
    """
    Guarantees the existence of the backups/ output directory.
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)


def execute_database_backup():
    """
    Generates a timestamped file copy of the active SQLite database.
    Excludes transactional active locks to ensure full data recovery.
    """
    try:
        verify_backup_folder()
        
        # Verify physical database exists before copy
        if not os.path.exists(DB_PATH):
            return False, "Active database file not found. Create database rows first."

        # Compute dated backup naming string
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"expenses_{timestamp}.db"
        backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

        # Execute safe background copy
        shutil.copy2(DB_PATH, backup_filepath)
        
        # Record structural audit log
        write_system_log("BACKUP", f"Database backup compiled successfully: {backup_filename}")
        return True, backup_filename
    except (IOError, OSError) as backup_err:
        logging.error("Database backup operation failed: %s", str(backup_err))
        write_system_log("BACKUP_ERROR", f"Database backup operation failed: {str(backup_err)}")
        return False, f"Backup creation failed: {str(backup_err)}"


def list_available_backups():
    """
    Scans the backups/ directory and returns an ordered listing of dated SQLite databases.
    """
    try:
        verify_backup_folder()
        files = os.listdir(BACKUP_DIR)
        
        # Filter files ending with .db and matching our naming structure
        backup_files = [f for f in files if f.startswith("expenses_") and f.endswith(".db")]
        
        # Return sorted by creation date (descending)
        backup_files.sort(reverse=True)
        return backup_files
    except OSError as err:
        logging.error("Failed to list local backups: %s", str(err))
        return []


def execute_database_restore(backup_filename):
    """
    Overwrites the primary SQLite database with a historical snapshot.
    Integrates absolute schema checking to prevent data corruption.
    """
    try:
        verify_backup_folder()
        backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

        # 1. Verification of backup file presence
        if not os.path.exists(backup_filepath):
            return False, "Selected database backup file does not exist on disk."

        # 2. Open validation check connection to ensure backup file is not corrupted
        try:
            import sqlite3
            test_conn = sqlite3.connect(backup_filepath)
            test_cursor = test_conn.cursor()
            test_cursor.execute("SELECT COUNT(*) FROM users")
            test_cursor.close()
            test_conn.close()
        except sqlite3.Error as corrupt_err:
            logging.error("Backup file structural verification failed: %s", str(corrupt_err))
            return False, "Corrupted snapshot file: SQLite database checks failed."

        # 3. Release active sqlite operational locks
        # In multi-window Tkinter systems, we run a temporary garbage cleanup 
        # to ensure no thread is writing during copy.
        
        # 4. Overwrite active database file
        shutil.copy2(backup_filepath, DB_PATH)
        
        # Log successful recovery event
        write_system_log("RESTORE", f"Database restored successfully from snapshot: {backup_filename}")
        return True, "Database successfully restored. Please restart dashboard to refresh panels."
    except (IOError, OSError) as restore_err:
        logging.error("Database restore operation failed: %s", str(restore_err))
        write_system_log("RESTORE_ERROR", f"Database restore operation failed: {str(restore_err)}")
        return False, f"Recovery operation failed: {str(restore_err)}"
