# -*- coding: utf-8 -*-
"""
NeuraSpend Vercel Serverless Web Handler Entrypoint
Academic Final Year Project - Cloud Deployment Adapter
"""

import os
import sys

# 1. Add the parent directory (project root) to sys.path
# This ensures that serverless execution can import all workspace files properly.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 2. Force mark Vercel environment flags to prevent local write errors
os.environ["VERCEL"] = "1"

# 3. Import and initialize database structures in /tmp
try:
    import database
    print("[Vercel Entrypoint] Running directory initialization...")
    database.initialize_directories()
    
    print("[Vercel Entrypoint] Compiling database tables and seeding demo data...")
    database.initialize_database()
    print("[Vercel Entrypoint] Database configured and pre-seeded successfully in /tmp.")
except Exception as db_init_err:
    print(f"[Vercel Entrypoint ERROR] Database configuration failed: {str(db_init_err)}")

# 4. Import the principal Flask app instance from main.py
try:
    from main import app
    print("[Vercel Entrypoint] Flask application loaded successfully.")
except Exception as app_import_err:
    print(f"[Vercel Entrypoint ERROR] Flask app import failed: {str(app_import_err)}")
    raise app_import_err

# Expose 'app' as the serverless callable for WSGI runtime
# Vercel's @vercel/python builder looks for the 'app' or 'application' variable.
application = app
