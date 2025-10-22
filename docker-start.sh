#!/bin/bash
# Victoria Project - Docker Startup Script

echo "Starting Victoria Assessment API..."

# Create necessary directories
mkdir -p /app/logs /app/output/reports /app/temp/uploads /app/temp/processing

# Set proper permissions (skip if mounted volumes don't allow it)
chmod 755 /app/logs /app/output /app/temp 2>/dev/null || true

# Start the API server
echo "Starting FastAPI server on port 8000..."
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --log-level info
