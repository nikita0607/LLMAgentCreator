@echo off
REM Script to run Alembic migrations

REM Navigate to the backend directory
cd /d "%~dp0"

REM Run migrations
alembic upgrade head

echo Migrations completed!
pause