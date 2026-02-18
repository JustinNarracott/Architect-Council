@echo off
REM Clean build script for Architecture Council
REM Nukes Docker cache to ensure fresh layers

echo [1/4] Stopping containers...
cd /d D:\Projects\Architect-Council
docker compose -f docker/docker-compose.yml down --remove-orphans

echo [2/4] Removing old images (no-cache build)...
docker image prune -f

echo [3/4] Building fresh (no cache)...
docker compose -f docker/docker-compose.yml build --no-cache

echo [4/4] Starting containers...
docker compose -f docker/docker-compose.yml up -d

echo.
echo Done. App at http://localhost:3011
echo Logs: docker compose -f docker/docker-compose.yml logs -f
