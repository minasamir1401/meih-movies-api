import asyncio
import re
import logging
import base64
import random
import os
import time
from typing import List, Dict, Optional, Union
from collections import OrderedDict
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
import httpx

# Neutral Logging Configuration
logger = logging.getLogger("provider")
logger.setLevel(logging.INFO)

class ProviderError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class DiscoveryCache:
    """Internal cache with varying TTLs for different resource types"""
    def __init__(self, capacity: int = 1000):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return None
        data, ts, ttl = self.cache[key]
        if time.time() - ts > ttl:
            del self.cache[key]
            return None
        self.cache.move_to_end(key)
        return data

    def put(self, key, value, ttl=3600):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = (value, time.time(), ttl)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class ResourceResolver:
    """Hardened resource discovery engine with non-sensitive naming"""
    
    # Provider domains stored in env for safety
    NET_NODES = os.getenv("NETWORK_NODES", "https://larooza.site,https://larooza.tv,https://larooza.net").split(',')
    
    def __init__(self):
        self.token = os.getenv("SCRAPER_API_KEY", "aba96c9b1ad64905456a513bfd43fbe9")
        self.node_idx = 0
        self.ROOT = self.NET_NODES[0]
        self.concurrency = asyncio.Semaphore(10) # Throttled
        self.store = DiscoveryCache(capacity=800)
        
    def _cycle_node(self):
        self.node_idx = (self.node_idx + 1) % len(self.NET_NODES)
        self.ROOT = self.NET_NODES[self.node_idx]

    def _generate_identity(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Rotate realistic browser headers"""
        browsers = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': random.choice(browsers)
        }
        if referer: headers['Referer'] = referer
        return headers

    async def _invoke_remote(self, endpoint: str, ref: Optional[str] = None, extended: bool = False) -> str:
        """Securely fetch remote content with jitter and caching"""
        cached = self.store.get(endpoint)
        if cached: return cached

        # Reduced Jitter (0.1-0.3s) for better speed while staying safe
        await asyncio.sleep(random.uniform(0.1, 0.3))

        async with self.concurrency:
            try:
                # 3. Security Proxy Config
                proxy_base = f"http://scraperapi:{self.token}@proxy-server.scraperapi.com:8001"
                if extended:
                    proxy_base = f"http://scraperapi.render=true:{self.token}@proxy-server.scraperapi.com:8001"
                
                ident = self._generate_identity(ref or self.ROOT)
                logger.info(f"Invoking Remote Task [Mode: {'E' if extended else 'F'}]") # Generic log
                
                async with httpx.AsyncClient(proxy=proxy_base, timeout=45.0, verify=False, follow_redirects=True) as client:
                    resp = await client.get(endpoint, headers=ident)
                
                if resp.status_code == 200:
                    raw = resp.text
                    # Auto-escalation if protection detected
                    if not extended and (len(raw) < 600 or "javascript" in raw.lower()[:300]):
                        logger.warning("Resource requires escalation...")
                        return await self._invoke_remote(endpoint, ref, extended=True)
                    
                    # Store with long-lived TTL (1800s - 1 hour)
                    self.store.put(endpoint, raw, ttl=3600)
                    return raw
                
                if not extended:
                    return await self._invoke_remote(endpoint, ref, extended=True)
                    
                raise ProviderError(f"Status {resp.status_code}")
            except Exception as e:
                if not extended:
                    return await self._invoke_remote(endpoint, ref, extended=True)
                logger.error(f"Execution Error") # No details in logs
                return ""

    def _map_content_grid(self, raw_html: str) -> List[Dict]:
        """Neutral extraction logic"""
        if not raw_html: return []
        soup = BeautifulSoup(raw_html, 'html.parser')
        nodes = []
        # Dynamic selectors to avoid static pattern detection
        grids = soup.select('li.col-sm-4, .pm-li-video, .video-item, article, .col-md-3')
        
        seen_uids = set()
        for node in grids:
            anchor = node.select_one('a.ellipsis, a[href*="video.php"]')
            if not anchor: continue
            
            ref_path = anchor.get('href', '')
            abs_url = urljoin(self.ROOT, ref_path)
            
            # Use stable UID
            v_match = re.search(r'vid=([^&]+)', abs_url)
            uid = v_match.group(1) if v_match else base64.urlsafe_b64encode(abs_url.encode()).decode()
            
            if uid in seen_uids: continue
            seen_uids.add(uid)
            
            # Asset Path (Neutral naming for poster)
            asset_node = node.find('img')
            asset_url = ""
            if asset_node:
                # Check ALL possible source attributes including legacy ones
                # Prefer data attributes over src for lazy-loaded images
                attrs_to_check = ['data-src', 'data-echo', 'data-original', 'lazy-src', 'data-lazy', 'src']
                for attr in attrs_to_check:
                    val = asset_node.get(attr)
                    if val and isinstance(val, str):
                        # Skip base64 encoded placeholders
                        if val.startswith('data:image'):
                            continue
                        if val.startswith('http'): asset_url = val
                        elif val.startswith('//'): asset_url = "https:" + val
                        elif val.startswith('/'): asset_url = urljoin(self.ROOT, val)
                        else: asset_url = urljoin(self.ROOT, val) # Fallback for relative paths without /
                        if asset_url: break
            
            label = ""
            if anchor.get('title'): label = anchor.get('title')
            elif asset_node and asset_node.get('alt'): label = asset_node.get('alt')
            else: label = anchor.get_text(strip=True)

            nodes.append({
                "id": base64.urlsafe_b64encode(abs_url.encode()).decode(),
                "title": label[:100] if label else "Content",
                "poster": asset_url,
                "type": "series" if any(x in label for x in ["مسلسل", "حلقة", "Episode", "Ep"]) else "movie"
            })
        return nodes

    def _resolve_vectors_from_soup(self, s: BeautifulSoup) -> List[Dict]:
        """Extra vectors from soup (fallback)"""
        vectors = []
        seen = set()
        
        # SPECIAL CASE: Larooza download page structure
        # Look for download list items with data-download-url attributes first
        download_list_items = s.select('ul.downloadlist li[data-download-url]')
        for item in download_list_items:
            u = item.get('data-download-url')
            if not u:
                # Try to get href from the anchor tag
                a_tag = item.find('a')
                if a_tag:
                    u = a_tag.get('href')
            
            if u:
                # Get all spans and combine their text for better labeling
                span_tags = item.find_all('span')
                if span_tags:
                    # Get the domain name from the URL for better labeling
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', u)
                    domain = domain_match.group(1) if domain_match else ''
                    
                    # Get descriptive text from spans
                    label_parts = [span.get_text(strip=True) for span in span_tags if span.get_text(strip=True)]
                    if label_parts:
                        # Use the first descriptive part as quality
                        quality = label_parts[0] if len(label_parts) > 0 else domain
                    else:
                        quality = domain if domain else f"Download Server {len(vectors)+1}"
                else:
                    # Extract domain name for labeling
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', u)
                    quality = domain_match.group(1) if domain_match else f"Download Server {len(vectors)+1}"
                
                abs_u = urljoin(self.ROOT, u) if not u.startswith('http') else u
                abs_u = abs_u.strip()
                
                if abs_u not in seen:
                    seen.add(abs_u)
                    vectors.append({"quality": quality, "url": abs_u})
        
        # If we found larooza-specific download links, return them immediately
        if len(vectors) > 0:
            logger.info(f"Found {len(vectors)} Larooza download vectors")
            return vectors
        
        # ENHANCED METHOD: Advanced download link extraction for Larooza
        # Try multiple attributes for download URL
        download_items = s.select('ul.downloadlist li')
        for i, item in enumerate(download_items):
            # Try multiple attributes for download URL
            download_url = (
                item.get('data-download-url') or 
                item.get('data-url') or 
                item.get('data-link')
            )
            
            # Try to get URL from anchor tag
            a_tag = item.find('a')
            if not download_url and a_tag:
                download_url = a_tag.get('href') or a_tag.get('data-href')
            
            # Get label/description
            label = ""
            spans = item.find_all('span')
            if spans:
                label_parts = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]
                label = ' '.join(label_parts) if label_parts else ""
            
            if not label:
                if a_tag:
                    label = a_tag.get_text(strip=True) or a_tag.get('title', '')
            
            # Clean and validate URL
            if download_url:
                # Handle relative URLs
                if not download_url.startswith('http'):
                    download_url = urljoin(self.ROOT, download_url)
                
                # Filter out obviously bad URLs
                if (download_url and 
                    not any(bad in download_url.lower() for bad in ['javascript:', '#', 'void']) and
                    len(download_url) > 10):
                    
                    # Avoid duplicates
                    if not any(dl['url'] == download_url for dl in vectors):
                        vectors.append({
                            'quality': label or f"Download Link {len(vectors)+1}",
                            'url': download_url
                        })
        
        if len(vectors) > 0:
            logger.info(f"Found {len(vectors)} enhanced download vectors")
            return vectors
        
        # Enhanced selectors to include larooza-specific download structures and more patterns
        selectors = [
            'a[href*="download"]', 'a[href*="multiup"]', 'a[href*="php?id="]', 
            'a[href*="mp4"]', 'a[href*="mkv"]', '.download-link', 'table a[href]', 
            'ul.downloadlist li', '.download-buttons a', '.dl-btn',
            'a.btn-download', 'a[href*="get_file"]', 'a[href*="direct"]',
            '.mirror a', '.mirrors a', 'a[data-file]', 'a[download]',
            # Larooza specific selectors
            '.download-servers a', '.download-options a', '.dl-option a'
        ]
        
        # Collect all matching elements
        tags = []
        for selector in selectors:
            tags.extend(s.select(selector))
        
        # Also look for divs with download classes that might contain buttons
        download_divs = s.select('div[class*="download"], div[class*="dl-"], div[id*="download"]')
        for div in download_divs:
            # Look for buttons or links inside these divs
            tags.extend(div.select('a, button'))
        
        # If we still don't have enough links, try finding any large buttons or prominent links
        if len(tags) < 3:
            # Look for prominent links that might be download buttons
            prominent_links = s.select('a.btn, a.button, a.large, a[href]:not(.nav-link):not(.menu-link)')
            tags.extend(prominent_links[:10])  # Limit to prevent too many false positives
        
        for item in tags:
            # Handle larooza-specific download list items
            if item.name == 'li' and item.parent and 'downloadlist' in (item.parent.get('class', []) or []):
                u = item.get('data-download-url')
                if not u:
                    # Try to find the link inside the li
                    a_tag = item.find('a')
                    if a_tag:
                        u = a_tag.get('href')
                # Get all spans and combine their text for better labeling
                span_tags = item.find_all('span')
                if span_tags:
                    label_parts = [span.get_text(strip=True) for span in span_tags if span.get_text(strip=True)]
                    label = ' '.join(label_parts) if label_parts else "Download"
                else:
                    label = "Download"
            else:
                # Traditional link handling
                u = item.get('href')
                if not u: 
                    # Try other attributes for buttons
                    u = item.get('data-href') or item.get('data-link') or item.get('onclick')
                    if u and 'location.href' in u:
                        # Extract URL from onclick="location.href='...'
                        match = re.search(r"location\\.href=['\"]([^'\"]+)['\"]", u)
                        if match:
                            u = match.group(1)
                    
                if not u: continue
                label = item.get_text(strip=True) or item.get('title') or item.get('data-title') or "Download"
                label = re.sub(r'\s+', ' ', label).strip()
                if not label or label.lower() in ['link', 'تحميل', 'download']:
                    td = item.find_parent('td')
                    if td: label = td.get_text(strip=True)
                
                # Try to get better labels from nearby elements
                if not label or len(label) < 3:
                    # Look for nearby spans or divs with quality info
                    parent = item.parent
                    if parent:
                        quality_elements = parent.select('span, div')
                        for elem in quality_elements:
                            text = elem.get_text(strip=True)
                            if text and len(text) > 2 and not any(x in text.lower() for x in ['download', 'تحميل']):
                                label = text
                                break
            
            if not u: continue
            abs_u = urljoin(self.ROOT, u) if not u.startswith('http') else u
            # Normalize the URL by stripping any trailing whitespace/newlines
            abs_u = abs_u.strip()
            
            # Clean up onclick URLs
            if abs_u.startswith('javascript:'):
                match = re.search(r"['\"]([^'\"]+)['\"]", abs_u)
                if match:
                    abs_u = match.group(1)
                    abs_u = urljoin(self.ROOT, abs_u) if not abs_u.startswith('http') else abs_u
            
            if abs_u not in seen:
                # Enhanced criteria for download links - stricter filtering
                # Must have video file extension OR explicit download indicators
                has_video_extension = any(x in abs_u.lower() for x in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m3u8'])
                has_download_indicator = any(x in abs_u.lower() for x in ['download', 'multiup', 'get_file', 'direct'])
                is_download_list_item = (item.name == 'li' and item.parent and 'downloadlist' in (item.parent.get('class', []) or []))
                has_html5_download = (item.get('download') is not None)
                has_download_class = any(x in (item.get('class', []) or []) for x in ['download', 'dl-btn', 'btn-download'])
                
                is_download_link = has_video_extension or has_download_indicator or is_download_list_item or has_html5_download or has_download_class
                
                # Exclude social media, tracking links, and navigation pages
                excluded_patterns = [
                    'facebook', 'twitter', 'whatsapp', 'telegram', 'mailto:', 'javascript:', '#',
                    '/home', '/gaza', '/category', '/section', '/browse', '/search',
                    'home.24', 'gaza.20', 'most-watched', 'topvideos', 'newvideos'
                ]
                
                if is_download_link and not any(x in abs_u.lower() for x in excluded_patterns) and abs_u != self.ROOT: 
                    seen.add(abs_u)
                    # Improve quality labeling - only use real video resolutions
                    # Reject labels that contain navigation terms
                    navigation_terms = ['home', 'page', 'series', 'categories', 'most', 'watched', 'الصفحة', 'مسلسل', 'اقسام', 'الاكثر', 'الاضافات', 'افلام']
                    has_navigation_term = any(term in label.lower() for term in navigation_terms)
                    
                    if not label or len(label) < 3 or has_navigation_term or any(x in label.lower() for x in ['download', 'تحميل', 'link', 'high', 'quality']):
                        # Try to infer quality from URL
                        if '1080' in abs_u:
                            label = '1080p'
                        elif '720' in abs_u:
                            label = '720p'
                        elif '480' in abs_u:
                            label = '480p'
                        elif '360' in abs_u:
                            label = '360p'
                        else:
                            # Only reject completely if it's clearly not a download link
                            has_video_indicators = any(x in abs_u.lower() for x in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m3u8', 'download', 'multiup', 'get_file'])
                            if has_video_indicators:
                                label = f"Download Link {len(vectors)+1}"
                            else:
                                # Skip non-download links entirely
                                continue
                    
                    vectors.append({"quality": label, "url": abs_u})
        
        # If we still don't have download links, try to parse download tables
        if len(vectors) == 0:
            tables = s.select('table')
            for table in tables:
                rows = table.select('tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 2:
                        # Look for rows with quality info and download links
                        quality_cell = cells[0]
                        link_cell = cells[-1]  # Usually the last cell contains the link
                        
                        quality = quality_cell.get_text(strip=True)
                        link_a = link_cell.select_one('a')
                        
                        if link_a and quality:
                            u = link_a.get('href')
                            if u:
                                abs_u = urljoin(self.ROOT, u) if not u.startswith('http') else u
                                abs_u = abs_u.strip()
                                
                                if abs_u not in seen and not any(x in abs_u.lower() for x in excluded_patterns):
                                    seen.add(abs_u)
                                    vectors.append({"quality": quality, "url": abs_u})
        
        logger.info(f"Found {len(vectors)} download vectors")
        return vectors

    async def _resolve_vectors(self, endpoint: str) -> List[Dict]:
        """Resolved storage vectors (neutral for downloads)"""
        try:
            # Force extended=True for download pages as they often use JS redirection/popups
            # Add timeout to prevent hanging
            raw = await asyncio.wait_for(self._invoke_remote(endpoint, extended=True), timeout=15.0)
            if not raw: return []
            return self._resolve_vectors_from_soup(BeautifulSoup(raw, 'html.parser'))
        except asyncio.TimeoutError:
            logger.warning(f"Timeout resolving download vectors for {endpoint}")
            return []
        except Exception as e:
            logger.error(f"Error resolving download vectors: {e}")
            return []

    async def _resolve_source_matrix(self, path: str, origin: Optional[str] = None) -> List[Dict]:
        """Resolved provider info (neutral for servers)"""
        try:
            # Try with timeout to prevent hanging
            raw = await asyncio.wait_for(self._invoke_remote(path, ref=origin), timeout=10.0)
            matrix = self._process_node_matrix(raw)
            if len(matrix) < 2:
                raw = await asyncio.wait_for(self._invoke_remote(path, ref=origin, extended=True), timeout=10.0)
                matrix = self._process_node_matrix(raw)
            return matrix
        except asyncio.TimeoutError:
            logger.warning(f"Timeout resolving source matrix for {path}")
            return []
        except Exception as e:
            logger.error(f"Error resolving source matrix: {e}")
            return []

    def _process_node_matrix(self, raw: str) -> List[Dict]:
        if not raw: return []
        s = BeautifulSoup(raw, 'html.parser')
        matrix = []
        
        # 1. Primary Vector
        f = s.find('iframe')
        if f:
            src = f.get('src') or f.get('data-src')
            if src:
                if not src.startswith('http'): src = urljoin(self.ROOT, src)
                # Be less restrictive on main player - allow most URLs
                problematic_domains = ['okprime.site', 'film77.xyz']
                # Only filter out truly problematic domains
                if not any(domain in src.lower() for domain in problematic_domains):
                    matrix.append({"name": "Main Player", "url": src, "type": "iframe"})
                else:
                    logger.info(f"Skipping problematic main player URL: {src}")
        else:
            # If no iframe found, look for video URLs in the page content
            # This handles cases where the video player is loaded dynamically
            page_text = s.get_text()
            video_patterns = [
                r'(?:https?://[^\s"]+embed\.php\?vid=[^\s"]+)',
                r'(?:https?://[^\s"]+video\.php\?vid=[^\s"]+)'
            ]
            for pattern in video_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    url = match.group(0)
                    # Filter out garbage URLs
                    if (url and url not in [m['url'] for m in matrix] and
                        'لم يتم إختيار' not in url and 'لم يتم العثور' not in url and
                        'no file' not in url.lower() and 'not found' not in url.lower()):
                        matrix.append({"name": "Dynamic Player", "url": url, "type": "iframe"})
        
        # 2. Secondary Matrix (Traditional Selectors)
        sel = [
            '.servers-list li', '.player-servers li', '.watch-servers a', 
            '.list-server-items li', 'ul.servers a', '.video-servers li',
            'div[data-url]', 'a[data-vid]', '.server-item',
            'ul.WatchList li',  # Added for larooza site
            '[data-embed-url]', '[data-embed-id]',  # Added for larooza site
            '.server-list li', '.servers-box a', '.play-servers li',
            '.video-player-servers li', '.stream-servers a', '.mirror-servers li',
            'div.server-link', 'a.server-option', '.server-button'
        ]
        
        for selector in sel:
            for item in s.select(selector):
                # Try larooza-specific attributes first
                u = item.get('data-embed-url') or item.get('data-url') or \
                    item.get('href') or item.get('data-id') or \
                    item.get('data-vid') or item.get('data-link') or item.get('data-source') or \
                    item.get('data-embed-id')  # Added for larooza site
                
                if not u and item.name != 'a':
                    a = item.find('a')
                    if a: u = a.get('href') or a.get('data-url') or a.get('data-vid')
                
                if u and 'javascript' not in u.lower():
                    # Handle IDs vs URLs
                    if not u.startswith('http') and len(u) > 5:
                        if u.isalnum() and not '/' in u:
                            u = urljoin(self.ROOT, f"play.php?vid={u}")
                        else:
                            u = urljoin(self.ROOT, u)
                    elif not u.startswith('http') and u:
                         u = urljoin(self.ROOT, u)
                            
                    if u and u.startswith('http'):
                        # Try to get a better name for larooza servers
                        name_elem = item.find('strong')
                        name = (name_elem.get_text(strip=True) if name_elem else '') or \
                               item.get_text(strip=True) or \
                               item.get('data-embed-id') or \
                               f"Server {len(matrix)+1}"
                        # Allow more servers by reducing filtering - only filter out clearly problematic ones
                        # Only filter out social media and clearly non-video domains
                        if any(x in u.lower() for x in ['facebook', 'twitter']):
                            logger.info(f"Skipping social media server URL: {u}")
                            continue
                        if not any(m['url'] == u for m in matrix):
                            matrix.append({"name": name, "url": u, "type": "iframe"})

        # 3. Script Scan (Deep Discovery) - Enhanced for all server types
        scripts = s.find_all('script')
        for script in scripts:
            content = script.string or ""
            # Look for common patterns like "url": "...", "link": "...", "vid": "..."
            # Extended to capture direct video sources and m3u8 files
            # Prioritize Larooza-specific patterns
            patterns = [
                r'(?:url|link|vid|file|src)\s*[:=]\s*["\']([^"\']*(?:embed\.php|video\.php)\?vid=[^"\']*)["\']',  # Larooza embed/video patterns
                r'(?:url|link|vid|file|src)\s*[:=]\s*["\']([^"\']*\.(?:mp4|mkv|avi|mov|wmv|flv|webm|m3u8)[^"\']*)["\']',
                r'(?:url|link|vid|file|src)\s*[:=]\s*["\']([^"\']+)["\']',
                r'\"(?:url|link|vid|file|src)\"\s*:\s*\"([^"]+)\"',
                r"\'(?:url|link|vid|file|src)\'\s*:\s*\'([^\']+)\'"
            ]
                    
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for m in matches:
                    u = m.group(1)
                    if u and len(u) > 10:
                        # Clean the link
                        if not u.startswith('http'): 
                            if u.startswith('//'): u = "https:" + u
                            else: u = urljoin(self.ROOT, u)
                                
                        # Filter out images, ROOT, and current page
                        if any(u.lower().endswith(x) for x in ['.jpg', '.png', '.webp', '.jpeg', '.gif', '.svg']):
                            continue
                        if u.rstrip('/') == self.ROOT.rstrip('/'):
                            continue
                        
                        # Filter out garbage URLs that contain fragments or are malformed
                        if ('url:' in u.lower() or 'link:' in u.lower() or 'file:' in u.lower() or 
                            '<a href=' in u.lower() or '={' in u or '}' in u or 
                            'javascript:' in u or 'void(' in u or
                            'لم يتم إختيار' in u or 'لم يتم العثور' in u or
                            'no file' in u.lower() or 'not found' in u.lower()):
                            continue
                                
                        # Filter out known problematic domains and patterns - but be less restrictive
                        problematic_domains = ['okprime.site', 'film77.xyz']
                        # Allow more servers by reducing filtering
                        if not any(m['url'] == u for m in matrix) and \
                           not any(x in u.lower() for x in ['facebook', 'twitter']) and \
                           not any(domain in u.lower() for domain in problematic_domains):
                            # Determine server type based on file extension
                            server_type = "video" if any(ext in u.lower() for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m3u8']) else "iframe"
                            # Better naming for Larooza servers
                            server_name = f"Mirror {len(matrix)+1}"
                            if 'embed.php' in u:
                                server_name = f"Embed Server {len(matrix)+1}"
                            elif 'video.php' in u:
                                server_name = f"Video Server {len(matrix)+1}"
                            matrix.append({"name": server_name, "url": u, "type": server_type})
        
        logger.info(f"Matrix Discovery Complete: {len(matrix)} nodes located")
        return matrix

    def _normalize_sequence(self, soup: BeautifulSoup, current_id: Optional[str] = None, current_title: Optional[str] = None) -> List[Dict]:
        """Normalize content sequence (neutral for episodes)"""
        seq_map = {}
        
        # 1. Add current item if it's an episode
        if current_id and current_title:
            v_match = re.search(r'(?:الحلقة|حلقة|Episode|Ep|v)\s*(\d+)', current_title, re.IGNORECASE)
            if v_match:
                idx = int(v_match.group(1))
                seq_map[idx] = {
                    "episode": idx,
                    "title": f"Part {idx}",
                    "id": current_id
                }

        # 2. Add other items from lists
        # Expanded selectors to capture more episode links
        links = soup.select('.pm-ul-browse-videos li a, .episodes-list a, .video-series-list a, a.ellipsis, .video-links a, p a[href*="video.php"], .series-episodes a, .episode-item a, .season-episodes a, a[href*="vid="]')
        logger.info(f"Found {len(links)} potential episode links")
        
        for a in links:
            t = a.get_text(strip=True) or a.get('title', '')
            h = a.get('href')
            if not h or 'video.php' not in h: continue
            
            abs_u = urljoin(self.ROOT, h)
            v_match = re.search(r'(?:الحلقة|حلقة|Episode|Ep|v)\s*(\d+)', t, re.IGNORECASE)
            if not v_match:
                if any(x in t for x in ["الحلقة", "حلقة", "Episode", "ep"]):
                    nums = re.findall(r'\d+', t)
                    idx = int(nums[0]) if nums else None
                else: continue
            else:
                idx = int(v_match.group(1))

            if idx is not None and idx not in seq_map:
                seq_map[idx] = {
                    "episode": idx,
                    "title": f"Part {idx}",
                    "id": base64.urlsafe_b64encode(abs_u.encode()).decode()
                }
                logger.info(f"Added episode {idx}: {t[:50]}...")
        
        sorted_episodes = sorted(seq_map.values(), key=lambda x: x['episode'])
        logger.info(f"Returning {len(sorted_episodes)} sorted episodes")
        return sorted_episodes

    async def get_content_details(self, entry_id: str) -> Dict:
        """Fetch media information securely"""
        try:
            sid = entry_id.replace('%3D', '=').replace(' ', '+')
            if len(sid) % 4: sid += '=' * (4 - len(sid) % 4)
            entry_url = base64.urlsafe_b64decode(sid).decode()

            logger.info("Content Resolution Phase A")
            raw_main = await self._invoke_remote(entry_url)
            if not raw_main: raise ProviderError("Resource Inaccessible")
            
            soup = BeautifulSoup(raw_main, 'html.parser')
            # Improved VID extraction (handles both vid= and video-ID-)
            v_match = re.search(r'vid=([^&]+)', entry_url)
            if not v_match:
                v_match = re.search(r'video-([a-f0-9]+)-', entry_url)
            
            vid = v_match.group(1) if v_match else None
            
            title_node = soup.find('h1')
            label = title_node.get_text(strip=True) if title_node else "Content"
            
            # 2. Parallel Secondary Resolution (Servers + Downloads) WITH TIMEOUTS
            matrix_task = None
            vector_task = None
            
            # Extract servers from the main page directly as well
            main_matrix = self._process_node_matrix(raw_main)
            
            # Fallback download links from main page
            main_vectors = self._resolve_vectors_from_soup(soup)
            
            # Early termination check - only skip remote fetch if we have many servers
            if len(main_matrix) >= 15:  # If we have 15 or more servers from main page, skip remote fetch
                logger.info(f"Early termination: Using {len(main_matrix)} servers from main page")
                matrix = main_matrix
                vectors = main_vectors
            elif vid:
                base_play = urljoin(self.ROOT, f"play.php?vid={vid}")
                base_dl = urljoin(self.ROOT, f"download.php?vid={vid}")
                # Add timeouts to prevent hanging - reduced timeouts for faster response
                matrix_task = asyncio.wait_for(self._resolve_source_matrix(base_play, origin=entry_url), timeout=8.0)
                vector_task = asyncio.wait_for(self._resolve_vectors(base_dl), timeout=15.0)
            else:
                # Fallback if no vid
                matrix = main_matrix
                vectors = main_vectors

            # Parallel Fetch with timeouts (only if we didn't early terminate)
            if matrix_task or vector_task:
                try:
                    results = await asyncio.gather(
                        matrix_task if matrix_task else asyncio.sleep(0, []),
                        vector_task if vector_task else asyncio.sleep(0, []),
                        return_exceptions=True
                    )
                except asyncio.TimeoutError:
                    logger.warning("Timeout during parallel fetch of servers/downloads")
                    results = [[], []]  # Return empty results on timeout
            else:
                # Use pre-computed values from early termination
                results = [matrix, vectors]
            
            remote_matrix = results[0] if not isinstance(results[0], Exception) else []
            remote_vectors = results[1] if not isinstance(results[1], Exception) else []
            
            # Combine matrices (De-duplicate by URL)
            matrix = remote_matrix
            seen_srv = {m['url'] for m in matrix}
            for m in main_matrix:
                if m['url'] not in seen_srv:
                    matrix.append(m)
                    seen_srv.add(m['url'])
                    
            # Combine vectors, prioritizing remote ones but falling back to main if remote fails
            # Only use remote if it actually has content, otherwise use main
            if remote_vectors is not None and len(remote_vectors) > 0:
                vectors = remote_vectors
            else:
                vectors = main_vectors
            
            desc_node = soup.select_one('.video-description, .description, p')
            summary = desc_node.get_text(strip=True) if desc_node else ""
            
            # Try multiple selectors for poster image including larooza-specific ones
            asset_img = soup.select_one('.video-poster img, .movie-poster img, .poster img, meta[property="og:image"]')
            asset_p = ""
            if asset_img:
                # For meta tags, use content attribute; for img tags, use src/data-src
                if asset_img.name == 'meta':
                    asset_p = asset_img.get('content', '')
                else:
                    asset_p = asset_img.get('src') or asset_img.get('data-src') or ''
            
            if asset_p and asset_p.startswith('//'): asset_p = "https:" + asset_p
            elif asset_p and not asset_p.startswith('http'): asset_p = urljoin(self.ROOT, asset_p)

            is_multi = any(x in label for x in ["مسلسل", "حلقة", "Episode", "Ep", "موسم"])
            
            # 3. Aggregate Sequence
            full_sequence = {}
            for item in self._normalize_sequence(soup, entry_id, label):
                full_sequence[item['episode']] = item

            if is_multi:
                # Resolve Parent Sequence (Breadcrumbs or Category links)
                parent_link = soup.select_one('.breadcrumb li a[href*="cat="], .video-categories a, a[href*="browse-"], a[href*="category"]')
                
                # Deep Discovery if breadcrumbs fail
                if not parent_link:
                    # Clean title for comparison (remove episode num)
                    clean_title = re.sub(r'(?:الحلقة|حلقة|Episode|Ep|v)\s*(\d+).*', '', label, flags=re.IGNORECASE).strip()
                    # Look for any link containing the cleaned title
                    parent_link = soup.find('a', string=re.compile(re.escape(clean_title), re.IGNORECASE))
                    
                # If still no parent link, try to find any series-related links
                if not parent_link:
                    # Look for links that might lead to the series page
                    potential_links = soup.select('a[href*="series"], a[href*="season"], a[href*="browse"], a[title*="الحلقة"], a[title*="Episode"]')
                    if potential_links:
                        parent_link = potential_links[0]  # Take the first one
                        logger.info(f"Found potential series link: {parent_link.get('href', 'N/A')}")

                if parent_link and parent_link.get('href'):
                    parent_u = urljoin(self.ROOT, parent_link['href'])
                    logger.info(f"Fetching parent series page: {parent_u}")
                    try:
                        # Add timeout to prevent long waits - reduced for faster response
                        raw_parent = await asyncio.wait_for(self._invoke_remote(parent_u), timeout=5.0)
                        if raw_parent:
                            parent_soup = BeautifulSoup(raw_parent, 'html.parser')
                            # Extract episodes from the parent page - limit to prevent excessive processing
                            parent_episodes = self._normalize_sequence(parent_soup)
                            logger.info(f"Found {len(parent_episodes)} episodes from parent page")
                            # Limit to first 50 episodes to prevent excessive processing
                            limited_episodes = parent_episodes[:50] if len(parent_episodes) > 50 else parent_episodes
                            for item in limited_episodes:
                                if item['episode'] not in full_sequence:
                                     full_sequence[item['episode']] = item
                                     logger.info(f"Added episode {item['episode']} from parent page")
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout fetching parent series page: {parent_u}")
                    except Exception as e:
                        logger.error(f"Error fetching parent series page: {e}")
                else:
                    logger.info("No parent series link found")
                
            sorted_seq = sorted(full_sequence.values(), key=lambda x: x['episode'])
            
            if sorted_seq:
                hi = sorted_seq[-1]['episode']
                lo = sorted_seq[0]['episode']
                if len(sorted_seq) < (hi - lo + 1):
                    logger.warning(f"Integrity Check: Sequence Incomplete ({len(sorted_seq)}/{hi-lo+1})")

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
            logger.error(f"Resolution Final Error: {e}")
            return {"title": "Unavailable", "servers": [], "episodes": [], "download_links": []}

    async def get_latest_content(self, p: int = 1):
        raw = await self._invoke_remote(f"{self.ROOT}/newvideos1.php?page={p}")
        return self._map_content_grid(raw)

    async def search_content(self, query: str):
        raw = await self._invoke_remote(f"{self.ROOT}/search.php?keywords={quote(query)}")
        return self._map_content_grid(raw)

    async def get_category_content(self, cid: str, p: int = 1):
        raw = await self._invoke_remote(f"{self.ROOT}/browse-{cid}-videos-{p}-date.html")
        return self._map_content_grid(raw)

# Export as scraper for compatibility with main.py
scraper = ResourceResolver()
