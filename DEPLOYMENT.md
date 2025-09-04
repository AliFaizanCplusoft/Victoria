# 🚀 Victoria Project - Deployment Guide

## 🐳 Docker Deployment (Recommended)

### Quick Start - Local Testing
```bash
# 1. Build the Docker image
docker build -t victoria-project .

# 2. Run both services with Docker Compose
docker-compose up -d

# Access:
# Dashboard: http://localhost:8501
# API: http://localhost:8000/docs
# Nginx (if enabled): http://localhost:80
```

### Production Docker Deployment
```bash
# Build for production
docker build -t victoria-project:production .

# Run with production profile (includes nginx)
docker-compose --profile production up -d

# Or deploy to Docker registry
docker tag victoria-project:production your-registry/victoria:latest
docker push your-registry/victoria:latest
```

## 🚂 Railway Deployment (Cloud)

Railway automatically detects Docker and makes deployment simple:

### Method 1: Railway CLI (Recommended)
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Create new project
railway new victoria-project

# 4. Deploy both services
# Deploy Dashboard
railway up --service dashboard

# Deploy API (create second service)
railway add
railway up --service api

# 5. Set environment variables in Railway dashboard
# Dashboard service: SERVICE_TYPE=dashboard
# API service: SERVICE_TYPE=api
```

### Method 2: GitHub Integration
1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Railway"
   git push origin main
   ```

2. **Connect to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Deploy from GitHub"
   - Select your Victoria Project repo
   - Railway will auto-detect Dockerfile and deploy

3. **Create Two Services**
   - **Dashboard Service**: 
     - Command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
     - Environment: `SERVICE_TYPE=dashboard`
   - **API Service**:
     - Command: `python run_api.py --host 0.0.0.0 --port=$PORT`
     - Environment: `SERVICE_TYPE=api`

## 🌐 Other Cloud Providers with Docker

### Google Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/victoria

# Deploy Dashboard
gcloud run deploy victoria-dashboard \
  --image gcr.io/PROJECT-ID/victoria \
  --set-env-vars SERVICE_TYPE=dashboard \
  --port 8501

# Deploy API
gcloud run deploy victoria-api \
  --image gcr.io/PROJECT-ID/victoria \
  --set-env-vars SERVICE_TYPE=api \
  --port 8000
```

### AWS ECS Fargate
```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin ECR-URI
docker tag victoria-project:latest ECR-URI/victoria:latest
docker push ECR-URI/victoria:latest

# Create task definitions for dashboard and API services
# Deploy using ECS Fargate with the same image, different commands
```

### Azure Container Instances
```bash
# Push to Azure Container Registry
az acr build --registry myregistry --image victoria:latest .

# Deploy Dashboard
az container create \
  --resource-group myResourceGroup \
  --name victoria-dashboard \
  --image myregistry.azurecr.io/victoria:latest \
  --ports 8501 \
  --environment-variables SERVICE_TYPE=dashboard

# Deploy API
az container create \
  --resource-group myResourceGroup \
  --name victoria-api \
  --image myregistry.azurecr.io/victoria:latest \
  --ports 8000 \
  --environment-variables SERVICE_TYPE=api
```

## 🎯 Service Configuration

### Environment Variables
Both services use the same Docker image but different configurations:

| Variable | Dashboard | API | Description |
|----------|-----------|-----|-------------|
| `SERVICE_TYPE` | `dashboard` | `api` | Service identifier |
| `PORT` | `8501` | `8000` | Service port |
| `PYTHONPATH` | `/app` | `/app` | Python path |

### Commands
- **Dashboard**: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
- **API**: `python run_api.py --host 0.0.0.0 --port=$PORT`

## 🔧 Local Development

### Development with Docker
```bash
# Start development environment
docker-compose up

# Rebuild after code changes
docker-compose up --build

# View logs
docker-compose logs -f dashboard
docker-compose logs -f api
```

### Development without Docker
```bash
# Terminal 1 - Dashboard
streamlit run streamlit_app.py

# Terminal 2 - API
python run_api.py
```

## 🚨 Troubleshooting

### Docker Build Issues
```bash
# Clear Docker cache
docker system prune -a

# Rebuild with no cache
docker build --no-cache -t victoria-project .
```

### Railway Deployment Issues
1. **Check Railway logs**: `railway logs`
2. **Verify environment variables** in Railway dashboard
3. **Ensure Dockerfile is in root directory**
4. **Check that ports match Railway's `$PORT` variable**

### Common Issues
| Issue | Solution |
|-------|----------|
| RaschPy installation fails | Docker handles this automatically |
| Port conflicts | Use `$PORT` environment variable |
| File permissions | Docker runs as non-root user |
| Memory issues | Increase container memory limits |

## 📊 Production Considerations

### Scaling
```yaml
# docker-compose.override.yml
services:
  dashboard:
    deploy:
      replicas: 3
  api:
    deploy:
      replicas: 2
```

### Monitoring
- **Health checks**: Built into Docker and Railway configs
- **Logs**: Centralized logging via Docker/Railway
- **Metrics**: Use Railway metrics or cloud provider monitoring

### Security
- **Non-root user**: Docker runs as `appuser`
- **Environment variables**: Store secrets in Railway/cloud provider
- **HTTPS**: Automatic with Railway and cloud providers

## 🎉 Quick Deploy Summary

**Fastest deployment (5 minutes):**
1. Push code to GitHub
2. Connect to Railway
3. Deploy → Two services automatically created
4. Access your live application!

**Docker benefits:**
- ✅ Consistent environment everywhere
- ✅ No dependency installation issues  
- ✅ Easy scaling and monitoring
- ✅ Works with any cloud provider
- ✅ Same image for dashboard and API

Choose Railway for simplest cloud deployment or use Docker with your preferred cloud provider for more control!