#!/bin/bash

# Startup script for Render deployment

echo "Starting application..."

# Start Proxy Service in background
echo "Starting Proxy Service..."
cd proxy-service
pm2 start server.js --name "stealth-proxy"
cd ..

# Start the FastAPI application
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app