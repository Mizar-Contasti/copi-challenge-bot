# Reset and Run Development Server
# PowerShell script to clean up Docker and start fresh development environment

Write-Host "Cleaning up Docker environment..." -ForegroundColor Yellow

# Stop all running containers
Write-Host "Stopping all running containers..." -ForegroundColor Gray
docker stop $(docker ps -aq) 2>$null

# Remove all containers
Write-Host "Removing all containers..." -ForegroundColor Gray
docker rm $(docker ps -aq) 2>$null

# Remove all images
Write-Host "Removing all Docker images..." -ForegroundColor Gray
docker rmi $(docker images -q) -f 2>$null

# Remove all volumes (optional - uncomment if needed)
# Write-Host "Removing all volumes..." -ForegroundColor Gray
# docker volume rm $(docker volume ls -q) 2>$null

# Clean up Docker system
Write-Host "Cleaning up Docker system..." -ForegroundColor Gray
docker system prune -af --volumes

Write-Host "Docker cleanup completed!" -ForegroundColor Green

# Wait a moment
Start-Sleep -Seconds 2

Write-Host "Starting development server..." -ForegroundColor Cyan

# Run docker-compose for development
docker-compose --profile dev up -d debate-bot-dev

if ($LASTEXITCODE -eq 0) {
    Write-Host "Development server started successfully!" -ForegroundColor Green
    Write-Host "Server available at: http://localhost:8001" -ForegroundColor Cyan
    Write-Host "API Docs: http://localhost:8001/docs" -ForegroundColor Cyan
} else {
    Write-Host "Failed to start development server. Check the error messages above." -ForegroundColor Red
}
