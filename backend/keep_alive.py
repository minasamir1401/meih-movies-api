"""
Keep-Alive Service to prevent Render.com from sleeping
Pings the server every 10 minutes to maintain activity
"""
import asyncio
import httpx
import logging
from datetime import datetime

logger = logging.getLogger("keep_alive")

class KeepAliveService:
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url
        self.running = False
        self.ping_interval = 600  # 10 minutes
        
    async def start(self):
        """Start the keep-alive service"""
        self.running = True
        logger.info("🔄 Keep-Alive service started (pinging every 10 minutes)")
        
        while self.running:
            try:
                await asyncio.sleep(self.ping_interval)
                await self._ping()
            except Exception as e:
                logger.error(f"Keep-Alive error: {e}")
    
    async def _ping(self):
        """Send a ping to keep the service alive"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    logger.info(f"✅ Keep-Alive ping successful at {datetime.now().strftime('%H:%M:%S')}")
                else:
                    logger.warning(f"⚠️ Keep-Alive ping returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Keep-Alive ping failed: {e}")
    
    def stop(self):
        """Stop the keep-alive service"""
        self.running = False
        logger.info("Keep-Alive service stopped")

keep_alive = KeepAliveService()
