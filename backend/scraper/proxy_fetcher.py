"""
Free Proxy Fetcher - Automatically fetches and validates free proxies
"""
import aiohttp
import asyncio
import logging

logger = logging.getLogger("proxy_fetcher")

class FreeProxyFetcher:
    def __init__(self):
        self.proxies = []
        self.last_fetch = 0
        
    async def fetch_free_proxies(self):
        """Fetch free proxies from public APIs"""
        proxy_sources = [
            "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
        ]
        
        all_proxies = []
        async with aiohttp.ClientSession() as session:
            for source in proxy_sources:
                try:
                    async with session.get(source, timeout=10) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            proxies = [f"http://{line.strip()}" for line in text.split('\n') if line.strip()]
                            all_proxies.extend(proxies[:20])  # Take first 20 from each source
                            logger.info(f"Fetched {len(proxies)} proxies from {source}")
                except Exception as e:
                    logger.error(f"Failed to fetch from {source}: {e}")
        
        self.proxies = all_proxies
        logger.info(f"Total free proxies loaded: {len(self.proxies)}")
        return self.proxies
    
    async def validate_proxy(self, proxy, test_url="https://httpbin.org/ip"):
        """Test if a proxy works"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, proxy=proxy, timeout=5) as resp:
                    if resp.status == 200:
                        return True
        except:
            pass
        return False
    
    async def get_working_proxies(self, max_count=10):
        """Get validated working proxies"""
        if not self.proxies:
            await self.fetch_free_proxies()
        
        working = []
        tasks = [self.validate_proxy(p) for p in self.proxies[:30]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for proxy, is_working in zip(self.proxies[:30], results):
            if is_working and len(working) < max_count:
                working.append(proxy)
        
        logger.info(f"Validated {len(working)} working proxies")
        return working

proxy_fetcher = FreeProxyFetcher()
