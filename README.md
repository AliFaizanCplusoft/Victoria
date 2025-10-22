# 🎯 Victoria Project - Psychometric Assessment Analysis System

A comprehensive system for processing raw survey data through advanced psychometric analysis (RaschPy) and creating interactive dashboards with professional reporting capabilities.

## ✅ Quick Start (3 Steps)

### 1. Install Dependencies
```bash
# Install all requirements
pip install -r requirements.txt

# Install RaschPy (for advanced analysis)
pip install git+https://github.com/MarkElliott999/RaschPy.git
```

### 2. Start the Dashboard
```bash
# Option A: Simple start
streamlit run streamlit_app.py

# Option B: Use startup script
./start_dashboard.sh

# Option C: Run API server
python run_api.py
```

### 3. Access & Upload Data
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- Upload your CSV file and start analyzing!

## 📊 What This System Does

### Core Pipeline
1. **Data Upload** - Handles raw CSV survey data with Likert scale responses
2. **Data Processing** - Converts responses to numeric format and validates quality
3. **Psychometric Analysis** - Runs RaschPy analysis for person abilities and item difficulties
4. **Clustering & Profiling** - K-means clustering to identify participant archetypes
5. **Visualization** - Interactive charts, heatmaps, and 3D cluster plots
6. **Report Generation** - Professional HTML/PDF reports for individuals and groups

### Key Features
- ✅ **RaschPy Integration** - Advanced psychometric modeling
- ✅ **Interactive Dashboard** - Streamlit-based web interface  
- ✅ **API Server** - FastAPI REST endpoints for programmatic access
- ✅ **ML Clustering** - Automatic trait clustering and archetype discovery
- ✅ **Multi-Format Reports** - HTML, PDF, CSV, JSON exports
- ✅ **Individual Profiles** - Detailed person-level assessments
- ✅ **Group Analytics** - Population-level insights and comparisons

## 📁 Expected Data Format

### Input CSV Structure
```csv
Please enter your prolific ID,EnergizedByPotential,EagertoPursue,PursuePerfection,...
6728f3d973b4504d88a81299,Often (66-90%),Always (91-100%),Sometimes (36-65%),...
56888951d7848e000c39a122,Sometimes (36-65%),Often (66-90%),Always (91-100%),...
```

**Requirements:**
- First column: Person/Assessment ID
- Remaining columns: Assessment items
- Responses: Likert scale text (e.g., "Often (66-90%)", "Sometimes (36-65%)")

### Output Format (RaschPy Compatible)
```csv
Measure,E1,E2,Persons,Assessment_Items
1.37,1,1,6728f3d973b4504d88a81299,EnergizedByPotential
1.81,1,2,6728f3d973b4504d88a81299,EagertoPursue
1.54,1,3,6728f3d973b4504d88a81299,PursuePerfection
```

## 🚀 Usage Options

### 1. Streamlit Dashboard
```bash
streamlit run streamlit_app.py
```
- Interactive web interface
- File upload and processing
- Real-time visualizations
- Export capabilities

### 2. API Server
```bash
python run_api.py --reload --port 8000
```
- REST API endpoints
- Programmatic access
- Batch processing
- Integration capabilities

### 3. Command Line Processing
```bash
python main.py --file survey_data.csv --output reports/
```
- Direct file processing
- Automated workflows
- Batch analysis

## 🎨 Dashboard Features

### Data Upload & Processing
- **Multi-format Support**: Raw CSV, Typeform exports, pre-processed data
- **Real-time Validation**: Live data quality checks
- **Processing Log**: Detailed transformation feedback
- **Error Handling**: Clear error messages and recovery options

### Psychometric Analysis
- **RaschPy Integration**: Advanced Rasch model analysis
- **Person Abilities**: Individual ability estimates with standard errors
- **Item Parameters**: Difficulty and fit statistics
- **Model Diagnostics**: Comprehensive fit assessments

### Visualization & Insights
- **Interactive Charts**: Plotly-based visualizations
- **3D Cluster Plots**: Trait clustering in 3D space
- **Person-Item Maps**: Ability vs difficulty mappings
- **Heatmaps**: Individual response patterns
- **Radar Charts**: Archetype comparisons

### Report Generation
- **Individual Profiles**: Detailed person-level reports
- **Group Summaries**: Population-level analytics
- **ML Dashboard**: Clustering and trait analysis
- **Export Options**: HTML, PDF, CSV, JSON formats

## 📊 Analysis Components

### Trait Clustering
- K-means clustering to identify participant archetypes
- Optimal cluster detection using silhouette analysis
- Archetype profiling (e.g., "High-Drive Innovators", "Collaborative Leaders")
- Interactive 3D visualization of cluster separation

### Individual Assessment
- Person ability estimates in logit scale
- Strengths vs development areas identification
- Response pattern analysis
- Personalized insights and recommendations

### Item Analysis
- Item difficulty parameters
- Discrimination indices
- Fit statistics (infit/outfit)
- Quality assessments and recommendations

## 🛠️ Project Structure

```
Victoria_Project/
├── app/                          # Application entry points
│   ├── api/                      # FastAPI application
│   └── streamlit/                # Streamlit UI application
├── victoria/                     # Core business logic package
│   ├── config/                   # Configuration management
│   ├── core/                     # Core domain models and services
│   ├── processing/               # Data processing pipeline
│   ├── scoring/                  # Psychometric scoring
│   ├── clustering/               # Trait clustering
│   ├── reporting/                # Report generation
│   └── utils/                    # Shared utilities
├── data/                         # Data files
├── templates/                    # HTML report templates
├── tests/                        # Test files
├── victoria_pipeline.py         # Main pipeline script
├── main.py                      # CLI processing tool
└── requirements.txt             # All dependencies
```

### Module Responsibilities

- **victoria.config**: Environment configuration, file path management, feature flags
- **victoria.core**: Domain models, core business interfaces, shared types
- **victoria.processing**: Data validation, RaschPy integration, data transformation
- **victoria.scoring**: Individual trait scoring, percentile calculations
- **victoria.clustering**: Trait correlation analysis, clustering algorithms, archetype mapping
- **victoria.reporting**: HTML report generation, PDF export, visualization creation
- **victoria.utils**: Common utilities, data helpers, logging setup

## 🔧 API Endpoints

### Assessment Processing
- `POST /api/v1/assess/upload` - Upload CSV data
- `POST /api/v1/assess/process` - Process uploaded data
- `GET /api/v1/assess/results/{id}` - Get analysis results

### Report Generation
- `POST /api/v1/reports/individual/{person_id}` - Generate individual report
- `POST /api/v1/reports/group` - Generate group summary
- `GET /api/v1/reports/download/{report_id}` - Download report

### System
- `GET /api/v1/health` - Health check
- `GET /docs` - Interactive API documentation

## 📝 Generated Outputs

### Individual Reports
- Personal ability estimates and standard errors
- Strengths and development areas identification
- Item-by-item response analysis
- Personalized insights and recommendations
- Professional HTML/PDF formatting

### Group Analytics
- Population statistics and distributions
- Cluster analysis and archetype identification
- Comparative analysis between groups
- Trend analysis and insights

### ML Dashboard
- Interactive trait distribution charts
- Cluster radar comparisons
- 3D scatter plots of participant clustering
- Individual trait heatmaps
- Archetype profiling and insights

## 🚨 Troubleshooting

### Dashboard Won't Start
```bash
# Try direct command
streamlit run streamlit_app.py --server.port 8501

# Check virtual environment
source .venv/bin/activate
pip install -r requirements.txt
```

### RaschPy Installation Issues
```bash
# Install from GitHub
pip install git+https://github.com/MarkElliott999/RaschPy.git

# Or fallback to basic analysis (system will adapt automatically)
```

### Data Upload Failures
- Ensure first column contains unique person/assessment IDs
- Check that Likert responses match expected format
- Verify CSV file encoding and structure
- Review terminal output for specific error messages

### API Server Issues
```bash
# Check dependencies
python run_api.py --check-deps

# Setup directories
python run_api.py --setup-only

# Run with detailed logging
python run_api.py --log-level DEBUG
```

## 📈 Technical Requirements

### System Requirements
- **Python**: 3.9 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space for dependencies and outputs
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)

### Key Dependencies
- **streamlit>=1.28.0** - Dashboard framework
- **fastapi>=0.104.0** - API server
- **pandas>=2.0.0** - Data processing
- **plotly>=5.17.0** - Interactive visualizations
- **scikit-learn>=1.3.0** - Machine learning
- **RaschPy** - Psychometric analysis (install separately)

## 📊 Sample Data

Test the system with included `sample_data.csv`:
- 32 participants with assessment IDs
- 146 assessment items with Likert responses
- Demonstrates full pipeline functionality
- Expected processing time: ~30 seconds

## 🎯 Success Indicators

When working correctly, you should see:
- ✅ "Data processed successfully!" message
- ✅ RaschPy analysis completion
- ✅ Interactive visualizations loading
- ✅ Generated reports in `output/` directory
- ✅ ML dashboard with clustering results
- ✅ Export options functioning

## 🚀 Deployment Options

### 🐳 Docker Deployment (Recommended)

#### Quick Start - Local Testing
```bash
# 1. Build the Docker image
docker build -t victoria-project .

# 2. Run both services with Docker Compose
docker-compose up -d

# Access:
# Dashboard: http://localhost:8501
# API: http://localhost:8000/docs
```

#### Production Docker Deployment
```bash
# Build for production
docker build -t victoria-project:production .

# Run with production profile (includes nginx)
docker-compose --profile production up -d
```

### 🚂 Railway Deployment (Cloud)

Railway automatically detects Docker and makes deployment simple:

#### Method 1: Railway CLI (Recommended)
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Create new project
railway new victoria-project

# 4. Deploy both services
railway up --service dashboard
railway add
railway up --service api
```

#### Method 2: GitHub Integration
1. Push to GitHub
2. Go to [railway.app](https://railway.app)
3. Click "Deploy from GitHub"
4. Select your Victoria Project repo
5. Create two services:
   - **Dashboard Service**: `SERVICE_TYPE=dashboard`
   - **API Service**: `SERVICE_TYPE=api`

### 🌐 Other Cloud Providers

#### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/victoria
gcloud run deploy victoria-dashboard --image gcr.io/PROJECT-ID/victoria --set-env-vars SERVICE_TYPE=dashboard
gcloud run deploy victoria-api --image gcr.io/PROJECT-ID/victoria --set-env-vars SERVICE_TYPE=api
```

#### AWS ECS Fargate
- Push to ECR
- Create task definitions for dashboard and API services
- Deploy using ECS Fargate with the same image, different commands

### 🔧 Service Configuration

| Variable | Dashboard | API | Description |
|----------|-----------|-----|-------------|
| `SERVICE_TYPE` | `dashboard` | `api` | Service identifier |
| `PORT` | `8501` | `8000` | Service port |
| `PYTHONPATH` | `/app` | `/app` | Python path |

**Commands:**
- **Dashboard**: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
- **API**: `python run_api.py --host 0.0.0.0 --port=$PORT`

## 📞 Support & Documentation

### Resources
- **API Documentation**: Visit `/docs` when server is running
- **Sample Data**: Use included files for testing
- **Error Logs**: Check `logs/` directory for detailed debugging
- **Processing Output**: Review `processed_output.txt` for data transformation results

### Common Issues
1. **Import Errors**: Ensure all requirements are installed
2. **RaschPy Failures**: System includes fallback analysis methods
3. **Memory Issues**: Close other applications, use smaller datasets for testing
4. **Port Conflicts**: Change port numbers in startup commands
5. **Docker Build Issues**: Clear cache with `docker system prune -a`
6. **Railway Deployment**: Check logs with `railway logs` and verify environment variables

## 🎉 Ready to Analyze!

Your Victoria Project system provides:
- **Professional psychometric analysis** with RaschPy integration
- **Modern web interface** for interactive exploration
- **Comprehensive reporting** in multiple formats
- **Advanced clustering** for participant profiling
- **API access** for programmatic integration

**Start with:** `streamlit run streamlit_app.py` and upload your assessment data!

---

**Victoria Project** - Transforming assessment data into actionable insights through advanced psychometric analysis and interactive visualization.