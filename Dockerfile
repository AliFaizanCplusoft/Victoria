# Victoria Project - API-Focused Docker Image
# Optimized for FastAPI server with psychometric assessment pipeline
FROM python:3.9-slim

LABEL maintainer="Victoria Project"
LABEL description="Psychometric Assessment Analysis API"

# Set working directory
WORKDIR /app

# Install system dependencies required for psychometric libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Note: RaschPy functionality is implemented as a custom processor
# No external RaschPy library installation needed

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x docker-start.sh

# Create necessary directories
RUN mkdir -p logs output/reports temp/uploads temp/processing

# Set environment variables

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose API port
EXPOSE 8000

# Health check for API
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run the startup script
CMD ["./docker-start.sh"]