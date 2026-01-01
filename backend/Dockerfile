FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install basic system dependencies + Chrome for Undetected Chromedriver
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    wget \
    gnupg \
    xvfb \
    xauth \
    dos2unix \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Create a non-privileged user and setup home
RUN useradd -m -u 1000 user
RUN chown -R user:user /app
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Copy application code
COPY . .

# Fix permissions and line endings
USER root
RUN dos2unix start.sh && chmod +x start.sh && chown -R user:user /app

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the port (Render uses $PORT env var, default 7860)
EXPOSE 7860
ENV PORT=7860

# Kickstart the engine
CMD uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
