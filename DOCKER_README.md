# Victoria Project - Docker Deployment Guide

## 🐳 Docker Setup for Victoria Assessment API

This guide shows you how to run the Victoria Assessment API using Docker for both local development and production deployment.

## 📋 Prerequisites

- Docker and Docker Compose installed
- OpenAI API key
- At least 2GB RAM available for the container

## 🚀 Quick Start

### 1. Configure Environment Variables

Copy the environment template and add your OpenAI API key:

```bash
cp docker.env .env
# Edit .env and add your actual OpenAI API key
```

Or set environment variables directly:

```bash
export OPENAI_API_KEY="your-actual-openai-key-here"
```

### 2. Build and Run the API

```bash
# Build the Docker image
docker-compose build

# Start the API service
docker-compose up -d

# View logs
docker-compose logs -f api
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Test report generation
curl -X POST "http://localhost:8000/api/v1/generate-report" \
  -F "responses_file=@responses.csv" \
  -F "person_index=0" \
  --output victoria_report.html
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |
| `OPENAI_MAX_TOKENS` | `2000` | Maximum tokens per request |
| `OPENAI_TEMPERATURE` | `0.7` | Response creativity (0-1) |
| `API_HOST` | `0.0.0.0` | API host address |
| `API_PORT` | `8000` | API port |

### Volume Mounts

- `./output:/app/output` - Generated reports
- `./logs:/app/logs` - Application logs
- `./temp:/app/temp` - Temporary files
- `./responses.csv:/app/responses.csv:ro` - Sample data (read-only)
- `./trait.txt:/app/trait.txt:ro` - Trait definitions (read-only)
- `./templates:/app/templates:ro` - HTML templates (read-only)

## 🏗️ Production Deployment

### 1. Enable Nginx Reverse Proxy

```bash
# Start with Nginx for production
docker-compose --profile production up -d
```

This will:
- Run the API on port 8000 (internal)
- Expose it through Nginx on port 80
- Provide load balancing and SSL termination

### 2. Environment-Specific Configuration

Create production environment file:

```bash
# production.env
OPENAI_API_KEY=your-production-key
OPENAI_MODEL=gpt-4o
LOG_LEVEL=WARNING
```

Run with production config:

```bash
docker-compose --env-file production.env up -d
```

## 📊 Monitoring

### Health Checks

The API includes built-in health checks:

```bash
# Check container health
docker-compose ps

# Manual health check
curl http://localhost:8000/health
```

### Logs

```bash
# View all logs
docker-compose logs

# Follow API logs
docker-compose logs -f api

# View last 100 lines
docker-compose logs --tail=100 api
```

## 🔄 Development Workflow

### Rebuild After Changes

```bash
# Rebuild and restart
docker-compose up --build -d

# Force rebuild without cache
docker-compose build --no-cache
```

### Debug Mode

```bash
# Run in foreground with debug logs
docker-compose up --build
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   netstat -tulpn | grep :8000
   
   # Kill the process or change port in docker-compose.yml
   ```

2. **OpenAI API Key Issues**
   ```bash
   # Check environment variables
   docker-compose exec api env | grep OPENAI
   ```

3. **Permission Issues**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER output logs temp
   ```

4. **Memory Issues**
   ```bash
   # Check container resource usage
   docker stats victoria-api
   ```

### Debug Container

```bash
# Access container shell
docker-compose exec api bash

# Check Python path
docker-compose exec api python -c "import sys; print(sys.path)"

# Test API import
docker-compose exec api python -c "from app.api.main import app; print('API imported successfully')"
```

## 📈 Scaling

### Multiple API Instances

```bash
# Scale API service
docker-compose up --scale api=3 -d
```

### Resource Limits

Add to docker-compose.yml:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

## 🔒 Security

### Production Security Checklist

- [ ] Use strong OpenAI API key
- [ ] Enable HTTPS with Nginx
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Monitor API usage
- [ ] Set up log rotation

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/docs` | GET | API documentation |
| `/api/v1/generate-report` | POST | Generate assessment report |

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs api`
2. Verify environment variables
3. Ensure all required files are mounted
4. Check container health: `docker-compose ps`

For more help, check the main project README or create an issue in the repository.





