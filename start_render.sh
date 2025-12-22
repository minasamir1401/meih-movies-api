#!/bin/bash

# Startup script for Render deployment

# Load NVM to ensure 'node' command is available
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Starting application..."

# Start Proxy Service in background
echo "Starting Proxy Service directly..."
cd proxy-service
# Use 'nohup' and redirect output, ensuring node from NVM is used
nohup node server.js > proxy.log 2>&1 &
cd ..

# Start the FastAPI application with optimized workers for Render Free Tier (512MB RAM)
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT