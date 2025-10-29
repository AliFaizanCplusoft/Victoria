#!/bin/bash

# Victoria Project - Production Deployment Script
# Run this script on your Digital Ocean server

set -e

echo "🚀 Starting Victoria Project Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create application directory
APP_DIR="/opt/victoria-project"
print_status "Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs output/reports temp/uploads temp/processing ssl

# Set up environment file
if [ ! -f .env ]; then
    print_status "Creating environment file..."
    cat > .env << EOF
# Victoria Project - Production Environment Variables
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
API_HOST=0.0.0.0
API_PORT=8000
DOCKER_ENV=true
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
PYTHONPATH=/app
EOF
    print_warning "Please edit .env file and add your OpenAI API key!"
fi

# Set up firewall
print_status "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Create systemd service for auto-start
print_status "Creating systemd service..."
cat > /etc/systemd/system/victoria-project.service << EOF
[Unit]
Description=Victoria Project
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl daemon-reload
systemctl enable victoria-project.service

print_status "Deployment setup completed!"
print_warning "Next steps:"
echo "1. Copy your project files to $APP_DIR"
echo "2. Edit .env file and add your OpenAI API key"
echo "3. Run: docker-compose -f docker-compose.prod.yml up -d"
echo "4. Or start the service: systemctl start victoria-project"

print_status "🎉 Victoria Project is ready for deployment!"




