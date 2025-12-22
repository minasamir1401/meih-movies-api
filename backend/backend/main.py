from fastapi import FastAPI, HTTPException, Query, Request, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from scraper.engine import scraper
import logging
import asyncio
import base64
import io
import time
import random
import traceback
from urllib.parse import quote, urljoin
import httpx
import os

# Fix for Windows asyncio issue with subprocesses
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Neutral Logging Configuration
import sys
log_stream = io.StringIO()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("system")

# Dual Handler: Log to both in-memory stream and console
memory_handler = logging.StreamHandler(log_stream)
console_handler = logging.StreamHandler(sys.stdout)

logger.addHandler(memory_handler)
logger.addHandler(console_handler)

# Scraper logger
scraper_logger = logging.getLogger("provider")
scraper_logger.addHandler(memory_handler)
scraper_logger.addHandler(console_handler)

# Global Async Client (This will be removed as proxy_asset now uses a local client)
# client = httpx.AsyncClient(timeout=45.0, verify=False, follow_redirects=True)

app = FastAPI(title="Media Hub API", version="3.2")

# CORS: Strict but functional
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], # Changed from ["GET", "OPTIONS"] to ["*"]
    allow_headers=["*"],
)

# 3️⃣ Rate Limiting & Throttling
# Simple in-memory rate limiter: 20 requests / minute / IP
ip_history = {} # { ip: [timestamp1, timestamp2, ...] }
RATE_LIMIT = 20
RATE_WINDOW = 60

async def check_rate_limit(request: Request):
    if not request.client:
        return True
    client_ip = request.client.host
    # 🔓 Dev Bypass: No throttling for localhost
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        return True
    
    # 🔓 Asset Bypass: No throttling for images/health
    if request.url.path in ["/media-asset", "/health", "/"]:
        return True

    now = time.time()
    if client_ip not in ip_history:
        ip_history[client_ip] = []
    
    ip_history[client_ip] = [ts for ts in ip_history[client_ip] if now - ts < RATE_WINDOW]
    
    if len(ip_history[client_ip]) >= RATE_LIMIT:
        logger.warning(f"Throttling IP: {client_ip[:8]}...")
        return False
    
    ip_history[client_ip].append(now)
    return True

# 5️⃣ Aggressive Caching
api_cache = {}
CACHE_TTL = 7200 # 2 hours for general content
DETAILS_CACHE_TTL = 3600 # 1 hour for content details
IMAGE_CACHE_TTL = 172800 # 48 hours for images

def get_cached_content(key, is_image=False, is_details=False):
    if key in api_cache:
        data, ts = api_cache[key]
        ttl = DETAILS_CACHE_TTL if is_details else (IMAGE_CACHE_TTL if is_image else CACHE_TTL)
        if time.time() - ts < ttl:
            return data
    return None

def set_cached_content(key, data, is_image=False, is_details=False):
    ttl = DETAILS_CACHE_TTL if is_details else (IMAGE_CACHE_TTL if is_image else CACHE_TTL)
    api_cache[key] = (data, time.time())

def wrap_assets(items: list, request: Request = None):
    """Encodes asset URLs to be fetched through our media-asset endpoint"""
    # Standardize base URL
    base = str(request.base_url).rstrip('/') if request else ""
    for item in items:
        asset_url = item.get('poster', '')
        if asset_url and not asset_url.startswith('data:'):
            encoded = base64.urlsafe_b64encode(asset_url.encode()).decode()
            item['poster'] = f"{base}/media-asset?token={encoded}"
    return items

@app.middleware("http")
async def secure_middleware(request: Request, call_next):
    try:
        # Apply global throttling check
        if not await check_rate_limit(request):
            # Return neutral empty 200 response
            return JSONResponse(status_code=200, content=[])
        
        return await call_next(request)
    except Exception as e:
        logger.error(f"Middleware caught error: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Middleware Error: {str(e)}"})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global handler caught error: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": f"Global Error: {str(exc)}"}
    )

@app.get("/")
async def status():
    return {"status": "ok", "version": "3.2"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/content/latest")
async def resolve_latest(page: int = 1, request: Request = None):
    key = f"latest_p{page}"
    cached = get_cached_content(key)
    if cached: return cached
    
    data = await scraper.get_latest_content(p=page)
    if not data: return []
    
    res = wrap_assets(data, request)
    set_cached_content(key, res)
    return res

@app.get("/content/search")
async def search_discovery(q: str = Query(..., min_length=2), request: Request = None):
    data = await scraper.search_content(q)
    return wrap_assets(data, request)

@app.get("/content/group/{cid}")
async def resolve_group(cid: str, page: int = 1, request: Request = None):
    key = f"group_{cid}_p{page}"
    cached = get_cached_content(key)
    if cached: return cached
    
    data = await scraper.get_category_content(cid, page)
    res = wrap_assets(data, request)
    set_cached_content(key, res)
    return res

@app.get("/content/details/{entry_id}")
async def resolve_details(entry_id: str, request: Request = None):
    key = f"details_{entry_id}"
    cached = get_cached_content(key, is_details=True)
    if cached: return cached
    
    data = await scraper.get_content_details(entry_id)
    if not data or data.get('title') == "Error":
        raise HTTPException(status_code=404, detail="Resource unavailable")
    
    if data.get('poster'):
        encoded = base64.urlsafe_b64encode(data['poster'].encode()).decode()
        base = str(request.base_url).rstrip('/') if request else ""
        data['poster'] = f"{base}/media-asset?token={encoded}"

    set_cached_content(key, data, is_details=True)
    return data

@app.get("/media-asset")
async def proxy_asset(token: str):
    """Proxy encrypted assets with multi-tier fallback and deep logging"""
    try:
        # 1. Decode & Sanitize
        real_url = base64.urlsafe_b64decode(token).decode()
        if not real_url.startswith('http'): 
            real_url = urljoin(scraper.ROOT, real_url)
            
        # Ensure HTTPS to avoid mixed content in production
        real_url = real_url.replace("http://", "https://")
        
        # Check cache first for images
        cache_key = f"asset_{real_url}"
        cached_data = get_cached_content(cache_key, is_image=True)
        if cached_data:
            logger.info(f"Asset Served [Cached]: {real_url[:40]}...")
            return Response(
                content=cached_data["content"], 
                media_type=cached_data["media_type"],
                headers={"Cache-Control": "public, max-age=86400"}
            )
            
        logger.info(f"Asset Request: {real_url[:60]}...")
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": scraper.ROOT,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        # Jitter to avoid bot detection
        await asyncio.sleep(random.uniform(0.1, 0.3))

        async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as local_client:
            # Tier 1: Direct Fetch
            try:
                res = await local_client.get(real_url, headers=headers)
                if res.status_code == 200 and len(res.content) > 200:
                    logger.info(f"Asset Served [Direct]: {real_url[:40]}")
                    # Cache the image data
                    media_type = res.headers.get("content-type", "image/jpeg")
                    set_cached_content(cache_key, {"content": res.content, "media_type": media_type}, is_image=True)
                    return Response(
                        content=res.content, 
                        media_type=media_type,
                        headers={"Cache-Control": "public, max-age=86400"}
                    )
            except Exception as e:
                logger.warning(f"Direct Fetch Failed: {str(e)[:50]}")

            # Tier 2: ScraperAPI Proxy
            key = scraper.token
            proxy_url = f"http://api.scraperapi.com?api_key={key}&url={quote(real_url)}"
            try:
                res = await local_client.get(proxy_url, timeout=25.0)
                if res.status_code == 200:
                    logger.info(f"Asset Served [Proxy]: {real_url[:40]}")
                    # Cache the image data
                    media_type = "image/jpeg"
                    set_cached_content(cache_key, {"content": res.content, "media_type": media_type}, is_image=True)
                    return Response(content=res.content, media_type=media_type)
            except Exception as e:
                logger.error(f"Proxy Fetch Failed: {str(e)[:50]}")
            
        return Response(status_code=404)
    except Exception as e:
        logger.error(f"Asset Proxy Critical Failure: {e}")
        raise HTTPException(status_code=404)

@app.get("/system-logs")
async def get_system_logs():
    return {"data": log_stream.getvalue()[-2000:]}
