#!/usr/bin/env python3
"""
Headless Browser Scraper Implementation

This implementation uses Playwright with Chromium in headless mode for ultra-fast scraping.
It's much faster than proxy-based solutions and doesn't require API credits.
"""

import asyncio
import base64
import re
import time
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("headless_scraper")

class HeadlessScraper:
    def __init__(self):
        self.browser = None
        self.playwright = None
        self.ROOT = "https://larooza.site"
        
    async def init_browser(self):
        """Initialize the headless browser"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            
        if not self.browser:
            # Launch Chromium in headless mode with optimizations
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
        logger.info("Headless browser initialized")
        
    async def close_browser(self):
        """Close the browser and cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def fetch_page(self, url, timeout=10000):
        """
        Fetch a page using headless browser
        timeout: milliseconds (10 seconds default)
        """
        if not self.browser:
            await self.init_browser()
            
        try:
            # Create a new context with optimized settings
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True
            )
            
            # Create a new page
            page = await context.new_page()
            
            # Navigate to the URL with timeout
            logger.info(f"Navigating to: {url}")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            
            # Wait a bit for dynamic content to load
            await page.wait_for_timeout(2000)
            
            # Get the page content
            content = await page.content()
            
            # Close the page and context
            await page.close()
            await context.close()
            
            logger.info(f"Successfully fetched {len(content)} characters from {url}")
            return content
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""
            
    def _process_node_matrix(self, raw_html: str) -> list:
        """Process server nodes from HTML (same logic as before but faster)"""
        if not raw_html: 
            return []
            
        s = BeautifulSoup(raw_html, 'html.parser')
        matrix = []
        
        # 1. Primary Vector (iframe)
        f = s.find('iframe')
        if f:
            src = f.get('src') or f.get('data-src')
            if src:
                if not src.startswith('http'): 
                    src = urljoin(self.ROOT, src)
                matrix.append({"name": "Main Player", "url": src, "type": "iframe"})
        
        # 2. Secondary Matrix (Traditional Selectors + Larooza specific)
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
                    item.get('data-embed-id')
                
                if not u and item.name != 'a':
                    a = item.find('a')
                    if a: 
                        u = a.get('href') or a.get('data-url') or a.get('data-vid')
                
                if u and 'javascript' not in u.lower():
                    # Handle URLs
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
                               
                        # Only filter out social media
                        if not any(x in u.lower() for x in ['facebook', 'twitter']):
                            if not any(m['url'] == u for m in matrix):
                                matrix.append({"name": name, "url": u, "type": "iframe"})
        
        logger.info(f"Matrix Discovery Complete: {len(matrix)} nodes located")
        return matrix
        
    def _resolve_vectors_from_soup(self, s: BeautifulSoup) -> list:
        """Extract download vectors from soup (same logic as before but faster)"""
        vectors = []
        seen = set()
        
        # SPECIAL CASE: Larooza download page structure
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
                quality = domain if domain else f"Download Server {len(vectors)+1}"
                
                abs_u = urljoin(self.ROOT, u) if not u.startswith('http') else u
                abs_u = abs_u.strip()
                
                if abs_u not in seen:
                    seen.add(abs_u)
                    vectors.append({"quality": quality, "url": abs_u})
        
        # If we found larooza-specific download links, return them immediately
        if len(vectors) > 0:
            logger.info(f"Found {len(vectors)} Larooza download vectors")
            return vectors
            
        # Enhanced selectors for download links
        selectors = [
            'a[href*="download"]', 'a[href*="multiup"]', 'a[href*="php?id="]', 
            'a[href*="mp4"]', 'a[href*="mkv"]', '.download-link', 'table a[href]', 
            'ul.downloadlist li', '.download-buttons a', '.dl-btn',
            'a.btn-download', 'a[href*="get_file"]', 'a[href*="direct"]',
            '.mirror a', '.mirrors a', 'a[data-file]', 'a[download]',
            '.download-servers a', '.download-options a', '.dl-option a'
        ]
        
        tags = []
        for selector in selectors:
            tags.extend(s.select(selector))
        
        for item in tags:
            u = item.get('href')
            if not u: 
                u = item.get('data-href') or item.get('data-link') or item.get('onclick')
                if u and 'location.href' in u:
                    match = re.search(r"location\\.href=['\"]([^'\"]+)['\"]", u)
                    if match:
                        u = match.group(1)
            
            if not u: 
                continue
                
            abs_u = urljoin(self.ROOT, u) if not u.startswith('http') else u
            abs_u = abs_u.strip()
            
            # Clean up onclick URLs
            if abs_u.startswith('javascript:'):
                match = re.search(r"['\"]([^'\"]+)['\"]", abs_u)
                if match:
                    abs_u = match.group(1)
                    abs_u = urljoin(self.ROOT, abs_u) if not abs_u.startswith('http') else abs_u
            
            if abs_u not in seen:
                has_video_extension = any(x in abs_u.lower() for x in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m3u8'])
                has_download_indicator = any(x in abs_u.lower() for x in ['download', 'multiup', 'get_file', 'direct'])
                
                is_download_link = has_video_extension or has_download_indicator
                
                excluded_patterns = [
                    'facebook', 'twitter', 'whatsapp', 'mailto:', 'javascript:', '#',
                    '/home', '/gaza', '/category', '/section', '/browse', '/search',
                    'home.24', 'gaza.20', 'most-watched', 'topvideos', 'newvideos'
                ]
                
                if is_download_link and not any(x in abs_u.lower() for x in excluded_patterns) and abs_u != self.ROOT: 
                    seen.add(abs_u)
                    label = item.get_text(strip=True) or item.get('title') or item.get('data-title') or "Download"
                    
                    if not label or len(label) < 3 or any(x in label.lower() for x in ['download', 'تحميل', 'link', 'high', 'quality']):
                        if '1080' in abs_u:
                            label = '1080p'
                        elif '720' in abs_u:
                            label = '720p'
                        elif '480' in abs_u:
                            label = '480p'
                        elif '360' in abs_u:
                            label = '360p'
                        else:
                            has_video_indicators = any(x in abs_u.lower() for x in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m3u8', 'download', 'multiup', 'get_file'])
                            if has_video_indicators:
                                label = f"Download Link {len(vectors)+1}"
                            else:
                                continue
                    
                    vectors.append({"quality": label, "url": abs_u})
        
        logger.info(f"Found {len(vectors)} download vectors")
        return vectors
        
    async def get_content_details(self, entry_id: str) -> dict:
        """Get content details using headless browser (much faster!)"""
        try:
            # Decode entry ID
            sid = entry_id.replace('%3D', '=').replace(' ', '+')
            if len(sid) % 4: 
                sid += '=' * (4 - len(sid) % 4)
            entry_url = base64.urlsafe_b64decode(sid).decode()
            
            logger.info(f"Fetching content details for: {entry_url}")
            
            # Fetch main page using headless browser (MUCH FASTER!)
            raw_main = await self.fetch_page(entry_url, timeout=15000)
            if not raw_main: 
                return {"title": "Unavailable", "servers": [], "episodes": [], "download_links": []}
                
            soup = BeautifulSoup(raw_main, 'html.parser')
            
            # Extract VID
            v_match = re.search(r'vid=([^&]+)', entry_url)
            if not v_match:
                v_match = re.search(r'video-([a-f0-9]+)-', entry_url)
            vid = v_match.group(1) if v_match else None
            
            # Get title
            title_node = soup.find('h1')
            label = title_node.get_text(strip=True) if title_node else "Content"
            
            # Extract servers from main page
            main_matrix = self._process_node_matrix(raw_main)
            
            # Extract download links from main page
            main_vectors = self._resolve_vectors_from_soup(soup)
            
            # Fetch play page if we have VID (using headless browser - FAST!)
            remote_matrix = []
            if vid:
                base_play = urljoin(self.ROOT, f"play.php?vid={vid}")
                logger.info(f"Fetching play page: {base_play}")
                raw_play = await self.fetch_page(base_play, timeout=10000)
                if raw_play:
                    remote_matrix = self._process_node_matrix(raw_play)
            
            # Combine matrices (De-duplicate by URL)
            matrix = remote_matrix[:]
            seen_srv = {m['url'] for m in matrix}
            for m in main_matrix:
                if m['url'] not in seen_srv:
                    matrix.append(m)
                    seen_srv.add(m['url'])
            
            # Get download page if we have VID (using headless browser - FAST!)
            vectors = main_vectors
            if vid:
                base_dl = urljoin(self.ROOT, f"download.php?vid={vid}")
                logger.info(f"Fetching download page: {base_dl}")
                raw_dl = await self.fetch_page(base_dl, timeout=15000)
                if raw_dl:
                    dl_soup = BeautifulSoup(raw_dl, 'html.parser')
                    dl_vectors = self._resolve_vectors_from_soup(dl_soup)
                    if dl_vectors:
                        vectors = dl_vectors
            
            # Extract description
            desc_node = soup.select_one('.video-description, .description, p')
            summary = desc_node.get_text(strip=True) if desc_node else ""
            
            # Extract poster
            asset_img = soup.select_one('.video-poster img, .movie-poster img, .poster img, meta[property="og:image"]')
            asset_p = ""
            if asset_img:
                if asset_img.name == 'meta':
                    asset_p = asset_img.get('content', '')
                else:
                    asset_p = asset_img.get('src') or asset_img.get('data-src') or ''
            
            if asset_p and asset_p.startswith('//'): 
                asset_p = "https:" + asset_p
            elif asset_p and not asset_p.startswith('http'): 
                asset_p = urljoin(self.ROOT, asset_p)
            
            is_multi = any(x in label for x in ["مسلسل", "حلقة", "Episode", "Ep", "موسم"])
            
            return {
                "title": label,
                "type": "series" if is_multi else "movie",
                "description": summary,
                "poster": asset_p,
                "episodes": [],  # Simplified for this example
                "servers": matrix,
                "download_links": vectors
            }
            
        except Exception as e:
            logger.error(f"Error getting content details: {e}")
            return {"title": "Unavailable", "servers": [], "episodes": [], "download_links": []}

# Example usage
async def main():
    """Example usage of the headless scraper"""
    print("🚀 HEADLESS BROWSER SCRAPER DEMO")
    print("=" * 40)
    
    scraper = HeadlessScraper()
    
    try:
        # Initialize the browser
        await scraper.init_browser()
        
        # Test with a sample entry ID
        test_entry_id = "aHR0cHM6Ly9sYXJvb3phLnNpdGUvdmlkZW8ucGhwP3ZpZD0xZDViMjcxOTc="
        
        print("Fetching content details...")
        start_time = time.time()
        
        details = await scraper.get_content_details(test_entry_id)
        
        end_time = time.time()
        
        print(f"✅ Fetched in {end_time - start_time:.2f} seconds!")
        print(f"Title: {details.get('title', 'N/A')}")
        print(f"Servers: {len(details.get('servers', []))}")
        print(f"Download links: {len(details.get('download_links', []))}")
        
        # Show servers
        if details.get('servers'):
            print("\n📺 Servers found:")
            for i, server in enumerate(details['servers'][:5]):
                print(f"  {i+1}. {server['name']} - {server['url']}")
        
        # Show download links
        if details.get('download_links'):
            print("\n📥 Download links found:")
            for i, link in enumerate(details['download_links'][:5]):
                print(f"  {i+1}. {link['quality']} - {link['url']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always close the browser
        await scraper.close_browser()

if __name__ == "__main__":
    asyncio.run(main())