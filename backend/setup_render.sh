#!/bin/bash

# Setup script for Render deployment

echo "Starting Render setup..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir --upgrade -r requirements.txt

echo "Setup complete!"
