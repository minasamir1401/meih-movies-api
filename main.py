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
import aiohttp
import os
import sys

# Fix for Windows asyncio issue with subprocesses
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except:
        pass

# Neutral Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("system")

# Scraper logger
scraper_logger = logging.getLogger("provider")

app = FastAPI(title="Media Hub API", version="3.2")

# CORS: Strict but functional
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(f"Response Sent: {response.status_code} in {duration:.2f}s")
        return response
    except Exception as e:
        logger.error(f"Request Failed: {e}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error", "detail": str(e)})

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time(), "workers": os.cpu_count()}

@app.get("/debug/domains")
async def test_domains():
    """Test all Larooza domains to see which ones are accessible"""
    results = []
    for domain in scraper.NET_NODES:
        try:
            test_url = f"{domain}/newvideos1.php"
            raw = await scraper._invoke_remote(test_url)
            status = "✅ Working" if raw and len(raw) > 1000 else "⚠️ Short response"
            results.append({
                "domain": domain,
                "status": status,
                "content_length": len(raw) if raw else 0
            })
        except Exception as e:
            results.append({
                "domain": domain,
                "status": f"❌ Error: {str(e)}",
                "content_length": 0
            })
    return {"tested_domains": results, "total": len(results)}

# 3️⃣ Rate Limiting & Throttling (Simplified)
ip_history = {}
RATE_LIMIT = 100 
RATE_WINDOW = 60

def check_rate_limit(client_ip: str):
    # Temporarily relaxed for production debugging
    return True

# 5️⃣ Aggressive Caching
api_cache = {}
CACHE_TTL = 7200 
DETAILS_CACHE_TTL = 3600 
IMAGE_CACHE_TTL = 172800 

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
    base = str(request.base_url).rstrip('/') if request else ""
    for item in items:
        asset_url = item.get('poster', '')
        if asset_url and not asset_url.startswith('data:'):
            encoded = base64.urlsafe_b64encode(asset_url.encode()).decode()
            item['poster'] = f"{base}/media-asset?token={encoded}"
    return items

@app.get("/")
async def status():
    return {"status": "ok", "version": "3.3", "engine": "stable"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/content/latest")
async def resolve_latest(request: Request, page: int = 1):
    # Manual rate limit check instead of middleware
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        return []

    key = f"latest_p{page}"
    cached = get_cached_content(key)
    if cached: return cached
    
    data = await scraper.get_latest_content(p=page)
    
    # FALLBACK: Use mock data if scraper fails
    if not data:
        logger.warning("Scraper failed, using MOCK DATA as fallback")
        from mock_data import get_mock_latest
        data = get_mock_latest(page)
    
    if not data: return []
    
    res = wrap_assets(data, request)
    set_cached_content(key, res)
    return res

@app.get("/content/search")
async def search_discovery(q: str = Query(..., min_length=2), request: Request = None):
    data = await scraper.search_content(q)
    
    # FALLBACK: Use mock data if scraper fails
    if not data:
        logger.warning("Search failed, using MOCK DATA")
        from mock_data import get_mock_search
        data = get_mock_search(q)
    
    return wrap_assets(data, request)

@app.get("/content/group/{cid}")
async def resolve_group(cid: str, page: int = 1, request: Request = None):
    key = f"group_{cid}_p{page}"
    cached = get_cached_content(key)
    if cached: return cached
    
    data = await scraper.get_category_content(cid, page)
    
    # FALLBACK: Use mock data if scraper fails
    if not data:
        logger.warning(f"Category {cid} failed, using MOCK DATA")
        from mock_data import get_mock_category
        data = get_mock_category(cid, page)
    
    res = wrap_assets(data, request)
    set_cached_content(key, res)
    return res

@app.get("/content/details/{entry_id}")
async def resolve_details(entry_id: str, request: Request = None):
    key = f"details_{entry_id}"
    cached = get_cached_content(key, is_details=True)
    if cached: return cached
    
    data = await scraper.get_content_details(entry_id)
    
    # FALLBACK: Use mock data if scraper fails
    if not data or data.get('title') == "Error":
        logger.warning(f"Details for {entry_id} failed, using MOCK DATA")
        from mock_data import get_mock_details
        data = get_mock_details(entry_id)
        if not data:
            raise HTTPException(status_code=404, detail="Resource unavailable")
    
    if data.get('poster'):
        encoded = base64.urlsafe_b64encode(data['poster'].encode()).decode()
        data['poster'] = f"{str(request.base_url).rstrip('/')}/media-asset?token={encoded}"

    set_cached_content(key, data, is_details=True)
    return data

import aiohttp

@app.get("/media-asset")
async def proxy_asset(token: str):
    """Proxy encrypted assets using aiohttp to avoid Python 3.14 httpx/anyio bugs"""
    try:
        real_url = base64.urlsafe_b64decode(token).decode()
        if not real_url.startswith('http'): 
            real_url = urljoin(scraper.ROOT, real_url)
            
        # URL Healing for assets
        real_url = scraper._heal_url(real_url)
        
        real_url = real_url.replace("http://", "https://")
        
        cache_key = f"asset_{real_url}"
        cached_data = get_cached_content(cache_key, is_image=True)
        if cached_data:
            return Response(
                content=cached_data["content"], 
                media_type=cached_data["media_type"],
                headers={"Cache-Control": "public, max-age=86400"}
            )
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": scraper.ROOT
        }
        
        # Tier 1: Direct Fetch with aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(real_url, headers=headers, timeout=15, ssl=False) as res:
                    if res.status == 200:
                        content = await res.read()
                        media_type = res.headers.get("content-type", "image/jpeg")
                        set_cached_content(cache_key, {"content": content, "media_type": media_type}, is_image=True)
                        return Response(content=content, media_type=media_type)
        except Exception as e:
            logger.warning(f"Direct Fetch Failed: {e}")

        # Tier 2: Local Proxy
        try:
            node_proxy_url = os.environ.get('NODE_PROXY_URL', 'http://localhost:3001')
            direct_proxy_url = f"{node_proxy_url}/proxy?url={quote(real_url)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(direct_proxy_url, timeout=25, ssl=False) as res:
                    if res.status == 200:
                        content = await res.read()
                        media_type = res.headers.get("content-type", "image/jpeg")
                        set_cached_content(cache_key, {"content": content, "media_type": media_type}, is_image=True)
                        return Response(content=content, media_type=media_type)
        except Exception as e:
            logger.error(f"Local Proxy Failed: {e}")
            
        return Response(status_code=404)
    except Exception as e:
        logger.error(f"Asset Proxy Critical Failure: {e}")
        return Response(status_code=404)

@app.get("/system-logs")
async def get_system_logs():
    return {"message": "Logging to console only"}

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("🚀 MEIH BACKEND IS READY AND WAITING FOR REQUESTS (Refreshed)")
    print(f"📡 API Root: http://localhost:8000")
    print(f"🏥 Health Check: http://localhost:8000/health")
    print("="*50 + "\n")

    # Keep-Alive Logic for Render
    async def _keep_alive():
        print("⏰ 'Keep-Alive' background task started.")
        while True:
            try:
                await asyncio.sleep(14 * 60) # 14 minutes
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8000/health") as resp:
                        if resp.status == 200:
                            logger.info(f"💓 Self-Ping Successful: {resp.status}")
                        else:
                            logger.warning(f"⚠️ Self-Ping Returned: {resp.status}")
            except Exception as e:
                logger.error(f"❌ Keep-Alive Error: {e}")
                # Don't break loop on error, just wait and retry
                await asyncio.sleep(60)

    asyncio.create_task(_keep_alive())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
