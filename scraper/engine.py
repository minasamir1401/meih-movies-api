# Production-Ready Hybrid Scraping Engine
#
# Multi-Tier Fallback Architecture:
#   Tier 1: Direct HTTP request (httpx) - fastest, works when no protection
#   Tier 2: curl_cffi with browser impersonation - bypasses TLS fingerprinting
#   Tier 3: ScraperAPI proxy - when direct/curl fail (rate limited)
#   Tier 4: Node.js Stealth Proxy - browser-like headers without browser overhead
#
# Intelligent Detection:
#   - 403 Forbidden -> escalate to next tier
#   - JavaScript challenge -> escalate to Node.js proxy
#   - Empty/short HTML -> escalate to render mode
#   - Cloudflare/WAF -> use stealth headers
#
# Windows Compatibility:
#   - Proper asyncio event loop policy
#   - Non-blocking async operations

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
import aiohttp

import os
os.environ['UVLOOP'] = '0'

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
    # Use SelectorEventLoop to avoid uvloop issues
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
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
    # Custom exception for scraping errors
    def __init__(self, message: str, status_code: int = None, tier: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.tier = tier


class DiscoveryCache:
    # Thread-safe LRU cache with TTL expiration
    
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
    # Production-ready hybrid scraping engine with intelligent fallback.
    
    # SCRAPING FLOW:
    # +---------------------------------------------------------------+
    # |                       SCRAPING REQUEST                          |
    # +-------------------------------+-------------------------------+
    #                                 |
    #                                 v
    # +---------------------------------------------------------------+
    # | TIER 1: Direct HTTP (httpx)                                   |
    # | - Fastest option, no external dependencies                     |
    # | - Works when target has no anti-bot protection                 |
    # +-------------------------------+-------------------------------+
    #                                 | 403/Challenge detected?
    #                                 v
    # +---------------------------------------------------------------+
    # | TIER 2: curl_cffi (TLS Fingerprint Bypass)                    |
    # | - Impersonates real browser TLS fingerprint                   |
    # | - Bypasses basic fingerprinting protection                    |
    # +-------------------------------+-------------------------------+
    #                                 | Still blocked?
    #                                 v
    # +---------------------------------------------------------------+
    # | TIER 3: ScraperAPI Proxy (if credits available)               |
    # | - Rotates IP addresses automatically                          |
    # | - Handles CAPTCHAs and challenges                             |
    # +-------------------------------+-------------------------------+
    #                               | JS rendering needed?
    #                               v
    # +---------------------------------------------------------------+
    # | TIER 4: Node.js Stealth Proxy                                 |
    # | - Browser-like headers without browser overhead               |
    # | - Lightweight alternative to headless browser                 |
    # +---------------------------------------------------------------+
    
    # Provider domains (configurable via environment)
    # Updated domains for Larooza (Discovery Nodes)
    NET_NODES = os.getenv("NETWORK_NODES", "https://larooza.site,https://larooza.video,https://larooza.net,https://larooza.tv,https://larooza.icu,https://q.larozavideo.net").split(',')
    
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
        # HTTP clients (shared sessions for stability and speed)
        self._shared_session = None
        self._concurrency_limit = 30 # High concurrency for detail fetching
        self.concurrency = asyncio.Semaphore(self._concurrency_limit)
        self.store = DiscoveryCache(capacity=2000) # Larger cache for fast UI
        
        # Monitoring statistics
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
        # Update monitoring statistics
        if key in self.stats:
            self.stats[key] += increment
    
    def get_stats(self) -> Dict:
        # Get current monitoring statistics with computed metrics
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
        # Rotate to next provider domain
        self.node_idx = (self.node_idx + 1) % len(self.NET_NODES)
        self.ROOT = self.NET_NODES[self.node_idx]
        logger.info(f"Cycled to node: {self.ROOT}")
    
    def _generate_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        # Generate realistic browser headers
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
        # Detect if response indicates blocking/protection.
        if status_code in [403, 429]:
            return True, f"HTTP {status_code}"
        
        if status_code == 503 and ("cloudflare" in content.lower() or "ddos-guard" in content.lower()):
            return True, "WAF Protection Active (503)"

        if not content or len(content) < 100: # Reduced threshold to catch smaller valid responses
            return True, f"Empty or tiny content ({len(content) if content else 0} bytes)"
        
        content_lower = content.lower()[:3000] # Check more of the content
        
        # Priority check for Cloudflare specific challenges
        if "just a moment" in content_lower or "checking your browser" in content_lower:
            return True, "Cloudflare JS Challenge"
            
        if "access denied" in content_lower and "cloudflare" in content_lower:
            return True, "Cloudflare Access Denied"

        # If we see common UI elements, it's NOT blocked even if some patterns match
        if any(x in content_lower for x in ['video-item', 'post-title', 'ellipsis', 'play.php', 'vid=']):
            return False, ""

        return False, ""
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._shared_session is None or self._shared_session.closed:
            connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300, use_dns_cache=True, ssl=False)
            # Reliable timeout for multi-tier fallbacks
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            self._shared_session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._shared_session

    async def _tier1_direct(self, url: str, headers: Dict) -> Tuple[Optional[str], int]:
        try:
            session = await self._get_session()
            # Fast fail for direct connections
            async with session.get(url, headers=headers, ssl=False, timeout=5) as response:
                text = await response.text()
                # Follow meta refresh redirects if present
                if text and '<meta' in text.lower():
                    text = await self._follow_meta_refresh(text, url)
                return text, response.status
        except Exception:
            return None, 0
    
    async def _tier2_curl_cffi(self, url: str) -> Tuple[Optional[str], int]:
        # TIER 2: curl_cffi with browser TLS fingerprint impersonation.
        # Bypasses TLS fingerprinting protection.
        # Only available if curl_cffi is installed.
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
        # TIER 3: ScraperAPI proxy service with aiohttp
        if not self.token:
            return None, 0
        
        try:
            proxy = f"http://scraperapi:{self.token}@proxy-server.scraperapi.com:8001"
            if render:
                proxy = f"http://scraperapi.render=true:{self.token}@proxy-server.scraperapi.com:8001"
                
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=proxy, timeout=45, ssl=False) as response:
                    text = await response.text()
                    return text, response.status
        except Exception as e:
            logger.warning(f"Tier 3 error for {url}: {e}")
            return None, 0
    
    async def _tier4_node_proxy(self, url: str, timeout: int = 45000) -> Tuple[Optional[str], int]:
        # TIER 4: Node.js Stealth Proxy with meta-redirect tracking
        proxy_url = os.environ.get('NODE_PROXY_URL', 'http://localhost:3001')
        try:
            session = await self._get_session()
            async with session.post(
                f"{proxy_url}/fetch",
                json={"url": url, "timeout": timeout},
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    html = data.get('html', '')
                    status = data.get('status', 0)
                    
                    if html and len(html) > 500:
                        # Follow meta refresh redirects often used by Larooza
                        if '<meta' in html.lower() and 'refresh' in html.lower():
                            refresh_match = re.search(r'url=([^"\'>]+)', html, re.IGNORECASE)
                            if refresh_match:
                                redirect_u = refresh_match.group(1).strip()
                                if not redirect_u.startswith('http'):
                                    redirect_u = urljoin(url, redirect_u)
                                return await self._tier4_node_proxy(redirect_u, timeout)
                        return html, status
                return None, response.status
        except Exception:
            return None, 0
    
    def _heal_url(self, url: str) -> str:
        """Robustly redirect any Larooza-related domain to the current active ROOT"""
        if not url: return url
        
        # Domains to be healed
        targets = ['larooza', 'laroza', 'aflam3isk', 'larozavideo']
        if any(t in url.lower() for t in targets):
            parsed = urlparse(url)
            # Ensure the netloc points to our current ROOT domain
            root_netloc = urlparse(self.ROOT).netloc
            current_netloc = parsed.netloc
            if current_netloc and current_netloc != root_netloc:
                # Specialized handling for q.larozavideo.net and similar subdomains
                # We want to redirect everything to the main active ROOT
                new_url = self.ROOT.rstrip('/') + (parsed.path if parsed.path.startswith('/') else '/' + parsed.path)
                if parsed.query:
                    new_url += f"?{parsed.query}"
                return new_url
        return url

    async def _follow_meta_refresh(self, html_content: str, original_url: str) -> str:
        """Follow meta refresh redirects in HTML content"""
        if not html_content or '<meta' not in html_content.lower():
            return html_content
        
        # Look for meta refresh tags
        meta_refresh_match = re.search(r'<meta[^>]*http-equiv=["\']?refresh["\']?[^>]*content=["\']?\d+;\s*url=([^"\'>]+)["\']?', html_content, re.IGNORECASE)
        if meta_refresh_match:
            refresh_url = meta_refresh_match.group(1).strip()
            # Make URL absolute if it's relative
            if not refresh_url.startswith('http'):
                refresh_url = urljoin(original_url, refresh_url)
            
            # Fetch the redirected content
            try:
                headers = self._generate_headers(original_url)
                session = await self._get_session()
                async with session.get(refresh_url, headers=headers, ssl=False, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
            except Exception as e:
                logger.warning(f"Failed to follow meta refresh redirect to {refresh_url}: {e}")
        
        return html_content

    async def _invoke_remote(self, endpoint: str, ref: Optional[str] = None, force_tier: int = 0) -> str:
        # 0. Heal URL before requesting
        endpoint = self._heal_url(endpoint)
        
        # 1. Check cache first
        cached = self.store.get(endpoint)
        if cached:
            self._update_stats('cache_hits')
            return cached
        
        # Performance Jitter (Minized for speed)
        if not endpoint.startswith(self.ROOT):
             await asyncio.sleep(random.uniform(0.01, 0.05))
        
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
                
                # Check for empty or blocked content even if 200 OK
                if content and status_code == 200:
                    is_blocked, reason = self._is_blocked(content, status_code)
                    if not is_blocked and len(content) > 500: # Ensure substantial content
                        self._update_stats('tier1_success')
                        successful_tier = 1
                    else:
                        logger.info(f"[TIER 1] Blocked or Empty ({len(content)}b): {reason if is_blocked else 'Insufficient Length'}")
                        content = None # Force escalation
                else:
                    logger.info(f"[TIER 1] Failed with status {status_code}")
                    content = None
            
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
            
            # TIER 4: Node.js Proxy
            if not content and (force_tier == 0 or force_tier == 4):
                node_proxy = os.environ.get('NODE_PROXY_URL', 'http://localhost:3001')
                logger.info(f"[TIER 4] Node.js proxy fetch ({node_proxy}): {endpoint[:60]}...")
                content, status_code = await self._tier4_node_proxy(endpoint)
                
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
        # Extract content items from grid/list pages
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        nodes = []
        seen_uids = set()
        
        # Expanded discovery selectors for the new domain design
        grids = soup.select('li.col-sm-4, li.col-sm-3, .pm-li-video, .video-item, article, .col-md-3, .postBlock, .movie-item, .item, .video-block')
        
        for node in grids:
            anchor = node.select_one('a.ellipsis, a[href*="video.php"], a[href*=".html"], a.title, .post-title a')
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
        # Extract download links from soup
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
        # Fetch and extract download links
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
    
    def _process_node_matrix(self, raw: str, current_vid: Optional[str] = None) -> List[Dict]:
        """Deep video server discovery using structural analysis and regex"""
        if not raw: return []
        
        s = BeautifulSoup(raw, 'html.parser')
        matrix = []
        seen_urls = set()

        def add_server(url: str, name: str = ""):
            if not url or 'javascript' in url.lower(): return
            
            # Heal and absolute
            url = self._heal_url(url)
            if not url.startswith('http'):
                if len(url) > 5 and len(url) < 20 and not '/' in url: # Likely a VID
                    # Only add if it's the requested VID OR we don't have a specific VID context
                    if current_vid and url != current_vid:
                         return
                    url = urljoin(self.ROOT, f"play.php?vid={url}")
                else:
                    url = urljoin(self.ROOT, url)
            
            # Filter unrelated videos if we have a current_vid
            if current_vid and 'vid=' in url and current_vid not in url:
                # Keep only if it's a known cloud provider even if it has a vid param
                if not any(x in url.lower() for x in ['vidoza', 'streamtape', 'doodstream', 'ok.ru', 'upstream']):
                    return

            # Filter social/ads
            if any(x in url.lower() for x in ['facebook', 'twitter', 'google', 'ad-network', 'contact', 'about']):
                 return
            
            if url not in seen_urls:
                seen_urls.add(url)
                # Clean name
                clean_name = name.split('\n')[0].strip()[:20] or f"Server {len(matrix)+1}"
                matrix.append({"name": clean_name, "url": url, "type": "iframe"})

        # 1. Direct Iframes
        for f in s.find_all('iframe'):
            src = f.get('src') or f.get('data-src') or f.get('data-lazy-src')
            if src: add_server(src, "Main Server")

        # 2. Structural Server Lists
        selectors = [
            '.servers-list li', '.player-servers li', '.watch-servers a',
            '.list-server-items li', 'ul.servers a', '.video-servers li',
            'div[data-url]', 'a[data-vid]', '.server-item',
            'ul.WatchList li', '[data-embed-url]', '[data-embed-id]',
            '.server-link', '.sv-item', '.play-btn', '.video-source',
            '.servers-div li', '.servers a', '.p-servers li', '.v-server',
            '.server-box', 'a.server-li', '.server-tab a'
        ]

        for selector in selectors:
            for item in s.select(selector):
                # Try all common attributes
                u = (item.get('data-embed-url') or item.get('data-url') or
                     item.get('href') or item.get('data-id') or
                     item.get('data-vid') or item.get('data-link') or
                     item.get('data-src') or item.get('src'))
                
                # Check for onclick pattern: loadVideo('ID')
                oc = item.get('onclick', '')
                if not u and oc:
                    v_match = re.search(r"loadVideo\(['\"]?([^'\"]+)['\"]?\)", oc)
                    if v_match: u = v_match.group(1)

                if not u and item.name != 'a':
                    a = item.find('a')
                    if a: u = a.get('href') or a.get('data-url')

                if u: add_server(u, item.get_text(strip=True))

        # 3. Script & Text Scanning (Deep Discovery)
        # Search for play.php?vid= patterns
        vids = re.findall(r'(?:play\.php\?vid=|id=|vid=)([a-zA-Z0-9]{5,15})', raw)
        for v in vids:
            # If we have a current_vid, only add if it matches
            if current_vid and v != current_vid:
                continue
            add_server(f"play.php?vid={v}", f"Main Mirror")
        
        # Search for raw embed URLs
        embeds = re.findall(r'[\'"](https?://[^\'"]+(?:vidoza|streamtape|doodstream|ok\.ru|feurl|upstream|uqload|vidmoly|voe\.sx|mixdrop|streamvid)[^\'"]+)[\'"]', raw)
        for e_match in embeds:
            url = e_match[0] if isinstance(e_match, tuple) else e_match
            # Detect provider name from URL
            provider = "Cloud"
            for p in ['vidoza', 'streamtape', 'doodstream', 'ok.ru', 'uqload', 'vidmoly', 'voe', 'mixdrop']:
                if p in url.lower():
                    provider = p.capitalize()
                    break
            add_server(url, f"{provider} Server")

        logger.info(f"[SCRAPER] Matrix Discovery: {len(matrix)} servers found for {self.ROOT}")
        return matrix[:20] # Limit to top 20 for performance
    
    async def _resolve_source_matrix(self, path: str, origin: Optional[str] = None) -> List[Dict]:
        # Fetch and extract video servers
        try:
            raw = await asyncio.wait_for(self._invoke_remote(path, ref=origin), timeout=20.0)
            # Extract VID from path if possible for filtering
            v_match = re.search(r'vid=([^&]+)', path)
            target_vid = v_match.group(1) if v_match else None
            matrix = self._process_node_matrix(raw, current_vid=target_vid)
            if len(matrix) < 2:
                # Try with higher tier
                raw = await self._invoke_remote(path, ref=origin, force_tier=4)
                matrix = self._process_node_matrix(raw, current_vid=target_vid)
            return matrix[:12]
        except asyncio.TimeoutError:
            logger.warning(f"Timeout resolving source matrix for {path}")
            return []
        except Exception as e:
            logger.error(f"Error resolving source matrix: {e}")
            return []
    
    def _normalize_sequence(self, soup: BeautifulSoup, current_id: Optional[str] = None, current_title: Optional[str] = None) -> List[Dict]:
        """Enhanced episode discovery with advanced numbering and deduplication"""
        seq_map = {}
        
        # 1. Self-reference handling
        if current_id and current_title:
            # Map Arabic ordinals to numbers
            clean_t = current_title
            ordinals = {
                'الاولى': '1', 'الثانية': '2', 'الثالثة': '3', 'الرابعة': '4', 'الخامسة': '5',
                'السادسة': '6', 'السابعة': '7', 'الثامنة': '8', 'التاسعة': '9', 'العاشرة': '10',
                'الحادية عشر': '11', 'الثانية عشر': '12', 'الثالثة عشر': '13', 'الرابعة عشر': '14',
                'الخامسة عشر': '15', 'السادسة عشر': '16', 'السابعة عشر': '17', 'الثامنة عشر': '18',
                'التاسعة عشر': '19', 'العشرون': '20', 'الحادية والعشرون': '21', 'الثانية والعشرون': '22',
                'الاخيرة': '999'
            }
            for k, v in ordinals.items():
                clean_t = clean_t.replace(k, v)
                
            v_match = re.search(r'(?:الحلقة|حلقة|Episode|Ep|v|part|p)\s*(\d+)', clean_t, re.IGNORECASE)
            if v_match:
                idx = int(v_match.group(1))
                seq_map[idx] = {"episode": idx, "title": f"الحلقة {idx}", "id": current_id}

        # 2. Extract from listed elements
        # Broaden selectors for different site versions
        selectors = [
            '.pm-ul-browse-videos li a', '.episodes-list a', '.video-series-list a', 
            'a.ellipsis', 'a[href*="vid="]', '.eps-list a', '.series-episodes a',
            '.movies-list .movie-item a', '.episodes-grid a', '.col-6 a', '.col-4 a', '.col-3 a',
            'div[class*="episode"] a'
        ]
        
        for selector in selectors:
            for a in soup.select(selector):
                t = a.get_text(strip=True) or a.get('title', '')
                h = a.get('href')
                if not h or ('video.php' not in h and 'series.php' not in h):
                    continue
                
                abs_u = urljoin(self.ROOT, h)
                
                # Intelligent numbering with Arabic support
                clean_t = t
                ordinals = {
                    'الاولى': '1', 'الثانية': '2', 'الثالثة': '3', 'الرابعة': '4', 'الخامسة': '5',
                    'السادسة': '6', 'السابعة': '7', 'الثامنة': '8', 'التاسعة': '9', 'العاشرة': '10',
                    'الحادية عشر': '11', 'الثانية عشر': '12', 'الثالثة عشر': '13', 'الرابعة عشر': '14',
                    'الخامسة عشر': '15', 'السادسة عشر': '16', 'السابعة عشر': '17', 'الثامنة عشر': '18',
                    'التاسعة عشر': '19', 'العشرون': '20', 'الحادية والعشرون': '21', 'الثانية والعشرون': '22',
                    'الاخيرة': '999'
                }
                for k, v in ordinals.items():
                    clean_t = clean_t.replace(k, v)
                    
                v_match = re.search(r'(?:الحلقة|حلقة|Episode|Ep|v|part|p)\s*(\d+)', clean_t, re.IGNORECASE)
                
                if not v_match:
                    nums = re.findall(r'\d+', clean_t)
                    idx = int(nums[0]) if nums else None
                else:
                    idx = int(v_match.group(1))
                
                if idx is not None:
                    # Prefer existing entry if it's the current page (more accurate)
                    if idx in seq_map and seq_map[idx]['id'] == current_id:
                        continue
                    
                    seq_map[idx] = {
                        "episode": idx,
                        "title": f"الحلقة {idx}",
                        "id": base64.urlsafe_b64encode(abs_u.encode()).decode()
                    }
        
        # 3. Sort numerically to ensure correct order
        return sorted(seq_map.values(), key=lambda x: x['episode'])
    
    # ========================================================================
    # PUBLIC API METHODS
    # ========================================================================
    
    async def get_content_details(self, entry_id: str) -> Dict:
        # Fetch complete media information
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
            
            # Extract title with higher precision
            title_node = soup.find('h1')
            meta_title = soup.find('meta', property='og:title') or soup.find('meta', name='twitter:title')
            if meta_title and meta_title.get('content'):
                label = meta_title['content'].split('|')[0].split('-')[0].strip()
            elif title_node:
                label = title_node.get_text(strip=True)
            else:
                label = soup.title.get_text(strip=True) if soup.title else "Content"
            
            # Clean title for common suffixes
            for suffix in ["فيديو لاروزا", "لاروزا فيديو", "لاروزا تي في", "Laroza"]:
                label = label.replace(suffix, "").strip(" -|")
            
            # Extract from main page
            main_matrix = self._process_node_matrix(raw_main, current_vid=vid)
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
            desc_node = soup.select_one('.video-description, .description, p, meta[name="description"]')
            if desc_node and desc_node.name == 'meta':
                 summary = desc_node.get('content', '')
            else:
                 summary = desc_node.get_text(strip=True) if desc_node else ""
            
            # Extract poster
            asset_img = soup.select_one('.video-poster img, .movie-poster img, .postBlock img, .post-thumbnail img, .single-poster img, meta[property="og:image"], meta[name="twitter:image"]')
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
            
            # 1. Initial Episode Scan
            full_sequence = {}
            for item in self._normalize_sequence(soup, entry_id, label):
                full_sequence[item['episode']] = item
            
            # 2. Determine if series (Deep check)
            is_multi = any(x in label for x in ["مسلسل", "حلقة", "Episode", "Ep", "موسم", "كارتون"]) or len(full_sequence) > 1
            
            # 3. Recursive Discovery for missing episodes
            # ALWAYS fetch series page to ensure complete list (play pages often show limited sidebar)
            if is_multi:
                series_link = soup.select_one('a[href*="series.php"], .series-all a, .breadcrumb a[href*="series"], .video-info a[href*="series"]')
                if series_link:
                    logger.info(f"Fetching full series list from: {series_link['href']}")
                    raw_series = await self._invoke_remote(urljoin(self.ROOT, series_link['href']))
                    if raw_series:
                        soup_s = BeautifulSoup(raw_series, 'html.parser')
                        # Merge episodes, preferring the ones we just found as they are from the master list
                        for item in self._normalize_sequence(soup_s, entry_id, label):
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
        target_path = f"newvideos1.php?page={p}"
        raw = await self._invoke_remote(f"{self.ROOT}/{target_path}")
        
        # Fallback 1: Try newvideos.php
        if not raw and p == 1:
            raw = await self._invoke_remote(f"{self.ROOT}/newvideos.php")
            
        # Fallback 2: Try ROOT directly for page 1
        if not raw and p == 1:
            raw = await self._invoke_remote(self.ROOT)
            
        return self._map_content_grid(raw)
    
    async def search_content(self, query: str) -> List[Dict]:
        # Search for content
        raw = await self._invoke_remote(f"{self.ROOT}/search.php?keywords={quote(query)}")
        return self._map_content_grid(raw)
    
    async def get_category_content(self, cid: str, p: int = 1) -> List[Dict]:
        # Pattern 1: Classic Larooza
        url1 = f"{self.ROOT}/browse-{cid}-videos-{p}-date.html"
        # Pattern 2: Search-like CID or category.php
        url2 = f"{self.ROOT}/category.php?cat={cid}&page={p}"
        
        raw = await self._invoke_remote(url1)
        if not raw:
            raw = await self._invoke_remote(url2)
            
        return self._map_content_grid(raw)
    
    async def cleanup(self):
        # Cleanup resources
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        
        logger.info("Resources cleaned up")

# Export singleton instance
scraper = ResourceResolver()
