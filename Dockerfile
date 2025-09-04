# Victoria Project - Multi-Service Docker Image
# Supports both Streamlit Dashboard and FastAPI Server
FROM python:3.9-slim

LABEL maintainer="Victoria Project"
LABEL description="Psychometric Assessment Analysis System"

# Set working directory
WORKDIR /app

# Install system dependencies required for psychometric libraries and PDF generation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    wkhtmltopdf \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install RaschPy from GitHub (psychometric analysis)
# Note: RaschPy repo doesn't have proper packaging, installing manually
RUN git clone https://github.com/MarkElliott999/RaschPy.git /tmp/raschpy && \
    cp -r /tmp/raschpy/RaschPy /usr/local/lib/python3.9/site-packages/raschpy && \
    rm -rf /tmp/raschpy

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x startup.sh

# Create necessary directories
RUN mkdir -p logs output temp/uploads temp/processing

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose ports for both services
EXPOSE 8501 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command (can be overridden)
CMD ["bash", "-c", "mkdir -p /app/data_writable && chmod 777 /app/data_writable && cp /app/data/*.csv /app/data_writable/ 2>/dev/null || true && cp /app/data/*.txt /app/data_writable/ 2>/dev/null || true && streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false"]