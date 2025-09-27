#!/usr/bin/env python3
"""
Standalone script to run Alembic migrations
"""

import sys
import os

# Add the backend directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.run_migrations import run_migrations

if __name__ == "__main__":
    print("Running Alembic migrations...")
    success = run_migrations()
    if success:
        print("Migrations completed successfully!")
    else:
        print("Migrations failed!")
        sys.exit(1)