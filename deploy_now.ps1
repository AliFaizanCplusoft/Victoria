# Deploy updated main.py to server
Write-Host "Deploying updated main.py to server..." -ForegroundColor Green

$server = "root@104.248.210.137"
$localFile = "app/api/main.py"
$remoteFile = "/opt/victoria-project/app/api/main.py"

# Copy file to server
Write-Host "Copying file to server..." -ForegroundColor Yellow
scp $localFile ${server}:${remoteFile}

if ($LASTEXITCODE -eq 0) {
    Write-Host "File copied successfully!" -ForegroundColor Green
    
    # Rebuild Docker
    Write-Host "Rebuilding Docker..." -ForegroundColor Yellow
    ssh $server "cd /opt/victoria-project && docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d --build api"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Deployment successful!" -ForegroundColor Green
        Write-Host "Checking logs..." -ForegroundColor Yellow
        ssh $server "cd /opt/victoria-project && docker-compose -f docker-compose.prod.yml logs --tail=50 api"
    } else {
        Write-Host "Docker rebuild failed" -ForegroundColor Red
    }
} else {
    Write-Host "File copy failed" -ForegroundColor Red
}


