@echo off
echo Stopping existing container...
docker stop spotify-sync-container

echo Removing old container...
docker rm spotify-sync-container

echo Rebuilding Docker image...
docker build -t spotify-sync .

echo Starting new container...
docker run -d -p 5000:5000 --env-file .env --name spotify-sync-container spotify-sync

echo Done! New container is running.

