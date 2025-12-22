# MEIH Movies API - Backend

## Overview

This is the backend API for the MEIH Movies streaming platform. It provides scraping capabilities for video content, including metadata extraction, server discovery, and download link extraction.

## Features

- Video content scraping from multiple sources
- Metadata extraction (titles, descriptions, posters)
- Server discovery for streaming
- Download link extraction
- Rate limiting and caching for performance
- Ad-blocking and tracker blocking
- Optimized headless browser scraping with Playwright

## Tech Stack

- **Framework**: FastAPI (Python)
- **Scraping**: Playwright (headless browser)
- **Parsing**: BeautifulSoup4
- **Caching**: In-memory caching with TTL
- **Deployment**: Render.com (recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install-deps
   playwright install chromium
   ```

5. **Run the application**
   ```bash
   python main.py
   ```
   
   Or with uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health status
- `GET /content/latest` - Latest content
- `GET /content/search?q={query}` - Search content
- `GET /content/group/{cid}` - Content by category
- `GET /content/details/{entry_id}` - Content details
- `GET /media-asset?token={encoded_url}` - Proxy for media assets
- `GET /system-logs` - Application logs

## Environment Variables

- `SCRAPER_API_KEY` - API key for ScraperAPI (optional)
- `NETWORK_NODES` - Comma-separated list of network nodes
- `PORT` - Port to run the application on (default: 10000)

## Deployment

See [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── scraper/
│   ├── engine.py        # Original scraping engine
│   ├── optimized_headless_scraper.py  # Optimized Playwright scraper
│   └── __init__.py
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── render.yaml          # Render deployment configuration
├── setup_render.sh      # Render setup script
├── start_render.sh      # Render start script
└── README.md            # This file
```

## Optimization Features

1. **Ad Blocking**: Blocks ads and trackers during scraping
2. **Resource Optimization**: Blocks unnecessary resources (images, fonts, etc.)
3. **Session Persistence**: Reuses browser contexts for faster repeated loads
4. **Anti-Bot Detection**: Uses stealth techniques to avoid bot detection
5. **Caching**: Implements intelligent caching for better performance
6. **Rate Limiting**: Prevents server overload with built-in rate limiting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License.