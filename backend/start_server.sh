#!/bin/bash

echo "Starting EduRPG Backend Server..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv_unix" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv_unix
fi

# Activate virtual environment
source venv_unix/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements-dev.txt

# Initialize database if needed
if [ ! -f "edurpg.db" ]; then
    echo "Initializing database..."
    python init_db.py
fi

# Start the server
echo "Starting server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000