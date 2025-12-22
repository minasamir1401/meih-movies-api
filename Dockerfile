FROM python:3.10-slim

WORKDIR /app

# Set up environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 10000
ENV NODE_PROXY_URL http://localhost:3001

# Install system dependencies (curl for Node install)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY . .

# Install Node dependencies
RUN cd proxy-service && npm install

# Expose port
EXPOSE 10000

# Script to start both services
RUN chmod +x start_render.sh
CMD ["./start_render.sh"]
