#!/bin/bash

# Setup script for Render deployment

echo "Starting Render setup..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir --upgrade -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install-deps
playwright install chromium

# Run database migrations if needed
# python manage.py migrate

echo "Setup complete!"