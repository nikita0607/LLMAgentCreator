#!/bin/bash
# Script to run Alembic migrations

# Navigate to the backend directory
cd "$(dirname "$0")"

# Run migrations
alembic upgrade head

echo "Migrations completed!"