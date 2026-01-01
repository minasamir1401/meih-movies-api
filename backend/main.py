import logging
import time
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from scraper.engine import scraper
from downloader import downloader
import os
import re
from urllib.parse import unquote
from fastapi.staticfiles import StaticFiles
from database import init_db
from keep_alive import keep_alive
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("backend")

app = FastAPI(title="MEIH Movies API", version="2.0.0")

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("🚀 Database initialized and ready")
    
    # Start Keep-Alive service for Render.com
    asyncio.create_task(keep_alive.start())
    logger.info("🔄 Keep-Alive service activated")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "engine": "Nitro-Power Larooza Engine",
        "active_mirror": scraper.BASE_URL,
        "engine_status": "WARM" if scraper._cookies_synced else "COLD"
    }

@app.get("/latest")
async def get_latest(page: int = 1):
    try:
        items = await scraper.fetch_home(page=page)
        return items
    except Exception as e:
        logger.error(f"Error fetching latest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/category/{cat_id}")
async def get_category(cat_id: str, page: int = 1):
    try:
        items = await scraper.fetch_category(cat_id, page=page)
        return items
    except Exception as e:
        logger.error(f"Error fetching category {cat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(q: str):
    try:
        items = await scraper.search(q)
        return items
    except Exception as e:
        logger.error(f"Error searching for {q}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/details/{safe_id}")
async def get_details(safe_id: str):
    try:
        details = await scraper.fetch_details(safe_id)
        if not details:
            return JSONResponse(status_code=404, content={"error": "Content not found"})
        return details
    except Exception as e:
        logger.error(f"Error fetching details for {safe_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proxy/image")
async def proxy_image(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    url = unquote(url)
    try:
        # Using follow_redirects and a longer timeout for images
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": scraper.headers["User-Agent"]})
            if resp.status_code == 200:
                # Return the image stream directly
                return StreamingResponse(
                    resp.iter_bytes(), 
                    media_type=resp.headers.get("Content-Type", "image/jpeg"),
                    headers={"Cache-Control": "public, max-age=31536000"}
                )
            else:
                logger.warning(f"Failed to proxy image {url} (Status: {resp.status_code})")
                return JSONResponse(status_code=resp.status_code, content={"error": f"Failed (Status {resp.status_code})"})
    except httpx.TimeoutException:
        logger.warning(f"Timeout proxying image: {url}")
        return JSONResponse(status_code=504, content={"error": "Image timeout"})
    except Exception as e:
        logger.error(f"Proxy image error for {url}: {type(e).__name__} - {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/download/info")
async def get_download_info(url: str):
    try:
        info = await downloader.get_info(url)
        return info
    except Exception as e:
        logger.error(f"Download info error for {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/file")
async def download_file(url: str, filename: str = "video.mp4"):
    # This just redirects for now, or could proxy but large files are risky for memory
    return JSONResponse(content={"url": url, "filename": filename})

@app.get("/health")
async def health():
    # Check FlareSolverr
    fs_status = "OFFLINE"
    try:
        # Increase timeout as solver might be busy
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:8191/health")
            if resp.status_code == 200:
                fs_status = "ONLINE"
    except:
        pass

    return {
        "backend": "ONLINE",
        "flaresolverr": fs_status,
        "scraper_sync": scraper._cookies_synced,
        "timestamp": time.time()
    }

# --- Frontend Mounting ---
# This ensures that our React app is served directly by FastAPI in production
# Check both relative and same-level structures for Docker/Local compatibility
base_dir = os.path.dirname(__file__)
frontend_path = os.path.join(base_dir, "meih-netflix-clone", "dist")

if not os.path.exists(frontend_path):
    # Try one level up (local dev structure)
    frontend_path = os.path.join(base_dir, "..", "meih-netflix-clone", "dist")

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # If the path starts with api/ or other backend routes, it should have been caught above
        # Otherwise, serve the main index.html for React Router to handle
        file_path = os.path.join(frontend_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    logger.warning(f"Frontend dist folder not found at {frontend_path}. Frontend serving disabled.")

if __name__ == "__main__":
    import uvicorn
    # Use port 7860 for Hugging Face Spaces compatibility
    uvicorn.run(app, host="0.0.0.0", port=7860)
