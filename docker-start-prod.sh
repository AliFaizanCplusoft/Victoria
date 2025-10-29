#!/bin/bash
# Victoria Project - Production Docker Startup Script

echo "Starting Victoria Project in Production Mode..."

# Create necessary directories
mkdir -p /app/logs /app/output/reports /app/temp/uploads /app/temp/processing

# Set proper permissions
chmod 755 /app/logs /app/output /app/temp 2>/dev/null || true

# Determine service type from environment
SERVICE_NAME=${SERVICE_NAME:-api}

if [ "$SERVICE_NAME" = "dashboard" ]; then
    echo "Starting Streamlit dashboard on port 8501..."
    python main.py streamlit
else
    echo "Starting FastAPI server on port 8000..."
    uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --log-level info
fi




