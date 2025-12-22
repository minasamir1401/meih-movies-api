#!/bin/bash

# Startup script for Render deployment

echo "Starting application..."

# Start the FastAPI application
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app