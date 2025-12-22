#!/bin/bash

# Startup script for Render deployment

echo "Starting application..."

# Start Proxy Service in background
echo "Starting Proxy Service directly..."
cd proxy-service
# Use 'nohup' and redirect output
nohup node server.js > proxy.log 2>&1 &
cd ..

# Start the FastAPI application with optimized workers for Render Free Tier (512MB RAM)
# Using uvicorn worker directly via gunicorn
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT