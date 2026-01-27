# Victoria Project - Entrepreneurial Psychometric Assessment System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## 🎯 Overview

**Victoria Project** (also known as **Vetria**) is a comprehensive psychometric assessment system designed to evaluate entrepreneurial traits and generate detailed personality reports. The system analyzes assessment responses, calculates trait scores using Rasch measurement theory, identifies entrepreneurial archetypes, and produces visually rich HTML reports with dynamic content generation.

### What It Does

1. **Processes Assessment Data**: Accepts CSV files containing psychometric assessment responses
2. **Calculates Trait Scores**: Uses Rasch analysis to compute 17 distinct personality traits
3. **Detects Archetypes**: Identifies entrepreneurial archetypes based on trait patterns
4. **Generates Reports**: Creates comprehensive HTML reports with:
   - Trait score visualizations (heatmaps, radar charts, gauges)
   - Archetype correlation analysis
   - Dynamic LLM-generated insights and explanations
   - Personalized recommendations

## ✨ Features

### Core Functionality
- ✅ **17 Trait Assessment**: Comprehensive evaluation across multiple personality dimensions
- ✅ **Rasch Measurement**: Psychometrically validated scoring methodology
- ✅ **Archetype Detection**: 5 distinct entrepreneurial archetypes
- ✅ **Dynamic Report Generation**: AI-powered content generation using OpenAI GPT models
- ✅ **Rich Visualizations**: Interactive charts and graphs using Plotly
- ✅ **Multi-Interface Support**: Both REST API and Streamlit dashboard

### Technical Features
- 🐳 **Docker Support**: Containerized deployment with Docker Compose
- 🔒 **Security**: Environment-based configuration, no hardcoded secrets
- 📊 **Data Processing**: Robust CSV parsing and data validation
- 🎨 **Customizable Templates**: Jinja2-based HTML report templates
- 📈 **Logging**: Comprehensive logging system for debugging and monitoring
- 🔄 **API-First**: RESTful API design for easy integration

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Victoria Project                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   FastAPI    │    │  Streamlit   │    │    Nginx     │  │
│  │   Server     │    │  Dashboard   │    │   Reverse    │  │
│  │   (Port 8000)│    │  (Port 8501) │    │    Proxy     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │          │
│         └────────────────────┼────────────────────┘          │
│                              │                               │
│                    ┌─────────▼─────────┐                    │
│                    │  Victoria Pipeline │                    │
│                    └─────────┬─────────┘                    │
│                              │                               │
│         ┌────────────────────┼────────────────────┐          │
│         │                    │                    │          │
│  ┌──────▼──────┐    ┌────────▼────────┐  ┌──────▼──────┐  │
│  │   Data      │    │   Trait         │  │  Archetype  │  │
│  │  Processor  │    │   Scorer        │  │  Detector   │  │
│  └─────────────┘    └─────────────────┘  └─────────────┘  │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Visualization│    │   Report     │    │   OpenAI     │  │
│  │   Engine     │    │  Generator   │    │   Client     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

- **`victoria/core/`**: Core business logic (data processing, archetype detection, visualization, report generation)
- **`victoria/scoring/`**: Trait scoring algorithms (Rasch analysis, fixed trait scoring)
- **`victoria/processing/`**: Data processing utilities (CSV parsing, response mapping)
- **`victoria/clustering/`**: Clustering and archetype mapping algorithms
- **`victoria/utils/`**: Utility functions (CSV helpers, logging, visualization helpers)
- **`app/api/`**: FastAPI REST endpoints
- **`app/streamlit/`**: Streamlit dashboard interface
- **`templates/html/`**: Jinja2 HTML report templates

## 📦 Prerequisites

### Required Software
- **Python**: 3.9 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 1.29+ (for multi-container orchestration)
- **Git**: For version control

### Required Services
- **OpenAI API Key**: For dynamic content generation (GPT-4o recommended)
- **Web Server**: Nginx (included in Docker setup)

### Python Dependencies
- FastAPI
- Streamlit
- Pandas
- NumPy
- Plotly
- Jinja2
- OpenAI
- python-dotenv
- Uvicorn

## 🚀 Installation

### Option 1: Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AliFaizanCplusoft/Victoria.git
   cd Victoria
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

5. **Verify installation**
   ```bash
   python -c "from victoria import __version__; print(f'Victoria {__version__}')"
   ```

### Option 2: Docker Setup (Recommended for Production)

1. **Clone the repository**
   ```bash
   git clone https://github.com/AliFaizanCplusoft/Victoria.git
   cd Victoria
   ```

2. **Configure environment**
   ```bash
   cp env.prod .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Build and start containers**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Verify services**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   curl http://localhost:8000/health
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DOCKER_ENV=false

# Logging
LOG_LEVEL=INFO

# Production Settings
PYTHONUNBUFFERED=1
PYTHONPATH=/app
```

### Configuration Files

- **`docker-compose.prod.yml`**: Docker Compose configuration for production
- **`nginx.prod.conf`**: Nginx reverse proxy configuration
- **`Dockerfile.prod`**: Production Docker image definition
- **`trait.txt`**: Trait definitions and descriptions (used in reports)

## 💻 Usage

### Command-Line Interface

Generate a report from a CSV file:

```bash
python victoria_pipeline.py <csv_file> <person_index>

# Example
python victoria_pipeline.py responses.csv 0
```

**Parameters:**
- `csv_file`: Path to CSV file containing assessment responses
- `person_index`: Index of the person to process (0-based)

**Output:**
- Generated HTML report saved to `output/reports/vetria_report_<name>_<timestamp>.html`

### FastAPI Server

Start the API server:

```bash
# Local development
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

# Or using the startup script
python app/api/main.py
```

The API will be available at `http://localhost:8000`

### Streamlit Dashboard

Start the Streamlit dashboard:

```bash
streamlit run app/streamlit/main.py
```

The dashboard will be available at `http://localhost:8501`

### Docker Deployment

Start all services:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Stop services:

```bash
docker-compose -f docker-compose.prod.yml down
```

View logs:

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

## 📡 API Documentation

### Base URL
- **Local**: `http://localhost:8000`
- **Production**: Configure via Nginx

### Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "vetria-api"
}
```

#### Generate Report from CSV File Upload
```http
POST /api/v1/generate-report
Content-Type: multipart/form-data
```

**Parameters:**
- `responses_file` (file): CSV file containing assessment responses
- `person_index` (int, optional): Index of person to process (default: 0)

**Response:**
- Returns HTML file as download

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/v1/generate-report" \
  -F "responses_file=@responses.csv" \
  -F "person_index=0"
```

#### Generate Report from CSV Content (JSON)
```http
POST /api/v1/generate-report-from-csv
Content-Type: application/json
```

**Request Body:**
```json
{
  "csv_content": "csv,content,here...",
  "person_index": 0
}
```

**Response:**
- Returns HTML file as download

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/v1/generate-report-from-csv" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_content": "First,Last,Email\nJohn,Doe,john@example.com",
    "person_index": 0
  }'
```

#### Generate Report (JSON Response)
```http
POST /api/v1/generate-report-from-csv-json
Content-Type: application/json
```

**Request Body:**
```json
{
  "csv_content": "csv,content,here...",
  "person_index": 0
}
```

**Response:**
```json
{
  "status": "success",
  "report_html": "<html>...</html>",
  "filename": "vetria_report_John_Doe_20260127_123456.html"
}
```

### Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📁 Project Structure

```
Victoria_Project/
├── app/                          # Application interfaces
│   ├── api/                      # FastAPI REST API
│   │   └── main.py              # API endpoints and routes
│   └── streamlit/               # Streamlit dashboard
│       └── main.py             # Streamlit application
│
├── victoria/                    # Core package
│   ├── core/                    # Core business logic
│   │   ├── archetype_detector.py    # Archetype detection
│   │   ├── data_processor.py       # Data processing
│   │   ├── report_generator.py      # Report generation
│   │   └── visualization_engine.py  # Chart generation
│   ├── scoring/                 # Scoring algorithms
│   │   └── fixed_trait_scorer.py   # Trait scoring
│   ├── processing/              # Data processing
│   │   ├── rasch_processor.py      # Rasch analysis
│   │   └── response_mapper.py      # Response mapping
│   ├── clustering/              # Clustering algorithms
│   ├── utils/                   # Utility functions
│   └── config/                  # Configuration
│
├── templates/                   # HTML templates
│   └── html/
│       └── vertria_comprehensive_report.html
│
├── output/                      # Generated reports (gitignored)
│   └── reports/
│
├── data/                        # Sample data (gitignored)
│
├── logs/                        # Log files (gitignored)
│
├── victoria_pipeline.py         # Main CLI script
├── docker-compose.prod.yml      # Docker Compose config
├── Dockerfile.prod              # Production Dockerfile
├── nginx.prod.conf              # Nginx configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🔧 Development

### Setting Up Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/Victoria.git
   cd Victoria
   ```

2. **Create a development branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8 mypy  # Optional: testing and linting
   ```

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where possible
- Document functions and classes with docstrings
- Keep functions focused and modular

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=victoria tests/
```

### Making Changes

1. Make your changes in a feature branch
2. Test your changes locally
3. Update documentation if needed
4. Commit with descriptive messages
5. Push and create a pull request

## 🚢 Deployment

### Production Deployment with Docker

1. **Prepare server**
   ```bash
   # Install Docker and Docker Compose
   sudo apt-get update
   sudo apt-get install docker.io docker-compose
   ```

2. **Transfer code to server**
   ```bash
   scp -r victoria/ root@your-server:/opt/victoria-project/
   scp docker-compose.prod.yml Dockerfile.prod nginx.prod.conf root@your-server:/opt/victoria-project/
   ```

3. **SSH into server**
   ```bash
   ssh root@your-server
   cd /opt/victoria-project
   ```

4. **Configure environment**
   ```bash
   cp env.prod .env
   nano .env  # Add your OPENAI_API_KEY
   ```

5. **Build and start**
   ```bash
   docker-compose -f docker-compose.prod.yml build --no-cache
   docker-compose -f docker-compose.prod.yml up -d
   ```

6. **Verify deployment**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   curl http://localhost:8000/health
   ```

### Updating Deployment

1. **Pull latest code**
   ```bash
   git pull origin main
   ```

2. **Rebuild containers**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml build --no-cache
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Environment-Specific Configuration

- **Development**: Use `.env` file with local settings
- **Production**: Use `env.prod` template, ensure secrets are secure
- **Docker**: Environment variables passed via `docker-compose.prod.yml`

## 🐛 Troubleshooting

### Common Issues

#### API Key Not Found
**Problem**: `OPENAI_API_KEY not found in environment variables`

**Solution**:
- Ensure `.env` file exists in project root
- Verify `OPENAI_API_KEY` is set correctly
- Restart the application after changing `.env`

#### Port Already in Use
**Problem**: `Address already in use` error

**Solution**:
```bash
# Find process using port
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process or change port in .env
```

#### Docker Build Fails
**Problem**: Docker build errors

**Solution**:
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose -f docker-compose.prod.yml build --no-cache
```

#### CSV Parsing Errors
**Problem**: `Failed to parse CSV` or `out-of-bounds` errors

**Solution**:
- Verify CSV format matches expected structure
- Check `person_index` is within valid range
- Ensure CSV encoding is UTF-8

#### Report Generation Fails
**Problem**: Report not generated or incomplete

**Solution**:
- Check logs: `logs/victoria_pipeline.log`
- Verify OpenAI API key is valid and has quota
- Ensure all required data files exist (`trait.txt`, templates)

### Logging

Logs are stored in:
- **Application logs**: `logs/victoria_pipeline.log`
- **API logs**: `logs/api.log` or `app/api/logs/`
- **Docker logs**: `docker-compose -f docker-compose.prod.yml logs`

### Getting Help

1. Check the logs for error messages
2. Review the [API documentation](#api-documentation)
3. Verify environment configuration
4. Check GitHub issues for similar problems

## 📊 Trait Definitions

The system evaluates 17 distinct personality traits:

1. **Accountability** - Taking responsibility for outcomes
2. **Adaptability** - Flexibility in changing circumstances
3. **Conflict Resolution** - Managing disagreements constructively
4. **Critical Thinking** - Analytical problem-solving
5. **Drive and Ambition** - Motivation and goal orientation
6. **Decision-Making** - Making choices effectively
7. **Emotional Intelligence** - Understanding and managing emotions
8. **Approach to Failure** - Learning from setbacks
9. **Social Orientation** - Extroversion/Introversion preference
10. **Innovation Orientation** - Creative thinking and ideation
11. **Negotiation** - Reaching mutually beneficial agreements
12. **Problem-Solving** - Systematic solution finding
13. **Relationship-Building** - Building meaningful connections
14. **Resilience and Grit** - Perseverance through challenges
15. **Risk-Taking** - Comfort with calculated risks
16. **Servant Leadership** - Leading by serving others
17. **Team Building** - Creating effective teams

## 🎭 Archetypes

The system identifies 5 entrepreneurial archetypes:

1. **Strategic Innovation** - Calculated, strategic innovative efforts
2. **Resilient Leadership** - Leading with empathy and building cohesive teams
3. **Collaborative Responsibility** - Focus on team growth and accountability
4. **Ambitious Drive** - High motivation and perseverance
5. **Adaptive Intelligence** - Flexibility and learning orientation

## 📝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines

- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Follow the existing code style
- Ensure all tests pass before submitting

## 📄 License

This project is proprietary software. All rights reserved.

## 👥 Authors

- **Development Team** - Initial work and ongoing maintenance

## 🙏 Acknowledgments

- OpenAI for GPT API
- Plotly for visualization capabilities
- FastAPI and Streamlit communities
- All contributors and users

## 📞 Contact

For questions, issues, or support:
- **GitHub Issues**: [Create an issue](https://github.com/AliFaizanCplusoft/Victoria/issues)
- **Repository**: [Victoria Project](https://github.com/AliFaizanCplusoft/Victoria)

---

**Last Updated**: January 2026  
**Version**: 2.0.0
