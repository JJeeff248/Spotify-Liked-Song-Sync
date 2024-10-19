@echo off
echo Stopping existing container...
docker-compose down

echo Rebuilding Docker image...
docker-compose build

echo Starting new container...
docker-compose up -d

echo Done! New stack is running.
