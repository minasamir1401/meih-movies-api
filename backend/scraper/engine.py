import asyncio
import httpx
import re
import logging
import base64
import random
import os
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from urllib.parse import urljoin, quote
from scraper.proxy_fetcher import proxy_fetcher
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Clean, strictly used logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper")

class LaroozaScraper:
    MIRRORS = ["https://q.larozavideo.net", "https://larooza.mom", "https://larooza.site", "https://m.laroza-tv.net"]
    BASE_URL = "https://q.larozavideo.net"
    TARGET_URL = "https://q.larozavideo.net/newvideos1.php"
    _blacklisted_mirrors = {}

    # Permanent Aliases -> Keywords search
    CATEGORY_KEYWORDS = {
        "arabic-movies": ["أفلام عربية", "افلام عربية", "افلام عربي", "arabic-movies33"],
        "english-movies": ["افلام اجنبية", "أفلام أجنبية", "افلام اجنبي", "أجنبي", "all_movies_13"],
        "indian-movies": ["افلام هندي", "أفلام هندية", "هندي", "indian-movies9"],
        "anime-movies": ["افلام انمي", "أفلام أنمي", "انمي", "anime-movies-7"],
        "dubbed-movies": ["افلام مدبلجة", "أفلام مدبلجة", "مدبلج", "7-aflammdblgh"],
        "turkish-series": ["مسلسلات تركية", "تركي", "turkish-3isk-seriess47"],
        "arabic-series": ["مسلسلات عربية", "عربي", "arabic-series46"],
        "english-series": ["مسلسلات اجنبية", "أجنبي", "english-series10"],
        "ramadan-2025": ["رمضان 2025", "13-ramadan-2025"],
        "ramadan-2024": ["رمضان 2024", "28-ramadan-2024"],
        "ramadan-2023": ["رمضان 2023", "10-ramadan-2023"],
        "asian-movies": ["آسيوي", "اسيوي", "آسيوية", "6-asian-movies"],
        "asian-series": ["مسلسلات اسياوية", "اسياوية", "6-asya"],
        "turkish-movies": ["افلام تركية", "أفلام تركية", "8-aflam3isk"],
        "anime-series": ["مسلسلات انمي", "كرتون", "6-anime-series"],
        "indian-series": ["مسلسلات هندية", "11indian-series"],
        "tv-programs": ["برامج تلفزيون", "tv-programs12"],
        "plays": ["مسرحيات", "masrh-5"]
    }

    # Manual Fallbacks for reliability
    HARDCODED_FALLBACKS = {
        "arabic-movies": "arabic-movies33",
        "english-movies": "all_movies_13",
        "indian-movies": "indian-movies9",
        "asian-movies": "6-asian-movies",
        "anime-movies": "anime-movies-7",
        "dubbed-movies": "7-aflammdblgh",
        "turkish-movies": "8-aflam3isk",
        "arabic-series": "arabic-series46",
        "ramadan-2025": "13-ramadan-2025",
        "ramadan-2024": "28-ramadan-2024",
        "ramadan-2023": "10-ramadan-2023",
        "english-series": "english-series10",
        "turkish-series": "turkish-3isk-seriess47",
        "indian-series": "11indian-series",
        "tv-programs": "tv-programs12",
        "plays": "masrh-5",
        "anime-series": "6-anime-series",
        "asian-series": "6-asya"
    }

    def __init__(self):
        # Primary fetcher: curl-cffi (Fastest, TLS Impersonation)
        # Using chrome120 and disabling SSL verify for maximum compatibility
        self.session = AsyncSession(impersonate="chrome120", timeout=30, verify=False) 
        self._cookies_synced = False
        self._last_pw_solve = 0
        self._ua_synced = None
        self._chrome_version = None
        self._domain_lock = asyncio.Lock()
        self._warming_lock = asyncio.Lock()
        self._proxy_refresh_interval = 1800  # 30 minutes
        self._semaphore = asyncio.Semaphore(5) # Reduced from 15 for stability
        self._optimization_started = False
        
        # Hybrid Configuration
        self.REMOTE_SOLVER_URL = "https://meih-movies-api.onrender.com/remote-fetch"
        self.IS_RENDER = os.environ.get("RENDER") is not None
        self.IS_HUGGINGFACE = os.environ.get("SPACE_ID") is not None
        
        # Free Proxy Pool for Hugging Face (to bypass IP bans)
        self._free_proxy_pool = []
        self._proxy_pool_last_refresh = 0
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
        }
        self._session_initialized = False
        self._session_warmed_at = 0
        self._httpx_client = None 
        
        # --- Proxy Rotation System ---
        proxy_str = os.getenv("PROXY_LIST", "")
        self.proxies = [p.strip() for p in proxy_str.split(",") if p.strip()]
        self._current_proxy_idx = 0
        if self.proxies:
            logger.info(f"✓ Proxy rotation enabled with {len(self.proxies)} endpoints")
        self._category_map = {}
        self._last_discovery = 0
        self._discovery_lock = asyncio.Lock()
        
        # --- Mirror & Performance ---
        self._cache = {} # {url: (timestamp, data)}
        self._cache_ttl = 3600 # 1 hour for data
        self._free_proxies = []
        self._optimization_started = False
        self._uc_lock = asyncio.Lock()
        self._solver_lock = asyncio.Lock() # Guard against multiple solvers
        
        # We'll start optimization on the first request to avoid "no running loop" error
    
    async def _optimize_connection(self):
        """Find the fastest mirror and warm up the engine"""
        logger.info("🔍 Testing mirror speeds in parallel...")
        
        results = []
        async def test_mirror(mirror):
            try:
                start = time.time()
                # Use a specific endpoint for speed tests to ensure path exists
                test_url = f"{mirror}/newvideos1.php"
                async with httpx.AsyncClient(timeout=3.0, follow_redirects=True, verify=False) as client:
                    resp = await client.get(test_url)
                    if resp.status_code == 200:
                        duration = time.time() - start
                        return (duration, mirror)
            except:
                pass
            return (999, mirror)

        results = await asyncio.gather(*(test_mirror(m) for m in self.MIRRORS))
        results.sort()
        
        min_time, fastest_mirror = results[0]
        
        if min_time < 999:
            logger.info(f"⚡ Fastest mirror: {fastest_mirror} ({min_time:.2f}s)")
            # Use the fastest mirror, but keep q.larozavideo.net as secondary fallback
            self.BASE_URL = fastest_mirror
            self.TARGET_URL = f"{fastest_mirror}/newvideos1.php"
        else:
            logger.warning("⚠️ No mirrors responded quickly, using default.")
        
        # Trigger first solve
        await self.fetch_home(1)
    
    async def _refresh_free_proxies(self):
        """Fetch free proxies from public APIs (for cloud deployments)"""
        # Enable on both Hugging Face and Render.com
        if not (self.IS_HUGGINGFACE or self.IS_RENDER):
            return
        
        now = time.time()
        if now - self._proxy_pool_last_refresh < 300:  # Refresh every 5 minutes
            return
        
        logger.info("🔄 Refreshing free proxy pool...")
        self._proxy_pool_last_refresh = now
        
        proxy_sources = [
            "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
        ]
        
        new_proxies = []
        for source in proxy_sources:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(source)
                    if resp.status_code == 200:
                        proxies = resp.text.strip().split('\n')
                        for proxy in proxies[:10]:  # Take first 10 from each source
                            proxy = proxy.strip()
                            if proxy and ':' in proxy:
                                new_proxies.append(f"http://{proxy}")
            except Exception as e:
                logger.warning(f"Failed to fetch proxies from {source}: {e}")
        
        if new_proxies:
            self._free_proxy_pool = new_proxies
            logger.info(f"✅ Loaded {len(new_proxies)} free proxies")
        else:
            logger.warning("⚠️ No free proxies available")

    async def _discover_categories(self, force=False):
        """Build the category map dynamically from the homepage"""
        async with self._discovery_lock:
            if not force and time.time() - self._last_discovery < 3600: # Cache for 1 hour
                return

            logger.info("Refreshing category mapping...")
            html = await self._get_html(self.BASE_URL)
            if not html: return

            soup = BeautifulSoup(html, 'html.parser')
            new_map = {}
            
            # Find all category links
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'cat=' not in href: continue
                
                cat_id = href.split('cat=')[-1].split('&')[0]
                text = a.get_text(strip=True).lower()
                
                # Match against keywords
                for alias, keywords in self.CATEGORY_KEYWORDS.items():
                    if alias not in new_map:
                        if any(k in text for k in keywords):
                            new_map[alias] = cat_id
            
            if new_map:
                self._category_map = new_map
                self._last_discovery = time.time()
                logger.info(f"✓ Mapped {len(new_map)} categories: {new_map}")

    async def _resolve_cat_id(self, cat_id: str) -> str:
        """Resolves an alias to a real ID, or returns the original if not an alias"""
        await self._discover_categories()
        # 1. Check dynamic map
        if cat_id in self._category_map:
            return self._category_map[cat_id]
        
        # 2. Check hardcoded fallbacks if dynamic failed
        if cat_id in self.HARDCODED_FALLBACKS:
            return self.HARDCODED_FALLBACKS[cat_id]
        
        return cat_id

    async def _warm_session(self):
        """Warm up session with the detected working mirror"""
        if not self._domain_detected:
            # We already set defaults in __init__ / class, just confirm
            logger.info(f"🚀 Targeting exclusive source: {self.TARGET_URL}")
            self._domain_detected = True

        if not self._session_initialized:
            self._session_initialized = True # Mark as init even if basic get fails, as PW will solve it

    async def _refresh_free_proxies(self):
        """Refresh free proxy list if needed"""
        if time.time() - self._proxy_refresh_time > self._proxy_refresh_interval:
            logger.info("Refreshing free proxy pool...")
            self._free_proxies = await proxy_fetcher.get_working_proxies(max_count=15)
            self._proxy_refresh_time = time.time()
            logger.info(f"Loaded {len(self._free_proxies)} working free proxies")
    
    def _get_proxy(self) -> Optional[str]:
        # On cloud platforms (HF or Render), prioritize free proxy pool
        if (self.IS_HUGGINGFACE or self.IS_RENDER) and self._free_proxy_pool:
            proxy = self._free_proxy_pool[self._current_proxy_idx % len(self._free_proxy_pool)]
            self._current_proxy_idx += 1
            return proxy
        
        # Try free proxies first (legacy proxy_fetcher)
        if self._free_proxies:
            proxy = self._free_proxies[self._current_proxy_idx % len(self._free_proxies)]
            self._current_proxy_idx += 1
            return proxy
        
        # Fallback to configured proxies
        if not self.proxies: return None
        proxy = self.proxies[self._current_proxy_idx % len(self.proxies)]
        self._current_proxy_idx += 1
        return proxy


    async def _get_html_with_undetected_chrome(self, url: str) -> Optional[str]:
        """The 'NUCLEAR Option': Undetected-Chromedriver with safety locks for Windows"""
        async with self._uc_lock: 
            import undetected_chromedriver as uc
            
            logger.info(f"💣 Launching Undetected-Chrome NUCLEAR Bypass for {url}...")

            def get_chrome_version():
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
                    version, _ = winreg.QueryValueEx(key, 'version')
                    return int(version.split('.')[0])
                except:
                    return 120 # Fallback

            if not self._chrome_version:
                self._chrome_version = get_chrome_version()

            def chrome_task():
                driver = None
                try:
                    options = uc.ChromeOptions()
                    options.add_argument('--headless')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--window-size=1280,1024')
                    options.add_argument('--mute-audio')
                    options.add_argument('--disable-notifications')
                    options.add_argument('--disable-popup-blocking')
                    options.add_argument('--hide-scrollbars')
                    options.add_argument('--disable-logging')
                    options.add_argument('--log-level=3')
                    options.add_argument('--no-first-run')
                    options.add_argument('--no-default-browser-check')
                    options.add_argument('--no-pings')
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    
                    # Disable images for maximum speed
                    prefs = {
                        'profile.managed_default_content_settings.images': 2,
                        'profile.default_content_settings.images': 2
                    }
                    options.add_experimental_option('prefs', prefs)
                    
                    driver = uc.Chrome(options=options, version_main=self._chrome_version)
                    driver.set_page_load_timeout(60)
                    
                    logger.info(f"💣 UC Fetching: {url}")
                    driver.get(url)
                    
                    # Wait for either content or challenge
                    time.sleep(10) # Heavy sleep for UC
                    
                    html = driver.page_source
                    
                    # Basic sync of UA
                    ua = driver.execute_script("return navigator.userAgent")
                    if ua:
                        self.headers["User-Agent"] = ua
                        
                    return html
                except Exception as e:
                    logger.error(f"Undetected-Chrome failure: {e}")
                    return None
                finally:
                    if driver:
                        try: driver.quit()
                        except: pass
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, chrome_task)

    async def _get_html_with_flaresolverr(self, url: str) -> Optional[str]:
        """FlareSolverr with Singleton Lock to avoid browser bloat"""
        async with self._solver_lock:
            # Re-check cache inside lock
            if url in self._cache:
                return self._cache[url][1]
                
            logger.info(f"✨ Requesting FlareSolverr solve for {url}...")
            
            flaresolverr_url = "http://localhost:8191/v1"
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            }
            
            # Connection Retry Loop
            max_conn_retries = 5 # Increased retries
            for conn_attempt in range(max_conn_retries):
                try:
                    async with httpx.AsyncClient(timeout=90.0) as client:
                        response = await client.post(flaresolverr_url, json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('status') == 'ok':
                                solution = data.get('solution', {})
                                html = solution.get('response', '')
                            
                                # SYNCING LOGIC
                                cookies = solution.get('cookies', [])
                                ua = solution.get('userAgent', '')
                                if ua:
                                    self._ua_synced = ua
                                    self.headers["User-Agent"] = ua
                                
                                for cookie in cookies:
                                    # Ensure domain is set for proper cookie handling
                                    domain = cookie.get('domain')
                                    if not domain and url:
                                        try:
                                            domain = urlparse(url).netloc
                                            if domain.startswith('www.'):
                                                domain = domain[4:]
                                        except:
                                            pass
                                    
                                    if domain:
                                        self.session.cookies.set(
                                            cookie['name'],
                                            cookie['value'],
                                            domain=domain,
                                            path=cookie.get('path', '/'),
                                            secure=cookie.get('secure', False),
                                            expires=cookie.get('expires')
                                        )
                                
                                self._cookies_synced = True
                                self._last_pw_solve = time.time()
                                logger.info("✅ Session Synced!")
                                return html
                            else:
                                logger.warning(f"FlareSolverr error: {data.get('message')}")
                        else:
                            logger.warning(f"FlareSolverr returned status {response.status_code}")
                except Exception as e:
                    if conn_attempt < max_conn_retries - 1:
                        logger.warning(f"FlareSolverr comm failed (attempt {conn_attempt+1}/{max_conn_retries}): {e}. Retrying...")
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"FlareSolverr comm failed after {max_conn_retries} attempts: {e}")
            return None

    async def _turbo_prefetch(self):
        """Pre-fetch all major categories in parallel to populate cache instantly"""
        if self._is_prefetching: return
        self._is_prefetching = True
        logger.info("🚀 NITRO MODE: Starting concurrent background pre-fetch...")
        
        try:
            # List of high-priority tasks
            tasks = [self.fetch_home(page=1)]
            
            # Map of key categories to pre-warm
            priority_cats = list(self.CATEGORY_KEYWORDS.keys())[:15]
            for cat_id in priority_cats:
                tasks.append(self.fetch_category(cat_id, page=1))
            
            # Run everything in parallel with semaphore protection
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"⚡ NITRO MODE complete! Cache primed with {len(self._cache)} items.")
        except Exception as e:
            logger.error(f"Nitro pre-fetch failed: {e}")
        finally:
            self._is_prefetching = False

    async def _get_html(self, url: str, max_retries: int = 1, follow_meta=True) -> Optional[str]:
        """Nitro-Speed Fetch with Parallel Safety"""
        if not self._optimization_started:
            self._optimization_started = True
            asyncio.create_task(self._optimize_connection())

        async with self._semaphore:
            now = time.time()
            
            # 0. Cache Check
            if url in self._cache:
                ts, data = self._cache[url]
                if now - ts < self._cache_ttl:
                    return data
            
            # Sanitize URL - Skip landing pages
            if any(x in url for x in ["/gaza.20", "/gaza.18", "/gaza.22"]):
                logger.info(f"Sanitizing landing page URL: {url} -> {self.TARGET_URL}")
                url = self.TARGET_URL
            
            # Refresh free proxies if on cloud platforms
            if self.IS_HUGGINGFACE or self.IS_RENDER:
                await self._refresh_free_proxies()
            
            proxy = self._get_proxy()
            proxy_dict = {"http": proxy, "https": proxy} if proxy else None
                
            # 1. Nitro Path (curl-cffi)
            logger.info(f"🚀 Nitro Path (curl-cffi) for {url}")
            try:
                # Increased timeout to 45s to handle extremely slow responses
                resp = await self.session.get(url, headers=self.headers, timeout=45, proxies=proxy_dict)
                status_code = resp.status_code
                logger.info(f"📡 Nitro Path response: {status_code} ({len(resp.content)} bytes)")
                
                if status_code == 200:
                    text = resp.text
                    # Improve Meta Refresh detection (Larooza uses this heavily for domain rotation)
                    refresh_match = re.search(r'http-equiv=["\']refresh["\'].*?content=["\']\d+;\s*url=(.*?)["\']', text, re.I)
                    if not refresh_match:
                        refresh_match = re.search(r'content=["\']\d+;\s*url=(.*?)["\']', text, re.I)
                    
                    if refresh_match and follow_meta:
                        new_url_raw = refresh_match.group(1).strip("'\" ")
                        new_url = urljoin(url, new_url_raw)
                        
                        # Preserve query parameters if the new URL doesn't have them but the old one did
                        if "?" not in new_url and "?" in url:
                            query = url.split("?")[-1]
                            new_url = f"{new_url}?{query}" if not new_url.endswith("?") else f"{new_url}{query}"

                        # If redirecting to a known landing page or ad-trap, skip it
                        if any(x in new_url for x in ["gaza.20", "gaza.18", "gaza.22", "gaza.24"]):
                            logger.info(f"🚫 Skipping ad-trap redirect: {new_url}")
                            new_url = self.TARGET_URL
                        
                        logger.info(f"🔄 Following meta refresh to: {new_url}")
                        return await self._get_html(new_url, max_retries=max_retries, follow_meta=False)
                    
                    # More robust Cloudflare & Landing Page detection
                    text_lower = text.lower()
                    cf_markers = ["challenge-running", "cf-ray", "cloudflare-static", "just a moment", "verify you are human", "checking your browser"]
                    is_cf = any(x in text_lower for x in cf_markers) or "id=\"challenge-form\"" in text_lower
                    
                    # Detect landing page even if 200 OK (gaza.20 redirect in JS or Meta)
                    is_landing = "gaza.20" in text_lower or "gaza.18" in text_lower or "gaza.22" in text_lower
                    
                    if is_cf:
                        logger.warning(f"⚠️ Cloudflare detected in Nitro response for {url}")
                    elif is_landing and follow_meta:
                        logger.info(f"🔄 Landing page detected in content for {url}, forcing target...")
                        return await self._get_html(self.TARGET_URL, max_retries=max_retries, follow_meta=False)
                    else:
                        self._cache[url] = (now, text)
                        return text
                elif status_code == 404:
                    logger.warning(f"⚠️ Nitro Path 404 for {url} on mirror {self.BASE_URL}")
                    # If this was a mirror, fallback to primary domain
                    primary_primary = self.MIRRORS[0]
                    if self.BASE_URL != primary_primary:
                        fallback_url = url.replace(self.BASE_URL, primary_primary)
                        logger.info(f"🔁 Falling back to primary domain: {fallback_url}")
                        return await self._get_html(fallback_url, max_retries=max_retries, follow_meta=True)
                elif status_code == 403:
                    logger.warning(f"🚫 Nitro Path 403 for {url}, falling back to solvers...")
            except Exception as e:
                logger.error(f"❌ Nitro Path error for {url}: {e}")

            # 2. Solver Path
            for att in range(max_retries):
                # Use a specific lock for solver to prevent multiple concurrent solver requests for the same URL
                # but allow different URLs in parallel. For simplicity, we use the existing semaphore and a small delay.
                
                # Check cache again just in case another task filled it
                if url in self._cache:
                    return self._cache[url][1]

                html = await self._get_html_with_flaresolverr(url)
                if html:
                    self._cache[url] = (now, html)
                    return html
                
                # UC Fallback for critical pages
                if att == max_retries - 1:
                    logger.info(f"UC Fallback for: {url}")
                    res = await self._get_html_with_undetected_chrome(url)
                    if res: return res
                    
            return None

    def _extract_items(self, soup: BeautifulSoup) -> List[Dict]:
        """Ultra-Fast Content Extraction with Deep Image Probing"""
        items = []
        if not soup: return []

        if soup.title:
            logger.info(f"Extracting: {soup.title.string}")
            if "challenge" in str(soup.title).lower() or "cloudflare" in str(soup.title).lower():
                return []

        # Ultra-Strong Coverage for all Larooza Variants & Mirrors
        containers = soup.select('.thumbnail, .pm-li-video, .pm-video-thumb, .video-block, .movie-item, li.col-xs-6, .box, .video-box, .video-item, .post-item')
        if not containers:
            # Deep scan for any link that looks like a video
            containers = soup.select('a[href*="video.php"], a[href*="watch.php"], .video-listing-content, .card-video')

        seen_urls = set()
        for tag in containers:
            # 1. Fast Link Detection
            link = tag if (tag.name == 'a' and 'video.php' in tag.get('href', '')) else \
                   (tag.select_one('a.ellipsis') or tag.find('a', href=lambda x: x and 'video.php' in x))
            
            if not link: continue
            href = link.get('href')
            if not href: continue
            
            full_link = urljoin(self.BASE_URL, href)
            if full_link in seen_urls: continue
            seen_urls.add(full_link)

            # 2. Extract Title & Clean it
            title_node = tag.select_one('h3, h2, .title, .ellipsis, .video-title, p')
            title = title_node.get_text(strip=True) if title_node else ""
            if not title and link: 
                title = link.get('title') or link.get_text(strip=True)
            
            # Clean Title (Remove noisy tags for premium look)
            for t_tag in ["مشاهدة", "فيلم", "مسلسل", "كامل", "HDCAM", "HD", "WEB-DL", "Cam", "مترجم", "اون لاين", "مدبلج"]:
                title = title.replace(t_tag, "").strip()
            title = re.sub(r'\d{4}', '', title).strip("- ").strip() # Remove Year
            
            # 3. Deep Image Probing
            img_node = tag.select_one('img')
            img_url = ""
            if img_node:
                # Try all possible lazy-load attributes, prefer potential real URLs over base64
                candidates = [
                    img_node.get('data-src'), 
                    img_node.get('data-lazy-src'), 
                    img_node.get('data-original'),
                    img_node.get('srcset'), 
                    img_node.get('src')
                ]
                for c in candidates:
                    if c and not c.startswith('data:'):
                        # Ensure it's a real URL
                        if c.startswith('http') or c.startswith('//') or c.startswith('/'):
                            img_url = c
                            break
                
                # If still no image, try to find ANY attribute that looks like a URL
                if not img_url:
                    for attr, val in img_node.attrs.items():
                        if isinstance(val, str) and (val.startswith('http') or '.jpg' in val or '.png' in val) and not val.startswith('data:'):
                            img_url = val
                            break

                if img_url and "," in img_url: # Handle srcset
                    img_url = img_url.split(",")[0].split(" ")[0]
            
            # Fallback: Check for background-image in style
            if not img_url:
                style = tag.get('style') or ""
                if 'background-image' in style:
                    m = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                    if m:
                        img_url = m.group(1)
            
            if not img_url or img_url.startswith('data:'): 
                img_url = "https://placehold.co/600x400/000000/FFFFFF?text=No+Poster"
            
            # Absolute URL correction
            if img_url.startswith('//'): img_url = 'https:' + img_url
            elif img_url.startswith('/'): img_url = self.BASE_URL + img_url
            
            # Proxy through our backend for stability
            poster = f"/proxy/image?url={quote(img_url)}"
            
            # 4. Speed-optimized Series Detection
            lt = title.lower()
            content_type = "series" if any(x in lt for x in ['حلقة', 'مسلسل', 'episode', 'season', 'series']) else "movie"

            items.append({
                "id": base64.urlsafe_b64encode(full_link.encode()).decode(),
                "title": title,
                "poster": poster,
                "type": content_type,
                "duration": tag.select_one('.duration, .pm-label-duration, .time').get_text(strip=True) if tag.select_one('.duration, .pm-label-duration, .time') else ""
            })
        return items

    async def fetch_home(self, page: int = 1) -> List[Dict]:
        target = f"{self.TARGET_URL}?page={page}"
        html = await self._get_html(target, max_retries=3)
        if not html:
            logger.error(f"Failed to fetch home page: {target}")
            return []
        
        items = self._extract_items(BeautifulSoup(html, 'html.parser'))
        logger.info(f"Fetched {len(items)} items from {target}")
        return items

    async def fetch_category(self, cat_id: str, page: int = 1) -> List[Dict]:
        resolved_id = await self._resolve_cat_id(cat_id)
        target = f"{self.BASE_URL}/category.php?cat={resolved_id}&page={page}"
        html = await self._get_html(target, max_retries=3)
        return self._extract_items(BeautifulSoup(html, 'html.parser')) if html else []

    def _normalize_number(self, text: str) -> int:
        """Extract episode number from Arabic/English text"""
        # Arabic number words mapping
        arabic_map = {
            'الأولى': 1, 'الاولى': 1, 'الثانية': 2, 'الثالثة': 3, 'الرابعة': 4, 
            'الخامسة': 5, 'السادسة': 6, 'السابعة': 7, 'الثامنة': 8, 'التاسعة': 9, 
            'العاشرة': 10, 'الحادية': 11, 'الثانية عشر': 12, 'الثالثة عشر': 13,
            'الرابعة عشر': 14, 'الخامسة عشر': 15, 'السادسة عشر': 16, 'السابعة عشر': 17,
            'الثامنة عشر': 18, 'التاسعة عشر': 19, 'العشرون': 20, 'الاخيرة': 999
        }
        
        # Try to find numeric digits first (most reliable)
        match = re.search(r'(\d+)', text)
        if match: 
            return int(match.group(1))
        
        # Try Arabic number words
        text_lower = text.lower()
        for arabic_word, num in arabic_map.items():
            if arabic_word in text_lower:
                return num
        
        # Try to extract from patterns like "الحلقة X" or "Episode X"
        patterns = [
            r'(?:الحلقة|حلقة|episode|ep)\s*[:\-]?\s*(\d+)',
            r'(\d+)\s*(?:الحلقة|حلقة|episode|ep)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1))
        
        return 0

    def _safe_get_episode(self, text: str, name_hint: str = None) -> int:
        """Smarter episode number extraction with common patterns"""
        # Remove common noise
        clean = re.sub(r'\(.*?\)', '', text)
        clean = re.sub(r'\[.*?\]', '', clean)
        
        if name_hint:
            # Remove the series name from the text to avoid matching numbers in the title (e.g. "2 قهوة")
            clean = clean.replace(name_hint, "").strip()

        # 1. Look for number after keywords (Most reliable)
        m = re.search(r'(?:الحلقة|حلقة|ep|episode|part|p)\s*(\d+)', clean, re.I)
        if m: return int(m.group(1))
        
        # 2. Direct digits (Fallback)
        m = re.search(r'(\d+)', clean)
        if m: return int(m.group(1))
        
        # 3. Word matches
        return self._normalize_number(clean)

    async def search(self, query: str) -> List[Dict]:
        url = f"{self.BASE_URL}/search.php?keywords={quote(query)}"
        html = await self._get_html(url, max_retries=2)
        return self._extract_items(BeautifulSoup(html, 'html.parser')) if html else []

    async def fetch_details(self, safe_id: str) -> Dict:
        try:
            url = base64.urlsafe_b64decode(safe_id).decode()
        except: return {}

        html = await self._get_html(url)
        if not html: return {}

        soup = BeautifulSoup(html, 'html.parser')
        
        # Follow play.php for watch servers
        watch_html = html
        watch_soup = soup
        play_a = soup.select_one('a[href*="play.php"]')
        if play_a:
            p_url = urljoin(self.BASE_URL, play_a.get('href'))
            p_html = await self._get_html(p_url)
            if p_html:
                watch_soup = BeautifulSoup(p_html, 'html.parser')
                watch_html = p_html

        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Unknown"
        is_series = bool(soup.select('.episodes-list, .season-episodes, .vid-episodes')) or any(x in title for x in ["حلقة", "مسلسل", "الموسم"])
        
        raw_poster = soup.select_one('meta[property="og:image"]')['content'] if soup.select_one('meta[property="og:image"]') else ""
        if not raw_poster:
            img_tag = soup.select_one('.poster img, .movie-poster img, .pm-video-watch-main img')
            if img_tag:
                raw_poster = img_tag.get('src') or img_tag.get('data-src')
        
        poster = ""
        if raw_poster:
            full_poster_url = urljoin(self.BASE_URL, raw_poster)
            poster = f"/proxy/image?url={quote(full_poster_url)}"

        response = {
            "id": safe_id, "title": title, 
            "description": soup.select_one('.story, .desc, .entry-content').get_text(strip=True) if soup.select_one('.story, .desc, .entry-content') else "",
            "poster": poster,
            "type": "series" if is_series else "movie", 
            "seasons": [], "episodes": [], "servers": [], "download_links": []
        }

        # --- Episodes ---
        if is_series:
            unique_eps = {}
            
            # 1. Proactive Search: Look for a "Series Category" link
            cat_link = None
            
            # A. Check Breadcrumbs (Very reliable for series category)
            for bc in soup.select('.breadcrumb a, .bread-crumb a, .breadcrumbs a, .pm-breadcrumb a'):
                href = bc.get('href')
                if href and ('cat=' in href or 'ser=' in href):
                    # Skip generic high-level categories if possible? 
                    # Actually, we filter by title later, so it's okay.
                    cat_link = urljoin(self.BASE_URL, href)
                    if 'ser=' in href: # Prefer ser= over cat=
                        break
            
            # Extract clean series name for filtering
            clean_title = title.replace("مسلسل", "").strip()
            # Try to get name before "الحلقة" or "المواسم"
            series_name = re.split(r'الحلقة|الموسم|حلقة|season|episode', clean_title, flags=re.I)[0].strip()
            # Arabic numeral support for filtering
            series_name_alt = series_name.replace('0','٠').replace('1','١').replace('2','٢').replace('3','٣').replace('4','٤').replace('5','٥').replace('6','٦').replace('7','٧').replace('8','٨').replace('9','٩')
            
            logger.info(f"Targeting series name: {series_name} (Alt: {series_name_alt})")

            # B. Check if Title itself is a link to the category or series
            if not cat_link:
                title_link = soup.select_one('h1 a[href*="cat="], h1 a[href*="ser="], h1 a[href*="tag.php"]')
                if title_link:
                    cat_link = urljoin(self.BASE_URL, title_link['href'])
            
            # C. General search in links with strict patterns
            if not cat_link:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    a_text = a.get_text(strip=True)
                    # High-confidence patterns
                    if any(x in a_text for x in ["المسلسل:", "جميع الحلقات", "حلقات المسلسل", "كل الحلقات"]):
                        cat_link = urljoin(self.BASE_URL, href)
                        logger.info(f"Found cat_link via labels: {cat_link}")
                        break
            
            # D. Fallback search by title
            if not cat_link:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if any(x in href for x in ['ser=', 'cat=', 'tag.php']):
                        a_text = a.get_text(strip=True)
                        if (series_name and series_name in a_text) or (series_name_alt and series_name_alt in a_text):
                            cat_link = urljoin(self.BASE_URL, href)
                            logger.info(f"Found cat_link via fallback title search: {cat_link}")
                            break
            
            if cat_link:
                try:
                    # Determine type: view-serie.php, category.php, tag.php
                    is_view_serie = 'view-serie' in cat_link
                    param_name = 'ser' if is_view_serie else ('t' if 'tag.php' in cat_link else 'cat')
                    
                    # Robust ID extraction
                    match = re.search(f'[?&]{param_name}=([^&]+)', cat_link)
                    if match:
                        cat_id = match.group(1)
                        base_deep_url = f"{self.BASE_URL}/tag.php?t={cat_id}" if param_name == 't' else \
                                        (f"{self.BASE_URL}/view-serie.php?ser={cat_id}" if is_view_serie else \
                                         f"{self.BASE_URL}/category.php?cat={cat_id}")
                        
                        logger.info(f"Deep scraping episodes from {cat_link} (ID: {cat_id})")
                        # Fetch first 5 pages
                        for p in range(1, 6):
                            target_p = f"{base_deep_url}&page={p}" if p > 1 else base_deep_url
                            p_html = await self._get_html(target_p)
                            if not p_html: break
                            p_items = self._extract_items(BeautifulSoup(p_html, 'html.parser'))
                            
                            if not p_items: break
                            for item in p_items:
                                # Filter Check: Use a fuzzy name match
                                i_title = item['title']
                                # Must match at least the first 2 words if possible, or the whole name
                                name_parts = series_name.split()
                                match_key = " ".join(name_parts[:2]) if len(name_parts) >= 2 else series_name
                                
                                if match_key in i_title or series_name in i_title or series_name_alt in i_title:
                                    e_num = self._safe_get_episode(i_title, name_hint=series_name)
                                    if e_num and e_num not in unique_eps:
                                        unique_eps[e_num] = {
                                            "id": item['id'],
                                            "episode": e_num,
                                            "title": i_title
                                        }
                            if len(p_items) < 10: break
                except Exception as e:
                    logger.error(f"Category episode fetch failed: {e}")

            # 2. Local fallback: Scrape episodes from the current page
            for ep in soup.select('.episodes-list a, .season-episodes a, .vid-episodes a, ul.episodes li a, div.caption h3 a, .movie-item a, .related-vids a'):
                ep_href = ep.get('href')
                if not ep_href or 'video.php' not in ep_href: continue
                ep_url = urljoin(self.BASE_URL, ep_href)
                ep_text = ep.get_text(strip=True)
                
                # If text is empty, check for nested title
                if not ep_text:
                    inner = ep.find(['h3', 'span', 'strong'])
                    if inner: ep_text = inner.get_text(strip=True)
                
                # CRITICAL FILTER: Item must belong to this series
                if series_name and series_name not in ep_text:
                    continue

                ep_num = self._safe_get_episode(ep_text, name_hint=series_name)
                if ep_num and ep_num not in unique_eps:
                    unique_eps[ep_num] = {
                        "id": base64.urlsafe_b64encode(ep_url.encode()).decode(),
                        "episode": ep_num,
                        "title": ep_text
                    }
            
            response['episodes'] = sorted(list(unique_eps.values()), key=lambda x: x['episode'])
            response['seasons'] = [{"number": 1, "episodes": response['episodes']}]

        # --- WATCH SERVERS ---
        watch_urls = set()

        def is_valid_srv(url_str: str) -> bool:
            if not url_str or 'javascript' in url_str: return False
            if 'larooza' in url_str and 'video.php' in url_str: return False
            if any(x in url_str.lower() for x in ['beacon', 'analytics', 'pixel', 'ads.', 'google', 'facebook']): return False
            return True

        # 1. Primary: WatchList & Source tags
        server_selectors = [
            'ul.WatchList li', '.server-list li', '#servers li', '.watch-servers li',
            '.video-servers-list li', 'div.servers a', '.player-servers li'
        ]
        
        for sel in server_selectors:
            for li in watch_soup.select(sel):
                s_url = li.get('data-embed-url') or li.get('data-link') or li.get('data-embed') or li.get('data-src') or li.get('data-url')
                if not s_url:
                    a_tag = li.find('a', href=True)
                    if a_tag and not a_tag['href'].startswith('javascript'):
                        s_url = a_tag['href']
                
                if s_url and is_valid_srv(s_url):
                    if s_url.startswith('//'): s_url = "https:" + s_url
                    full_s_url = urljoin(self.BASE_URL, s_url)
                    if full_s_url not in watch_urls:
                        watch_urls.add(full_s_url)
                        name = li.get_text(strip=True) or f"سيرفر {len(response['servers']) + 1}"
                        response['servers'].append({"name": name, "url": full_s_url, "type": "iframe"})

        # 2. Secondary: Deep Iframe Scan
        for ifr in watch_soup.select('iframe[src], embed[src], video source[src]'):
            src = ifr.get('src')
            if is_valid_srv(src):
                if src.startswith('//'): src = "https:" + src
                full_s_url = urljoin(self.BASE_URL, src)
                if full_s_url not in watch_urls:
                    watch_urls.add(full_s_url)
                    response['servers'].append({"name": f"سيرفر سريع {len(response['servers']) + 1}", "url": full_s_url, "type": "iframe"})

        # 3. Regex Fallback (Scripts & Global)
        patterns = [
            r'iframe.*?src=["\'](https?://[^"\']+)["\']',
            r'embedUrl["\']\s*:\s*["\'](https?://[^"\']+)["\']',
            r'file["\']\s*:\s*["\'](https?://[^"\']+\.m3u8)["\']',
            r'source\s*src=["\'](https?://[^"\']+)["\']'
        ]
        for pattern in patterns:
            for match in re.findall(pattern, watch_html, re.I):
                if is_valid_srv(match) and match not in watch_urls:
                    watch_urls.add(match)
                    response['servers'].append({"name": f"سيرفر احتياطي {len(response['servers']) + 1}", "url": match, "type": "iframe"})

        # Clean duplicates and sort by quality/relevance if possible
        # For now, just ensuring uniqueness
        
        # --- Downloads ---
        dl_url = url.replace('video.php', 'download.php').replace('play.php', 'download.php')
        dl_html = await self._get_html(dl_url)
        if dl_html:
            dl_soup = BeautifulSoup(dl_html, 'html.parser')
            for mirror in dl_soup.select('a[target="_blank"]'):
                m_url = mirror.get('href')
                if m_url and 'http' in m_url:
                    if any(x in m_url.lower() for x in ['wa.me', 'facebook.com', 'twitter.com', 'telegram.me', 't.me', 'sharer.php']):
                        continue
                    q_text = mirror.get_text(strip=True).replace("اضغط هنا للتحميل", "").replace("تحميل الملف", "").strip() or "رابط تحميل"
                    response['download_links'].append({"quality": q_text, "url": m_url})

        return response

scraper = LaroozaScraper()
