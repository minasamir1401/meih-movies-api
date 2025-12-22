FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    NODE_PROXY_URL=http://localhost:3001

# Install system dependencies + Node.js (Version 18)
# We install curl to fetch nodejs setup, then install nodejs
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first (for better caching)
# We assume the Docker context is the repo root, so we copy from backend/
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the entire backend directory contents into /app
COPY backend/ .

# Install Proxy dependencies
# Now /app/proxy-service exists because we copied backend/ content to /app
RUN cd proxy-service && npm install

# Fix permissions
RUN chmod +x setup_render.sh start_render.sh

# Expose port
EXPOSE 10000

# Start command
CMD ["bash", "start_render.sh"]
