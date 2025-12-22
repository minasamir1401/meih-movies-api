#!/bin/bash

# Setup script for Render deployment

echo "Starting Render setup..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir --upgrade -r requirements.txt


# Install Node.js
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs
npm install -g pm2

# Install Proxy Dependencies
echo "Installing Proxy Dependencies..."
cd proxy-service
npm install
cd ..

echo "Setup complete!"
