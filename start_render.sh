#!/bin/bash

# Startup script for Render deployment

echo "Starting application..."

# Start Proxy Service in background
echo "Starting Proxy Service directly..."
cd proxy-service
nohup node server.js > proxy.log 2>&1 &
cd ..

# Start the FastAPI application
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app