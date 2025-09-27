import os
import sys
from alembic import command
from alembic.config import Config
from app.core.config import settings

def run_migrations():
    """Run Alembic migrations automatically"""
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate to the backend directory where alembic.ini is located
    backend_dir = os.path.dirname(os.path.dirname(current_dir))
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")
    
    # Create Alembic config
    alembic_cfg = Config(alembic_ini_path)
    
    # Set the script location
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "migrations"))
    
    # Override the database URL with the one from settings
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    try:
        # Run the migrations
        command.upgrade(alembic_cfg, "head")
        print("Alembic migrations completed successfully!")
        return True
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    if not success:
        sys.exit(1)