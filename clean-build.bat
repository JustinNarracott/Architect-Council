@echo off
REM Clean build script for Architecture Council
REM Nukes Docker cache and rebuilds from scratch

echo [1/4] Stopping containers...
docker compose -f docker/docker-compose.yml down --remove-orphans

echo [2/4] Removing old images...
docker image prune -f

echo [3/4] Building fresh (no cache)...
docker compose -f docker/docker-compose.yml build --no-cache

echo [4/4] Starting containers...
docker compose -f docker/docker-compose.yml up -d

echo.
echo Done.
echo Backend:  http://localhost:8011
echo Frontend: http://localhost:3011
echo Logs: docker compose -f docker/docker-compose.yml logs -f
