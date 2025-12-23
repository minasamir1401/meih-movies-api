FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    NODE_PROXY_URL=http://localhost:3001

# Install system dependencies + Node.js (Version 18)
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first (for better caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright
RUN playwright install --with-deps chromium

# Copy the entire backend directory contents into /app
COPY backend/ .

# Force copy the latest start_render.sh
COPY backend/start_render.sh ./start_render.sh

# Install Proxy dependencies
RUN cd proxy-service && npm install

# Fix permissions
RUN chmod +x setup_render.sh start_render.sh

# Expose port
EXPOSE 10000

# Start command
CMD ["bash", "start_render.sh"]
