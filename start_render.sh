#!/bin/bash

# Startup script for Render deployment

echo "Starting application..."

# Start Proxy Service in background on port 3001
echo "Starting Proxy Service on port 3001..."
cd proxy-service
# Export PORT for proxy to use 3001, then start it in background
PORT=3001 nohup node server.js > proxy.log 2>&1 &
PROXY_PID=$!
echo "Proxy started with PID: $PROXY_PID"
cd ..

# Wait a moment for proxy to bind to port
sleep 2

# Start the FastAPI application with optimized workers for Render Free Tier (512MB RAM)
# Using uvicorn worker directly via gunicorn on the main PORT (10000)
echo "Starting FastAPI on port ${PORT}..."
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:${PORT}