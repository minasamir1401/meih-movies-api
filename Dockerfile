# ==========================================
# Nitro Backend-Only Dockerfile for Hugging Face
# ==========================================
FROM python:3.11-slim

# Install system dependencies for Scraper (Chrome) and FlareSolverr
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    wget \
    gnupg \
    xvfb \
    xauth \
    dos2unix \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Backend Dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy Backend Application
COPY backend/ ./

# Fix line endings and permissions
RUN dos2unix start.sh && chmod +x start.sh

# Create local user for Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
RUN chown -R user:user /app
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONPATH=/app

# Expose the mandatory Hugging Face Space port
EXPOSE 7860

# Kickstart the engine
CMD ["/bin/bash", "./start.sh"]
