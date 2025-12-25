# MEIH Backend API

This is the backend API for the MEIH Netflix clone project, built with FastAPI.

## Features
- Content scraping from various sources
- RESTful API endpoints for content delivery
- Caching mechanisms for improved performance
- Multi-tier scraping with fallback strategies
- Automatic handling of meta refresh redirects

## Tech Stack
- Python 3.10+
- FastAPI
- BeautifulSoup4
- aiohttp
- uvicorn

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
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

## Recent Fixes

- Fixed handling of meta refresh redirects that were preventing content retrieval
- Improved redirect following mechanism for better compatibility with source websites

## Deployment

The backend is configured for deployment on Render. See the `render.yaml` file for configuration details.