#!/bin/bash

# Setup script for Render deployment (Non-Root Version)

echo "Setting up Render environment..."

# 1. Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers (headless)
echo "Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

# 2. Install Node.js locally (without root/sudo)
echo "Installing Node.js locally..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] || curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

nvm install 18
nvm use 18
nvm alias default 18

# Verify Node installation
node -v
npm -v

# 3. Install Proxy Dependencies
echo "Installing Proxy Dependencies..."
cd proxy-service
npm install
cd ..

echo "Setup complete!"
