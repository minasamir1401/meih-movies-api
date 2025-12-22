"""
Optimized Headless Browser Scraper with Playwright

This implementation focuses on:
1. Maximum speed and reliability
2. Ad blocking and resource optimization
3. Proper handling of JavaScript-rendered content
4. Session persistence for faster repeated loads
5. Anti-bot detection measures
"""

import asyncio
import logging
import random
import re
import sys
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Fix for Windows asyncio issue with subprocesses
if sys.platform == 'win32':
    try:
        from asyncio import WindowsProactorEventLoopPolicy, set_event_loop_policy
        set_event_loop_policy(WindowsProactorEventLoopPolicy())
    except ImportError:
        pass

# Configure logging
logger = logging.getLogger("optimized_scraper")
logger.setLevel(logging.INFO)

class OptimizedHeadlessScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.contexts = []  # Track browser contexts for cleanup
        self.browser_semaphore = asyncio.Semaphore(3)  # Limit concurrent browser instances
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Resource management
        self._last_cleanup = time.time()
        
        # Domains to block for ad/tracker blocking
        self.blocked_domains = [
            'doubleclick.net',
            'googlesyndication.com',
            'googleadservices.com',
            'googletagservices.com',
            'facebook.net',
            'facebook.com',
            'twitter.com',
            'youtube.com',
            'youtube-nocookie.com',
            'amazon-adsystem.com',
            'scorecardresearch.com',
            'quantserve.com',
            'advertising.com',
            'adservice.google.com',
            'googletagmanager.com',
            'analytics.google.com',
            'hotjar.com',
            'mouseflow.com',
            'fullstory.com',
            'segment.com',
            'intercom.io',
            'zendesk.com',
            'crashlytics.com',
            'fabric.io',
            'mixpanel.com',
            'newrelic.com',
            'datadoghq.com',
            'sentry.io',
            'rollbar.com',
            'bugsnag.com',
            'pubmatic.com',
            'rubiconproject.com',
            'openx.net',
            'adnxs.com',
            'casalemedia.com',
            'contextweb.com',
            'dotomi.com',
            'sharethrough.com',
            'sonobi.com',
            'teads.tv',
            'tribalfusion.com',
            'yieldmo.com',
            'zedo.com',
            '3lift.com',
            'adform.net',
            'adtechus.com',
            'atwola.com',
            'bidswitch.net',
            'criteo.com',
            'emxdgt.com',
            'exelator.com',
            'mathtag.com',
            'pulsepoint.com',
            'revcontent.com',
            'simpli.fi',
            'smartadserver.com',
            'taboola.com',
            'zemanta.com',
            'outbrain.com',
            'taboola.com',
            'parsely.com',
            'chartbeat.com',
            'comscore.com',
            'krxd.net',
            'adsafeprotected.com',
            'moatads.com',
            'sitescout.com',
            'lkqd.net',
            'spotxchange.com',
            'freewheel.tv',
            'brightcove.com',
            'ooyala.com',
            'theplatform.com',
            'vidible.tv',
            'vimeo.com',
            'dailymotion.com',
            'metacafe.com',
            'break.com',
            'veoh.com',
            'clipfish.de',
            'myvideo.de',
            'sevenload.com',
            'video.google.com',
            'photobucket.com',
            'flickr.com',
            'instagram.com',
            'snapchat.com',
            'tiktok.com',
            'linkedin.com',
            'pinterest.com',
            'reddit.com',
            'tumblr.com',
            'whatsapp.com',
            'wechat.com',
            'qq.com',
            'weibo.com',
            'baidu.com',
            'sohu.com',
            'sina.com.cn',
            'ifeng.com',
            'youku.com',
            'iqiyi.com',
            'tudou.com',
            'pptv.com',
            'letv.com',
            'mgtv.com',
            '163.com',
            'sogou.com',
            '360.cn',
            'alibaba.com',
            'taobao.com',
            'tmall.com',
            'jd.com',
            'amazon.com',
            'ebay.com',
            'walmart.com',
            'target.com',
            'bestbuy.com',
            'costco.com',
            'kohls.com',
            'macys.com',
            'nordstrom.com',
            'sears.com',
            'kmart.com',
            'jcpenney.com',
            'bloomingdales.com',
            'neimanmarcus.com',
            'saksfifthavenue.com',
            'barneys.com',
            'lordandtaylor.com',
            'dillards.com',
            'belk.com',
            'victoriassecret.com',
            'anntaylor.com',
            'chicos.com',
            'whitehouseblackmarket.com',
            'lanebryant.com',
            'ashleyfurniture.com',
            'ikea.com',
            'wayfair.com',
            'overstock.com',
            'hayneedle.com',
            'westelm.com',
            'potterybarn.com',
            'crateandbarrel.com',
            'williams-sonoma.com',
            'sur-la-table.com',
            'bedbathandbeyond.com',
            'lowes.com',
            'homedepot.com',
            'acehardware.com',
            'truevalue.com',
            'do it best.com',
            'build.com',
            'flooranddecor.com',
            'carpetright.co.uk',
            'tilesandlaminate.co.uk',
            'wallsandfloors.co.uk',
            'victorianplumbing.co.uk',
            'bathstore.com',
            'showerspas.co.uk',
            'bathroomsensations.co.uk',
            'tradingstandards.gov.uk',
            'financialconductauthority.gov.uk',
            'gov.uk',
            'nhs.uk',
            'bbc.co.uk',
            'telegraph.co.uk',
            'guardian.co.uk',
            'independent.co.uk',
            'mirror.co.uk',
            'sun.co.uk',
            'dailyrecord.co.uk',
            'heraldscotland.com',
            'thetimes.co.uk',
            'ft.com',
            'economist.com',
            'forbes.com',
            'bloomberg.com',
            'cnbc.com',
            'reuters.com',
            'wsj.com',
            'nytimes.com',
            'washingtonpost.com',
            'latimes.com',
            'chicagotribune.com',
            'boston.com',
            'seattletimes.com',
            'sfchronicle.com',
            'denverpost.com',
            'startribune.com',
            'ajc.com',
            'cleveland.com',
            'oregonlive.com',
            'philly.com',
            'post-gazette.com',
            'freep.com',
            'jsonline.com',
            'dispatch.com',
            'kansascity.com',
            'stltoday.com',
            'sandiegouniontribune.com',
            'dallasnews.com',
            'miamiherald.com',
            'orlandosentinel.com',
            'tampabay.com',
            'suntimes.com',
            'chicago.suntimes.com',
            'newsday.com',
            'nypost.com',
            'amny.com',
            'si.com',
            'sportsillustrated.cnn.com',
            'espn.com',
            'foxsports.com',
            'cbssports.com',
            'nbcsports.com',
            'mlb.com',
            'nba.com',
            'nfl.com',
            'nhl.com',
            'pga.com',
            'tennis.com',
            'golf.com',
            'olympics.com',
            'fifa.com',
            'uefa.com',
            'motogp.com',
            'formula1.com',
            'nascar.com',
            'ufc.com',
            'wwe.com',
            'boxing.com',
            'mmafighting.com',
            'bleacherreport.com',
            'theathletic.com',
            'athletic.net',
            'maxpreps.com',
            'hudl.com',
            'gamechanger.io',
            'sports-reference.com',
            'baseball-reference.com',
            'basketball-reference.com',
            'football-reference.com',
            'hockey-reference.com',
            'soccerway.com',
            'transfermarkt.com',
            'goal.com',
            'skysports.com',
            'talksport.com',
            'radio5live.co.uk',
            'bbc.co.uk/sport',
            'itv.com/hub/itvbe',
            'channel4.com',
            'channel5.com',
            'sky.com',
            'bt.com',
            'virginmedia.com',
            'talktalk.co.uk',
            'plus.net',
            'aa.net.uk',
            'zen.co.uk',
            ' Andrews & Arnold',
            'clara.net',
            'pipex.com',
            'easynews.com',
            'news.com.au',
            'smh.com.au',
            'theage.com.au',
            'brisbanetimes.com.au',
            'watoday.com.au',
            'perthnow.com.au',
            'adelaidenow.com.au',
            'ntnews.com.au',
            'theadvocate.com.au',
            'examiner.com.au',
            'couriermail.com.au',
            'goldcoastbulletin.com.au',
            'dailymercury.com.au',
            'frasercoastchronicle.com.au',
            'gympietimes.com.au',
            'heraldsun.com.au',
            'weeklytimesnow.com.au',
            'townsvillebulletin.com.au',
            'cairnspost.com.au',
            'dailyexaminer.com.au',
            'northerndailyleader.com.au',
            'armidaleexpress.com.au',
            'bordermail.com.au',
            'dailyliberal.com.au',
            'illawarramercury.com.au',
            'newcastleherald.com.au',
            'portlincolntimes.com.au',
            'standard.net.au',
            'theadvocate.com.au',
            'thecourier.com.au',
            'westernadvocate.com.au',
            'themorningbulletin.com.au',
            'maitlandmercury.com.au',
            'northernstar.com.au',
            'sunshinecoastdaily.com.au',
            'gladstoneobserver.com.au',
            'mackaydailymercury.com.au',
            'rockhamptonmorningbulletin.com.au',
            'dailynews.toowoomba.com.au',
            'warwickdailynews.com.au',
            'chronicleonline.com.au',
            'moretonbayregion.com.au',
            'redlandcitybulletin.com.au',
            'logancitybulletin.com.au',
            'goldcoastbulletin.com.au',
            'sunshinecoastdaily.com.au',
            'frasercoastchronicle.com.au',
            'gympietimes.com.au',
            'dailymercury.com.au',
            'mackaydailymercury.com.au',
            'rockhamptonmorningbulletin.com.au',
            'gladstoneobserver.com.au',
            'heraldsun.com.au',
            'weeklytimesnow.com.au',
            'townsvillebulletin.com.au',
            'cairnspost.com.au',
            'dailyexaminer.com.au',
            'northerndailyleader.com.au',
            'armidaleexpress.com.au',
            'bordermail.com.au',
            'dailyliberal.com.au',
            'illawarramercury.com.au',
            'newcastleherald.com.au',
            'portlincolntimes.com.au',
            'standard.net.au',
            'theadvocate.com.au',
            'thecourier.com.au',
            'westernadvocate.com.au',
            'themorningbulletin.com.au',
            'maitlandmercury.com.au',
            'northernstar.com.au',
            'sunshinecoastdaily.com.au',
            'gladstoneobserver.com.au',
            'mackaydailymercury.com.au',
            'rockhamptonmorningbulletin.com.au',
            'dailynews.toowoomba.com.au',
            'warwickdailynews.com.au',
            'chronicleonline.com.au',
            'moretonbayregion.com.au',
            'redlandcitybulletin.com.au',
            'logancitybulletin.com.au'
        ]

    async def init(self):
        """Initialize Playwright and browser with optimal settings and Windows compatibility"""
        try:
            if not self.playwright:
                logger.info("Starting Playwright...")
                self.playwright = await async_playwright().start()
                
            if not self.browser:
                logger.info("Launching Chromium browser with optimized settings...")
                
                # Platform-specific browser arguments
                browser_args = [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
                
                # Windows-specific adjustments
                if sys.platform == 'win32':
                    # Remove sandbox arguments on Windows as they can cause issues
                    browser_args = [arg for arg in browser_args if not arg.startswith('--no-sandbox') and not arg.startswith('--disable-setuid-sandbox')]
                    logger.info("Adjusted browser arguments for Windows platform")
                
                self.browser = await self.playwright.chromium.launch(
                    headless=True,  # Run in headless mode for server environments
                    args=browser_args
                )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize headless browser: {e}")
            # Try fallback initialization without problematic arguments
            try:
                if self.playwright and not self.browser:
                    logger.info("Trying fallback browser initialization...")
                    self.browser = await self.playwright.chromium.launch(headless=True)
                    logger.info("Fallback browser initialization successful")
                    return True
            except Exception as fallback_error:
                logger.error(f"Fallback browser initialization also failed: {fallback_error}")
            return False

    async def close(self):
        """Close browser and Playwright"""
        # Close all contexts first
        for context in self.contexts:
            try:
                await context.close()
            except Exception as e:
                logger.warning(f"Error closing browser context: {e}")
        self.contexts.clear()
        
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def cleanup_resources(self):
        """Periodically clean up unused resources"""
        current_time = time.time()
        if current_time - self._last_cleanup > 300:  # Every 5 minutes
            # Close old contexts
            for context in self.contexts[:]:  # Copy the list to avoid modification during iteration
                try:
                    await context.close()
                except Exception as e:
                    logger.warning(f"Error closing browser context during cleanup: {e}")
            self.contexts.clear()
            self._last_cleanup = current_time
            logger.info("Performed periodic browser resource cleanup")

    async def fetch(self, url: str, timeout: int = 15000, wait_time: int = 5000) -> str:
        """
        Fetch page content with optimized settings for speed and reliability
        
        Args:
            url: URL to fetch
            timeout: Maximum time to wait for page load (milliseconds)
            wait_time: Time to wait for dynamic content (milliseconds)
        """
        # Limit concurrent browser usage
        async with self.browser_semaphore:
            if not self.browser:
                if not await self.init():
                    logger.error("Failed to initialize browser")
                    return ""

            context = None
            page = None
            try:
                # Create context with optimized settings
                context = await self.browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                    java_script_enabled=True,
                    bypass_csp=True,
                    ignore_https_errors=True
                )
                # Track context for cleanup
                self.contexts.append(context)
            
                # Add stealth scripts to avoid detection
                await context.add_init_script("""
                    // Hide webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // Hide plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Hide languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    // Override chrome property
                    window.chrome = {
                        runtime: {},
                    };
                    
                    // Override permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                """)
                
                # Set realistic headers
                await context.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                })
                
                # Block ads and trackers
                async def block_ads(route):
                    if any(domain in route.request.url for domain in self.blocked_domains):
                        await route.abort()
                    else:
                        await route.continue_()
                
                await context.route("**/*", block_ads)
                
                # Create page
                page = await context.new_page()
                
                # Set timeouts
                page.set_default_timeout(timeout)
                page.set_default_navigation_timeout(timeout)
                
                logger.info(f"Navigating to: {url}")
                
                # Navigate to URL with redirect handling
                try:
                    response = await page.goto(url, wait_until='load', timeout=timeout)
                    logger.info(f"Page loaded with status: {response.status if response else 'Unknown'}")
                except Exception as e:
                    logger.warning(f"Initial navigation failed: {e}")
                    # Try with reduced timeout
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=min(timeout, 5000))
                    logger.info(f"Page loaded with status: {response.status if response else 'Unknown'}")
                
                # Wait for dynamic content
                await page.wait_for_timeout(wait_time)
                
                # Handle meta refresh redirects
                content = await page.content()
                redirect_attempts = 0
                max_redirects = 3
                
                while content and '<meta' in content.lower() and 'refresh' in content.lower() and 'url=' in content.lower() and redirect_attempts < max_redirects:
                    refresh_match = re.search(r'<meta[^>]*http-equiv=["\']?refresh["\']?[^>]*content=["\']?\d*;\s*url=([^"\'>]+)["\']?', content, re.IGNORECASE)
                    if refresh_match:
                        redirect_url = refresh_match.group(1).strip('"\'')
                        logger.info(f"Found meta refresh redirect to: {redirect_url}")
                        
                        # Make sure it's a full URL
                        if redirect_url.startswith('/'):
                            parsed = urlparse(url)
                            base_url = f"{parsed.scheme}://{parsed.netloc}"
                            redirect_url = urljoin(base_url, redirect_url)
                        elif not redirect_url.startswith('http'):
                            redirect_url = urljoin(url, redirect_url)
                        
                        logger.info(f"Following meta refresh redirect to: {redirect_url}")
                        
                        # Navigate to the redirect URL
                        try:
                            redirect_response = await page.goto(redirect_url, wait_until='load', timeout=timeout)
                            logger.info(f"Redirect page loaded with status: {redirect_response.status if redirect_response else 'Unknown'}")
                        except Exception as e:
                            logger.warning(f"Redirect navigation failed: {e}")
                            # Try with reduced timeout
                            redirect_response = await page.goto(redirect_url, wait_until='domcontentloaded', timeout=min(timeout, 5000))
                            logger.info(f"Redirect page loaded with status: {redirect_response.status if redirect_response else 'Unknown'}")
                        
                        # Wait for dynamic content
                        await page.wait_for_timeout(wait_time)
                        
                        # Get updated content
                        content = await page.content()
                        redirect_attempts += 1
                    else:
                        break
                
                # Get final content
                # Use a more reliable approach to get content
                try:
                    # Wait for network idle with a shorter timeout
                    await page.wait_for_load_state('networkidle', timeout=min(timeout, 5000))
                except:
                    # If networkidle fails, continue anyway
                    pass
                
                # Try to get content multiple times if needed
                final_content = ""
                for attempt in range(3):
                    try:
                        final_content = await page.content()
                        if final_content:
                            break
                    except Exception as e:
                        logger.warning(f"Content fetch attempt {attempt+1} failed: {e}")
                        if attempt < 2:  # Don't wait on the last attempt
                            await page.wait_for_timeout(1000)  # Wait 1 second before retry
                
                if not final_content:
                    # Last resort: try to get content with a simple evaluation
                    try:
                        final_content = await page.evaluate("() => document.documentElement.outerHTML")
                    except Exception as e:
                        logger.error(f"Failed to get content via evaluation: {e}")
                
                logger.info(f"Successfully fetched {len(final_content)} characters")
                return final_content
                
            except Exception as e:
                logger.error(f"Navigation failed: {e}")
                return ""
            
            finally:
                # Close page and context
                try:
                    if page:
                        await page.close()
                    if context and context in self.contexts:
                        self.contexts.remove(context)
                        await context.close()
                except Exception as cleanup_error:
                    logger.warning(f"Error during cleanup: {cleanup_error}")

    async def extract_download_links(self, url: str) -> List[Dict]:
        """
        Extract download links from a page using optimized scraping
        
        Args:
            url: URL to extract download links from
            
        Returns:
            List of download links with quality information
        """
        try:
            content = await self.fetch(url)
            if not content:
                logger.warning(f"Empty content received for download links extraction: {url}")
                return []
                
            soup = BeautifulSoup(content, 'html.parser')
            vectors = []
            seen = set()
        except Exception as e:
            logger.error(f"Error initializing download links extraction for {url}: {e}")
            return []
        
        # SPECIAL CASE: Larooza download page structure with line-break handling
        download_list_items = soup.select('ul.downloadlist li')
        for item in download_list_items:
            # Handle broken data-download-url attributes that span multiple lines
            u = item.get('data-download-url')
            
            # If the attribute is broken (ends with newline), try to reconstruct it
            if u and u.endswith('\n'):
                # Look for the next sibling text that might contain the rest of the URL
                if item.get_text():
                    # Try to find the complete URL in the item's text
                    text_content = item.get_text()
                    # Look for URLs in the text that might be the continuation
                    url_matches = re.findall(r'https?://[^\s"<>]+', text_content)
                    if url_matches:
                        u = url_matches[0].strip()
            
            # Fallback to href if data-download-url is missing or broken
            if not u:
                a_tag = item.find('a')
                if a_tag:
                    u = a_tag.get('href')
                    # Handle broken href attributes
                    if u and u.endswith('\n'):
                        # Try to reconstruct from anchor text
                        if a_tag.get_text():
                            text_content = a_tag.get_text()
                            url_matches = re.findall(r'https?://[^\s"<>]+', text_content)
                            if url_matches:
                                u = url_matches[0].strip()
            
            if u:
                # Clean up the URL
                u = u.strip()
                # Remove any trailing newlines or extra characters
                u = re.sub(r'[\r\n\s]+$', '', u)
                
                # Skip obviously invalid URLs
                if len(u) < 10 or 'javascript:' in u.lower():
                    continue
                
                domain_match = re.search(r'https?://(?:www\.)?([^/]+)', u)
                domain = domain_match.group(1) if domain_match else ''
                
                # Get quality label from spans
                quality = ""
                spans = item.find_all('span')
                if spans:
                    # Look for descriptive text in spans
                    for span in spans:
                        span_text = span.get_text(strip=True)
                        if span_text and len(span_text) > 2 and not any(x in span_text.lower() for x in ['تحميل', 'click', 'here']):
                            quality = span_text
                            break
                
                # Fallback quality labels
                if not quality:
                    if domain:
                        quality = domain
                    elif '1080' in u:
                        quality = '1080p'
                    elif '720' in u:
                        quality = '720p'
                    elif '480' in u:
                        quality = '480p'
                    elif '360' in u:
                        quality = '360p'
                    else:
                        quality = f"Download Server {len(vectors)+1}"
                
                abs_u = urljoin(url, u) if not u.startswith('http') else u
                abs_u = abs_u.strip()
                
                # Validate URL
                if abs_u and abs_u not in seen and len(abs_u) > 10:
                    seen.add(abs_u)
                    vectors.append({"quality": quality, "url": abs_u})
        
        # If we found larooza-specific download links, return them immediately
        if len(vectors) > 0:
            logger.info(f"Found {len(vectors)} Larooza download vectors (enhanced)")
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
            tags.extend(soup.select(selector))
        
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
                
            abs_u = urljoin(url, u) if not u.startswith('http') else u
            abs_u = abs_u.strip()
            
            # Clean up onclick URLs
            if abs_u.startswith('javascript:'):
                match = re.search(r"['\"]([^'\"]+)['\"]", abs_u)
                if match:
                    abs_u = match.group(1)
                    abs_u = urljoin(url, abs_u) if not abs_u.startswith('http') else abs_u
            
            if abs_u not in seen:
                has_video_extension = any(x in abs_u.lower() for x in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m3u8'])
                has_download_indicator = any(x in abs_u.lower() for x in ['download', 'multiup', 'get_file', 'direct'])
                
                is_download_link = has_video_extension or has_download_indicator
                
                excluded_patterns = [
                    'facebook', 'twitter', 'whatsapp', 'mailto:', 'javascript:', '#',
                    '/home', '/gaza', '/category', '/section', '/browse', '/search',
                    'home.24', 'gaza.20', 'most-watched', 'topvideos', 'newvideos'
                ]
                
                if is_download_link and not any(x in abs_u.lower() for x in excluded_patterns) and abs_u != url: 
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

    async def extract_servers(self, url: str) -> List[Dict]:
        """
        Extract video streaming servers from a page
        
        Args:
            url: URL to extract servers from
            
        Returns:
            List of video servers with name and URL
        """
        try:
            content = await self.fetch(url)
            if not content:
                logger.warning(f"Empty content received for server extraction: {url}")
                return []
                
            soup = BeautifulSoup(content, 'html.parser')
            matrix = []
        except Exception as e:
            logger.error(f"Error initializing server extraction for {url}: {e}")
            return []
        
        # 1. Primary Vector (iframe)
        f = soup.find('iframe')
        if f:
            src = f.get('src') or f.get('data-src')
            if src:
                if not src.startswith('http'): 
                    src = urljoin(url, src)
                # Be less restrictive on main player - allow most URLs
                problematic_domains = ['okprime.site', 'film77.xyz']
                # Only filter out truly problematic domains
                if not any(domain in src.lower() for domain in problematic_domains):
                    matrix.append({"name": "Main Player", "url": src, "type": "iframe"})
                else:
                    logger.info(f"Skipping problematic main player URL: {src}")
        else:
            # If no iframe found, look for video URLs in the page content
            page_text = soup.get_text()
            video_patterns = [
                r'(?:https?://[^\s"]+embed\.php\?vid=[^\s"]+)',
                r'(?:https?://[^\s"]+video\.php\?vid=[^\s"]+)'
            ]
            for pattern in video_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    url_found = match.group(0)
                    # Filter out garbage URLs
                    if (url_found and url_found not in [m['url'] for m in matrix] and
                        'لم يتم إختيار' not in url_found and 'لم يتم العثور' not in url_found and
                        'no file' not in url_found.lower() and 'not found' not in url_found.lower()):
                        matrix.append({"name": "Dynamic Player", "url": url_found, "type": "iframe"})
        
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
            for item in soup.select(selector):
                # Try larooza-specific attributes first
                u = item.get('data-embed-url') or item.get('data-url') or \
                    item.get('href') or item.get('data-id') or \
                    item.get('data-vid') or item.get('data-link') or item.get('data-source') or \
                    item.get('data-embed-id')  # Added for larooza site
                
                if not u and item.name != 'a':
                    a = item.find('a')
                    if a: 
                        u = a.get('href') or a.get('data-url') or a.get('data-vid')
                
                if u and 'javascript' not in u.lower():
                    # Handle IDs vs URLs
                    if not u.startswith('http') and len(u) > 5:
                        if u.isalnum() and not '/' in u:
                            u = urljoin(url, f"play.php?vid={u}")
                        else:
                            u = urljoin(url, u)
                    elif not u.startswith('http') and u:
                         u = urljoin(url, u)
                            
                    if u and u.startswith('http'):
                        # Try to get a better name for larooza servers
                        name_elem = item.find('strong')
                        name = (name_elem.get_text(strip=True) if name_elem else '') or \
                               item.get_text(strip=True) or \
                               item.get('data-embed-id') or \
                               f"Server {len(matrix)+1}"
                        # Filter out known problematic domains and patterns - but be less restrictive
                        problematic_domains = ['okprime.site', 'film77.xyz']
                        # Allow more servers by reducing filtering
                        if any(x in u.lower() for x in ['facebook', 'twitter']) or \
                           any(domain in u.lower() for domain in problematic_domains):
                            logger.info(f"Skipping problematic server URL: {u}")
                            continue
                        if not any(m['url'] == u for m in matrix):
                            matrix.append({"name": name, "url": u, "type": "iframe"})

        # 3. Script Scan (Deep Discovery) - Enhanced for all server types
        scripts = soup.find_all('script')
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
                            if u.startswith('//'): 
                                u = "https:" + u
                            else: 
                                u = urljoin(url, u)
                                
                        # Filter out images, ROOT, and current page
                        if any(u.lower().endswith(x) for x in ['.jpg', '.png', '.webp', '.jpeg', '.gif', '.svg']):
                            continue
                        if u.rstrip('/') == url.rstrip('/'):
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

# Export instance for use
optimized_scraper = OptimizedHeadlessScraper()