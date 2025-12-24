# MEIH Backend API - Optimized Version

This is the optimized backend API for the MEIH Netflix clone project, built with FastAPI.

## Performance Improvements

### Backend Optimizations
- Updated to latest library versions for better performance
- Implemented ORJSON for faster JSON serialization/deserialization
- Added connection pooling and efficient request handling
- Optimized caching with aiocache for better memory usage
- Improved Gunicorn configuration for better resource utilization

### Proxy Service Optimizations
- Replaced http-proxy with more efficient undici library
- Implemented connection pooling and keep-alive by default
- Added timeout handling and retry logic with exponential backoff
- Enhanced stealth headers to bypass anti-bot measures
- Added multiple fallback mechanisms for reliability

### Resource Usage Optimizations
- Reduced CPU usage through efficient async processing
- Minimized network overhead with connection reuse
- Implemented aggressive caching to reduce repeated requests
- Added request compression and decompression
- Optimized image proxy with proper cache headers

## Features
- Content scraping from various sources
- RESTful API endpoints for content delivery
- Caching mechanisms for improved performance
- Multi-tier scraping with fallback strategies
- Advanced anti-blocking measures

## Tech Stack
- Python 3.10+
- FastAPI
- ORJSON for fast serialization
- aiohttp for async requests
- aiocache for efficient caching
- BeautifulSoup4 for HTML parsing
- Node.js proxy service with undici
- uvicorn/gunicorn for deployment

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   cd proxy-service && npm install
   ```

3. Run the server:
   ```
   python main.py
   ```
   Or with uvicorn directly:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health status
- `GET /content/latest` - Get latest content
- `GET /content/search` - Search content
- `GET /content/group/{cid}` - Get content by category
- `GET /content/details/{entry_id}` - Get detailed content information

## Deployment

The backend is configured for deployment on Render with optimized settings:
- Gunicorn with performance-tuned parameters
- Worker connection pooling
- Request limits to prevent abuse
- Memory-optimized temporary directory usage