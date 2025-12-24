#!/bin/bash

# Startup script for Render deployment

echo "Starting application..."

# Start Proxy Service in background on port 3001
echo "Starting Proxy Service on port 3001..."
cd proxy-service
# Start proxy WITHOUT setting PORT env var (will use default 3001 from server.js)
nohup node server.js > proxy.log 2>&1 &
PROXY_PID=$!
echo "Proxy started with PID: $PROXY_PID"
cd ..

# Wait a moment for proxy to bind to port
sleep 3

# Start the FastAPI application with optimized workers for Render Free Tier (512MB RAM)
# Using uvicorn worker directly via gunicorn on the main PORT (10000)
echo "Starting FastAPI on port ${PORT}..."
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 --worker-tmp-dir /dev/shm main:app --bind 0.0.0.0:${PORT}