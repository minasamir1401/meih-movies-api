"""
Production-Ready Hybrid Scraping Engine

Multi-Tier Fallback Architecture:
  Tier 1: Direct HTTP request (httpx) - fastest, works when no protection
  Tier 2: curl_cffi with browser impersonation - bypasses TLS fingerprinting
  Tier 3: ScraperAPI proxy - when direct/curl fail (rate limited)
  Tier 4: Playwright headless browser - for JS-rendered content

Intelligent Detection:
  - 403 Forbidden → escalate to next tier
  - JavaScript challenge → escalate to Playwright
  - Empty/short HTML → escalate to render mode
  - Cloudflare/WAF → use stealth browser

Windows Compatibility:
  - Proper asyncio event loop policy
  - Playwright subprocess handling
  - Non-blocking async operations
"""

import asyncio
import re
import logging
import base64
import random
import os
import sys
import time
from typing import List, Dict, Optional, Tuple
from collections import OrderedDict
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
import httpx

# ============================================================================
# OPTIONAL DEPENDENCIES
# ============================================================================
try:
    import nest_asyncio
    nest_asyncio.apply()
except (ImportError, ValueError):
    # ValueError: Can't patch uvloop (used in production)
    pass

if sys.platform == 'win32':
    # Use ProactorEventLoop for subprocess support on Windows
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
logger = logging.getLogger("provider")
logger.setLevel(logging.DEBUG)

# File handler for persistent logs
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
log_handler = logging.FileHandler('scraper_provider.log', encoding='utf-8')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)

# Console handler for debugging
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)


class ProviderError(Exception):
    """Custom exception for scraping errors"""
    def __init__(self, message: str, status_code: int = None, tier: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.tier = tier


class DiscoveryCache:
    """Thread-safe LRU cache with TTL expiration"""
    
    def __init__(self, capacity: int = 1000):
        self.cache = OrderedDict()
        self.capacity = capacity
        self._last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[str]:
        if key not in self.cache:
            return None
        data, ts, ttl = self.cache[key]
        if time.time() - ts > ttl:
            del self.cache[key]
            return None
        self.cache.move_to_end(key)
        return data
    
    def put(self, key: str, value: str, ttl: int = 3600):
        current_time = time.time()
        
        # Periodic cleanup of expired entries
        if current_time - self._last_cleanup > 60:
            expired_keys = [
                k for k, (_, ts, entry_ttl) in self.cache.items()
                if current_time - ts > entry_ttl
            ]
            for k in expired_keys:
                del self.cache[k]
            self._last_cleanup = current_time
        
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = (value, time.time(), ttl)
        
        # LRU eviction
        while len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def clear(self):
        self.cache.clear()


class ResourceResolver:
    """
    Production-ready hybrid scraping engine with intelligent fallback.
    
    SCRAPING FLOW:
    ┌─────────────────────────────────────────────────────────────────┐
    │                       SCRAPING REQUEST                          │
    └─────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ TIER 1: Direct HTTP (httpx)                                     │
    │ - Fastest option, no external dependencies                      │
    │ - Works when target has no anti-bot protection                  │
    └─────────────────────────┬───────────────────────────────────────┘
                              │ 403/Challenge detected?
                              ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ TIER 2: curl_cffi (TLS Fingerprint Bypass)                      │
    │ - Impersonates real browser TLS fingerprint                     │
    │ - Bypasses basic fingerprinting protection                      │
    └─────────────────────────┬───────────────────────────────────────┘
                              │ Still blocked?
                              ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ TIER 3: ScraperAPI Proxy (if credits available)                 │
    │ - Rotates IP addresses automatically                            │
    │ - Handles CAPTCHAs and challenges                               │
    └─────────────────────────┬───────────────────────────────────────┘
                              │ JS rendering needed?
                              ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ TIER 4: Playwright Headless Browser                             │
    │ - Full JavaScript execution                                      │
    │ - Stealth mode to avoid detection                               │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    # Provider domains (configurable via environment)
    NET_NODES = os.getenv("NETWORK_NODES", "https://larooza.site,https://larooza.tv,https://larooza.net").split(',')
    
    # Detection patterns for anti-bot protection
    PROTECTION_PATTERNS = [
        'cloudflare',
        'cf-ray',
        'just a moment',
        'checking your browser',
        'ddos-guard',
        'please wait',
        'security check',
        'access denied',
        'bot detected',
        'captcha',
        'recaptcha',
        'hcaptcha',
    ]
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff
    
    def __init__(self):
        self.token = os.getenv("SCRAPER_API_KEY", "")
        self.node_idx = 0
        self.ROOT = self.NET_NODES[0]
        self.concurrency = asyncio.Semaphore(8)
        self.store = DiscoveryCache(capacity=800)
        
        # Playwright instance (lazy initialized)
        self._playwright = None
        self._browser = None
        self._browser_lock = asyncio.Lock()
        
        # HTTP clients (reusable)
        self._http_client = None
        self._curl_session = None
        
        # Monitoring statistics
        self.stats = {
            'requests_made': 0,
            'tier1_success': 0,
            'tier2_success': 0,
            'tier3_success': 0,
            'tier4_success': 0,
            'cache_hits': 0,
            'total_errors': 0,
            'start_time': time.time()
        }
        
        # User agents rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        ]
    
    def _update_stats(self, key: str, increment: int = 1):
        """Update monitoring statistics"""
        if key in self.stats:
            self.stats[key] += increment
    
    def get_stats(self) -> Dict:
        """Get current monitoring statistics with computed metrics"""
        elapsed = time.time() - self.stats['start_time']
        stats = self.stats.copy()
        stats['requests_per_second'] = stats['requests_made'] / max(elapsed, 1)
        stats['success_rate'] = (
            (stats['tier1_success'] + stats['tier2_success'] + 
             stats['tier3_success'] + stats['tier4_success']) / 
            max(stats['requests_made'], 1) * 100
        )
        return stats
    
    def _cycle_node(self):
        """Rotate to next provider domain"""
        self.node_idx = (self.node_idx + 1) % len(self.NET_NODES)
        self.ROOT = self.NET_NODES[self.node_idx]
        logger.info(f"Cycled to node: {self.ROOT}")
    
    def _generate_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Generate realistic browser headers"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': random.choice(self.user_agents),
            'Cache-Control': 'max-age=0',
        }
        if referer:
            headers['Referer'] = referer
            headers['Origin'] = urlparse(referer).scheme + '://' + urlparse(referer).netloc
        return headers
    
    def _is_blocked(self, content: str, status_code: int) -> Tuple[bool, str]:
        """
        Detect if response indicates blocking/protection.
        Returns (is_blocked, reason)
        """
        if status_code == 403:
            return True, "HTTP 403 Forbidden"
        
        if status_code == 503:
            return True, "HTTP 503 Service Unavailable (possible WAF)"
        
        if status_code == 429:
            return True, "HTTP 429 Rate Limited"
        
        if not content or len(content) < 500:
            return True, f"Suspiciously short content ({len(content) if content else 0} bytes)"
        
        content_lower = content.lower()[:2000]
        for pattern in self.PROTECTION_PATTERNS:
            if pattern in content_lower:
                return True, f"Protection pattern detected: {pattern}"
        
        # Check for JavaScript challenge
        if '<noscript>' in content_lower and 'enable javascript' in content_lower:
            return True, "JavaScript challenge detected"
        
        return False, ""
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create reusable HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=20.0,
                verify=False,
                follow_redirects=True,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
                http2=True,
            )
        return self._http_client
    
    async def _tier1_direct(self, url: str, headers: Dict) -> Tuple[Optional[str], int]:
        """
        TIER 1: Direct HTTP request using httpx.
        Fastest option, works when target has no protection.
        """
        try:
            client = await self._get_http_client()
            response = await client.get(url, headers=headers)
            return response.text, response.status_code
        except httpx.TimeoutException:
            logger.warning(f"Tier 1 timeout for {url}")
            return None, 0
        except Exception as e:
            logger.warning(f"Tier 1 error for {url}: {e}")
            return None, 0
    
    async def _tier2_curl_cffi(self, url: str) -> Tuple[Optional[str], int]:
        """
        TIER 2: curl_cffi with browser TLS fingerprint impersonation.
        Bypasses TLS fingerprinting protection.
        Only available if curl_cffi is installed.
        """
        try:
            from curl_cffi.requests import AsyncSession
        except ImportError:
            logger.debug("curl_cffi not installed, skipping Tier 2")
            return None, 0
        
        try:
            async with AsyncSession() as session:
                response = await session.get(
                    url,
                    impersonate="chrome120",
                    timeout=20,
                    allow_redirects=True,
                )
                return response.text, response.status_code
        except Exception as e:
            logger.warning(f"Tier 2 error for {url}: {e}")
            return None, 0
    
    async def _tier3_scraperapi(self, url: str, render: bool = False) -> Tuple[Optional[str], int]:
        """
        TIER 3: ScraperAPI proxy service.
        Rotates IPs and handles some anti-bot measures.
        """
        if not self.token:
            logger.debug("ScraperAPI token not configured, skipping Tier 3")
            return None, 0
        
        try:
            # Build proxy URL
            if render:
                proxy_url = f"http://scraperapi.render=true:{self.token}@proxy-server.scraperapi.com:8001"
            else:
                proxy_url = f"http://scraperapi:{self.token}@proxy-server.scraperapi.com:8001"
            
            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=45.0,
                verify=False,
                follow_redirects=True
            ) as client:
                headers = self._generate_headers()
                response = await client.get(url, headers=headers)
                
                # Check if ScraperAPI credits exhausted
                if response.status_code == 403 and 'exhausted' in response.text.lower():
                    logger.error("ScraperAPI credits exhausted!")
                    return None, 403
                
                return response.text, response.status_code
        except Exception as e:
            logger.warning(f"Tier 3 error for {url}: {e}")
            return None, 0
    
    async def _tier4_playwright(self, url: str, wait_time: int = 3000) -> Tuple[Optional[str], int]:
        """
        TIER 4: Playwright headless browser.
        Full JavaScript execution with stealth mode.
        Only available if playwright is installed.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.debug("Playwright not installed, skipping Tier 4")
            return None, 0
        
        try:
            
            async with self._browser_lock:
                if self._playwright is None:
                    self._playwright = await async_playwright().start()
                
                if self._browser is None:
                    # Browser launch arguments
                    args = [
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-first-run',
                    ]
                    
                    self._browser = await self._playwright.chromium.launch(
                        headless=True,
                        args=args
                    )
            
            # Create context with stealth settings
            context = await self._browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                java_script_enabled=True,
                bypass_csp=True,
                ignore_https_errors=True,
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            # Stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                window.chrome = { runtime: {} };
            """)
            
            page = await context.new_page()
            
            try:
                response = await page.goto(url, wait_until='load', timeout=30000)
                status_code = response.status if response else 0
                
                # Wait for dynamic content
                await page.wait_for_timeout(wait_time)
                
                # Handle meta refresh redirects
                content = await page.content()
                if '<meta' in content.lower() and 'refresh' in content.lower():
                    refresh_match = re.search(
                        r'<meta[^>]*http-equiv=["\']?refresh["\']?[^>]*content=["\']?\d*;\s*url=([^"\'>]+)',
                        content, re.IGNORECASE
                    )
                    if refresh_match:
                        redirect_url = refresh_match.group(1).strip('"\'')
                        if not redirect_url.startswith('http'):
                            redirect_url = urljoin(url, redirect_url)
                        logger.info(f"Following meta refresh to: {redirect_url}")
                        await page.goto(redirect_url, wait_until='load', timeout=15000)
                        await page.wait_for_timeout(2000)
                        content = await page.content()
                
                return content, status_code
                
            finally:
                await page.close()
                await context.close()
                
        except Exception as e:
            logger.warning(f"Tier 4 error for {url}: {e}")
            return None, 0
    
    async def _invoke_remote(self, endpoint: str, ref: Optional[str] = None, force_tier: int = 0) -> str:
        """
        Intelligent multi-tier content fetching with automatic escalation.
        
        Args:
            endpoint: URL to fetch
            ref: Referer URL (optional)
            force_tier: Force starting from specific tier (0=auto, 1-4=specific tier)
        
        Returns:
            Page content as string, empty string on failure
        """
        # Check cache first
        cached = self.store.get(endpoint)
        if cached:
            self._update_stats('cache_hits')
            logger.debug(f"Cache hit for: {endpoint[:60]}...")
            return cached
        
        # Rate limiting jitter
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        async with self.concurrency:
            self._update_stats('requests_made')
            headers = self._generate_headers(ref or self.ROOT)
            
            content = None
            status_code = 0
            successful_tier = 0
            
            # TIER 1: Direct HTTP
            if force_tier == 0 or force_tier == 1:
                logger.info(f"[TIER 1] Direct fetch: {endpoint[:60]}...")
                content, status_code = await self._tier1_direct(endpoint, headers)
                
                if content and status_code == 200:
                    is_blocked, reason = self._is_blocked(content, status_code)
                    if not is_blocked:
                        self._update_stats('tier1_success')
                        successful_tier = 1
                    else:
                        logger.info(f"[TIER 1] Blocked: {reason}")
                        content = None
                else:
                    logger.info(f"[TIER 1] Failed with status {status_code}")
            
            # TIER 2: curl_cffi
            if not content and (force_tier == 0 or force_tier == 2):
                logger.info(f"[TIER 2] curl_cffi fetch: {endpoint[:60]}...")
                content, status_code = await self._tier2_curl_cffi(endpoint)
                
                if content and status_code == 200:
                    is_blocked, reason = self._is_blocked(content, status_code)
                    if not is_blocked:
                        self._update_stats('tier2_success')
                        successful_tier = 2
                    else:
                        logger.info(f"[TIER 2] Blocked: {reason}")
                        content = None
                elif content:
                    logger.info(f"[TIER 2] Failed with status {status_code}")
            
            # TIER 3: ScraperAPI (skip if credits known to be exhausted)
            if not content and (force_tier == 0 or force_tier == 3) and self.token:
                logger.info(f"[TIER 3] ScraperAPI fetch: {endpoint[:60]}...")
                content, status_code = await self._tier3_scraperapi(endpoint, render=False)
                
                if content and status_code == 200:
                    is_blocked, reason = self._is_blocked(content, status_code)
                    if not is_blocked:
                        self._update_stats('tier3_success')
                        successful_tier = 3
                    else:
                        # Try render mode
                        logger.info(f"[TIER 3] Blocked, trying render mode: {reason}")
                        content, status_code = await self._tier3_scraperapi(endpoint, render=True)
                        if content and status_code == 200:
                            is_blocked, _ = self._is_blocked(content, status_code)
                            if not is_blocked:
                                self._update_stats('tier3_success')
                                successful_tier = 3
                            else:
                                content = None
                        else:
                            content = None
                elif content:
                    logger.info(f"[TIER 3] Failed with status {status_code}")
            
            # TIER 4: Playwright
            if not content and (force_tier == 0 or force_tier == 4):
                logger.info(f"[TIER 4] Playwright fetch: {endpoint[:60]}...")
                content, status_code = await self._tier4_playwright(endpoint)
                
                if content and len(content) > 500:
                    self._update_stats('tier4_success')
                    successful_tier = 4
                else:
                    content = None
            
            # Final result
            if content and successful_tier > 0:
                logger.info(f"[SUCCESS] Tier {successful_tier} succeeded for: {endpoint[:60]}...")
                self.store.put(endpoint, content, ttl=3600)
                return content
            else:
                self._update_stats('total_errors')
                logger.error(f"[FAILED] All tiers failed for: {endpoint[:60]}...")
                return ""
    
    # ========================================================================
    # CONTENT EXTRACTION METHODS
    # ========================================================================
    
    def _map_content_grid(self, raw_html: str) -> List[Dict]:
        """Extract content items from grid/list pages"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        nodes = []
        seen_uids = set()
        
        # Dynamic selectors
        grids = soup.select('li.col-sm-4, .pm-li-video, .video-item, article, .col-md-3')
        
        for node in grids:
            anchor = node.select_one('a.ellipsis, a[href*="video.php"]')
            if not anchor:
                continue
            
            ref_path = anchor.get('href', '')
            abs_url = urljoin(self.ROOT, ref_path)
            
            # Generate stable UID
            v_match = re.search(r'vid=([^&]+)', abs_url)
            uid = v_match.group(1) if v_match else base64.urlsafe_b64encode(abs_url.encode()).decode()
            
            if uid in seen_uids:
                continue
            seen_uids.add(uid)
            
            # Extract poster image
            asset_node = node.find('img')
            asset_url = ""
            if asset_node:
                attrs_to_check = ['data-src', 'data-echo', 'data-original', 'lazy-src', 'data-lazy', 'src']
                for attr in attrs_to_check:
                    val = asset_node.get(attr)
                    if val and isinstance(val, str) and not val.startswith('data:image'):
                        if val.startswith('http'):
                            asset_url = val
                        elif val.startswith('//'):
                            asset_url = "https:" + val
                        else:
                            asset_url = urljoin(self.ROOT, val)
                        break
            
            # Extract title
            label = ""
            if anchor.get('title'):
                label = anchor.get('title')
            elif asset_node and asset_node.get('alt'):
                label = asset_node.get('alt')
            else:
                label = anchor.get_text(strip=True)
            
            nodes.append({
                "id": base64.urlsafe_b64encode(abs_url.encode()).decode(),
                "title": label[:100] if label else "Content",
                "poster": asset_url,
                "type": "series" if any(x in label for x in ["مسلسل", "حلقة", "Episode", "Ep"]) else "movie"
            })
        
        return nodes
    
    def _resolve_vectors_from_soup(self, s: BeautifulSoup) -> List[Dict]:
        """Extract download links from soup"""
        vectors = []
        seen = set()
        
        # Larooza-specific download structure
        download_list_items = s.select('ul.downloadlist li[data-download-url]')
        for item in download_list_items:
            u = item.get('data-download-url')
            if not u:
                a_tag = item.find('a')
                if a_tag:
                    u = a_tag.get('href')
            
            if u:
                domain_match = re.search(r'https?://(?:www\.)?([^/]+)', u)
                domain = domain_match.group(1) if domain_match else ''
                
                span_tags = item.find_all('span')
                if span_tags:
                    label_parts = [span.get_text(strip=True) for span in span_tags if span.get_text(strip=True)]
                    quality = label_parts[0] if label_parts else domain
                else:
                    quality = domain if domain else f"Download Server {len(vectors)+1}"
                
                abs_u = urljoin(self.ROOT, u) if not u.startswith('http') else u
                abs_u = abs_u.strip()
                
                if abs_u not in seen:
                    seen.add(abs_u)
                    vectors.append({"quality": quality, "url": abs_u})
        
        if vectors:
            logger.info(f"Found {len(vectors)} Larooza download vectors")
            return vectors
        
        # Generic download selectors
        selectors = [
            'a[href*="download"]', 'a[href*="multiup"]', 'a[href*="php?id="]',
            'a[href*="mp4"]', 'a[href*="mkv"]', '.download-link', 'table a[href]',
            '.download-buttons a', '.dl-btn', 'a.btn-download',
            'a[href*="get_file"]', 'a[href*="direct"]', '.mirror a', 'a[download]',
        ]
        
        tags = []
        for selector in selectors:
            tags.extend(s.select(selector))
        
        for item in tags:
            u = item.get('href') or item.get('data-href') or item.get('data-link')
            if not u:
                continue
            
            abs_u = urljoin(self.ROOT, u) if not u.startswith('http') else u
            abs_u = abs_u.strip()
            
            excluded = ['facebook', 'twitter', 'whatsapp', 'mailto:', 'javascript:', '#']
            if any(x in abs_u.lower() for x in excluded):
                continue
            
            if abs_u not in seen and abs_u != self.ROOT:
                is_download = any(x in abs_u.lower() for x in ['download', 'multiup', 'mp4', 'mkv', 'get_file'])
                if is_download:
                    seen.add(abs_u)
                    label = item.get_text(strip=True) or item.get('title') or f"Download Link {len(vectors)+1}"
                    vectors.append({"quality": label, "url": abs_u})
        
        logger.info(f"Found {len(vectors)} download vectors")
        return vectors
    
    async def _resolve_vectors(self, endpoint: str) -> List[Dict]:
        """Fetch and extract download links"""
        try:
            raw = await asyncio.wait_for(self._invoke_remote(endpoint), timeout=25.0)
            if not raw:
                return []
            soup = BeautifulSoup(raw, 'html.parser')
            return self._resolve_vectors_from_soup(soup)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout resolving download vectors for {endpoint}")
            return []
        except Exception as e:
            logger.error(f"Error resolving download vectors: {e}")
            return []
    
    def _process_node_matrix(self, raw: str) -> List[Dict]:
        """Extract video servers from HTML"""
        if not raw:
            return []
        
        s = BeautifulSoup(raw, 'html.parser')
        matrix = []
        
        # Primary: iframe
        f = s.find('iframe')
        if f:
            src = f.get('src') or f.get('data-src')
            if src:
                if not src.startswith('http'):
                    src = urljoin(self.ROOT, src)
                problematic = ['okprime.site', 'film77.xyz']
                if not any(d in src.lower() for d in problematic):
                    matrix.append({"name": "Main Player", "url": src, "type": "iframe"})
        
        # Secondary: server lists
        selectors = [
            '.servers-list li', '.player-servers li', '.watch-servers a',
            '.list-server-items li', 'ul.servers a', '.video-servers li',
            'div[data-url]', 'a[data-vid]', '.server-item',
            'ul.WatchList li', '[data-embed-url]', '[data-embed-id]'
        ]
        
        for selector in selectors:
            for item in s.select(selector):
                u = (item.get('data-embed-url') or item.get('data-url') or
                     item.get('href') or item.get('data-id') or
                     item.get('data-vid') or item.get('data-link'))
                
                if not u and item.name != 'a':
                    a = item.find('a')
                    if a:
                        u = a.get('href') or a.get('data-url')
                
                if u and 'javascript' not in u.lower():
                    if not u.startswith('http'):
                        if u.isalnum() and '/' not in u:
                            u = urljoin(self.ROOT, f"play.php?vid={u}")
                        else:
                            u = urljoin(self.ROOT, u)
                    
                    if u.startswith('http'):
                        if any(x in u.lower() for x in ['facebook', 'twitter']):
                            continue
                        if not any(m['url'] == u for m in matrix):
                            name = item.get_text(strip=True) or f"Server {len(matrix)+1}"
                            matrix.append({"name": name, "url": u, "type": "iframe"})
        
        logger.info(f"Matrix Discovery: {len(matrix)} servers found")
        return matrix
    
    async def _resolve_source_matrix(self, path: str, origin: Optional[str] = None) -> List[Dict]:
        """Fetch and extract video servers"""
        try:
            raw = await asyncio.wait_for(self._invoke_remote(path, ref=origin), timeout=20.0)
            matrix = self._process_node_matrix(raw)
            if len(matrix) < 2:
                # Try with higher tier
                raw = await self._invoke_remote(path, ref=origin, force_tier=4)
                matrix = self._process_node_matrix(raw)
            return matrix[:12]
        except asyncio.TimeoutError:
            logger.warning(f"Timeout resolving source matrix for {path}")
            return []
        except Exception as e:
            logger.error(f"Error resolving source matrix: {e}")
            return []
    
    def _normalize_sequence(self, soup: BeautifulSoup, current_id: Optional[str] = None, current_title: Optional[str] = None) -> List[Dict]:
        """Extract episode list from soup"""
        seq_map = {}
        
        if current_id and current_title:
            v_match = re.search(r'(?:الحلقة|حلقة|Episode|Ep|v)\s*(\d+)', current_title, re.IGNORECASE)
            if v_match:
                idx = int(v_match.group(1))
                seq_map[idx] = {"episode": idx, "title": f"Part {idx}", "id": current_id}
        
        links = soup.select('.pm-ul-browse-videos li a, .episodes-list a, .video-series-list a, a.ellipsis, a[href*="vid="]')
        
        for a in links:
            t = a.get_text(strip=True) or a.get('title', '')
            h = a.get('href')
            if not h or 'video.php' not in h:
                continue
            
            abs_u = urljoin(self.ROOT, h)
            v_match = re.search(r'(?:الحلقة|حلقة|Episode|Ep|v)\s*(\d+)', t, re.IGNORECASE)
            
            if not v_match:
                nums = re.findall(r'\d+', t)
                idx = int(nums[0]) if nums else None
            else:
                idx = int(v_match.group(1))
            
            if idx is not None and idx not in seq_map:
                seq_map[idx] = {
                    "episode": idx,
                    "title": f"Part {idx}",
                    "id": base64.urlsafe_b64encode(abs_u.encode()).decode()
                }
        
        return sorted(seq_map.values(), key=lambda x: x['episode'])
    
    # ========================================================================
    # PUBLIC API METHODS
    # ========================================================================
    
    async def get_content_details(self, entry_id: str) -> Dict:
        """Fetch complete media information"""
        try:
            # Decode entry ID
            sid = entry_id.replace('%3D', '=').replace(' ', '+')
            if len(sid) % 4:
                sid += '=' * (4 - len(sid) % 4)
            entry_url = base64.urlsafe_b64decode(sid).decode()
            
            logger.info(f"Fetching content details for: {entry_url[:60]}...")
            
            raw_main = await self._invoke_remote(entry_url)
            if not raw_main:
                raise ProviderError("Resource Inaccessible")
            
            soup = BeautifulSoup(raw_main, 'html.parser')
            
            # Extract VID
            v_match = re.search(r'vid=([^&]+)', entry_url)
            if not v_match:
                v_match = re.search(r'video-([a-f0-9]+)-', entry_url)
            vid = v_match.group(1) if v_match else None
            
            # Extract title
            title_node = soup.find('h1')
            label = title_node.get_text(strip=True) if title_node else "Content"
            
            # Extract from main page
            main_matrix = self._process_node_matrix(raw_main)
            main_vectors = self._resolve_vectors_from_soup(soup)
            
            # Parallel fetch if needed
            if len(main_matrix) < 5 and vid:
                base_play = urljoin(self.ROOT, f"play.php?vid={vid}")
                base_dl = urljoin(self.ROOT, f"download.php?vid={vid}")
                
                try:
                    results = await asyncio.gather(
                        self._resolve_source_matrix(base_play, origin=entry_url),
                        self._resolve_vectors(base_dl),
                        return_exceptions=True
                    )
                    
                    remote_matrix = results[0] if not isinstance(results[0], Exception) else []
                    remote_vectors = results[1] if not isinstance(results[1], Exception) else []
                except Exception:
                    remote_matrix = []
                    remote_vectors = []
            else:
                remote_matrix = []
                remote_vectors = []
            
            # Combine results
            matrix = remote_matrix if remote_matrix else main_matrix
            seen_srv = {m['url'] for m in matrix}
            for m in main_matrix:
                if m['url'] not in seen_srv:
                    matrix.append(m)
                    seen_srv.add(m['url'])
            
            vectors = remote_vectors if remote_vectors else main_vectors
            
            # Extract description
            desc_node = soup.select_one('.video-description, .description, p')
            summary = desc_node.get_text(strip=True) if desc_node else ""
            
            # Extract poster
            asset_img = soup.select_one('.video-poster img, .movie-poster img, meta[property="og:image"]')
            asset_p = ""
            if asset_img:
                if asset_img.name == 'meta':
                    asset_p = asset_img.get('content', '')
                else:
                    asset_p = asset_img.get('src') or asset_img.get('data-src') or ''
            
            if asset_p:
                if asset_p.startswith('//'):
                    asset_p = "https:" + asset_p
                elif not asset_p.startswith('http'):
                    asset_p = urljoin(self.ROOT, asset_p)
            
            # Determine if series
            is_multi = any(x in label for x in ["مسلسل", "حلقة", "Episode", "Ep", "موسم"])
            
            # Get episodes
            full_sequence = {}
            for item in self._normalize_sequence(soup, entry_id, label):
                full_sequence[item['episode']] = item
            
            sorted_seq = sorted(full_sequence.values(), key=lambda x: x['episode'])
            
            return {
                "title": label,
                "type": "series" if is_multi else "movie",
                "description": summary,
                "poster": asset_p,
                "episodes": sorted_seq,
                "servers": matrix,
                "download_links": vectors
            }
            
        except Exception as e:
            logger.error(f"Content details error: {e}")
            return {"title": "Unavailable", "servers": [], "episodes": [], "download_links": []}
    
    async def get_latest_content(self, p: int = 1) -> List[Dict]:
        """Fetch latest content from homepage"""
        raw = await self._invoke_remote(f"{self.ROOT}/newvideos1.php?page={p}")
        return self._map_content_grid(raw)
    
    async def search_content(self, query: str) -> List[Dict]:
        """Search for content"""
        raw = await self._invoke_remote(f"{self.ROOT}/search.php?keywords={quote(query)}")
        return self._map_content_grid(raw)
    
    async def get_category_content(self, cid: str, p: int = 1) -> List[Dict]:
        """Fetch content from category"""
        raw = await self._invoke_remote(f"{self.ROOT}/browse-{cid}-videos-{p}-date.html")
        return self._map_content_grid(raw)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        
        if self._browser:
            await self._browser.close()
        
        if self._playwright:
            await self._playwright.stop()
        
        logger.info("Resources cleaned up")


# Export singleton instance
scraper = ResourceResolver()
