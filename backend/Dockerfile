FROM python:3.10-slim

WORKDIR /app

# Set up environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 10000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 10000

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
# Render deploy 2025-12-21 20:38
