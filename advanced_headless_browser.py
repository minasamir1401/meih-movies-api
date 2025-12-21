"""
Advanced Headless Browser with Anti-Bot Bypass

This implementation includes all the best practices to bypass 403 Forbidden errors:
1. Realistic browser profiles
2. Modern user agents
3. Proper HTTP headers
4. Stealth techniques
5. Human-like interactions
6. Proxy integration
"""

import asyncio
import random
import time
from urllib.parse import urljoin
import logging

# Try to import Playwright for headless browser
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available")

logger = logging.getLogger("advanced_scraper")

class AdvancedHeadlessBrowser:
    """Advanced headless browser with anti-bot bypass capabilities"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.user_agents = [
            # Real browser user agents to avoid detection
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
    async def init(self, proxy=None):
        """Initialize advanced headless browser with stealth features"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return False
            
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
                
            if not self.browser:
                # Launch browser with stealth arguments to avoid detection
                launch_args = [
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
                    '--disable-renderer-backgrounding'
                ]
                
                # Add proxy if provided
                if proxy:
                    launch_args.extend([f'--proxy-server={proxy}'])
                
                self.browser = await self.playwright.chromium.launch(
                    headless=False,  # Non-headless mode is less detectable
                    args=launch_args
                )
                
                logger.info("Advanced headless browser initialized with stealth features")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize advanced headless browser: {e}")
            return False
            
    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def fetch(self, url, proxy=None, timeout=30000):
        """Fetch page content with anti-bot bypass techniques"""
        logger.info(f"Fetching with advanced anti-bot bypass: {url}")
        
        if not self.browser:
            if not await self.init(proxy=proxy):
                return ""
                
        try:
            # Create context with realistic settings
            context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                java_script_enabled=True,
                bypass_csp=True,
                ignore_https_errors=True
            )
            
            # Add stealth headers to avoid detection
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
            """)
            
            # Create page
            page = await context.new_page()
            
            # Set realistic headers
            await page.set_extra_http_headers({
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
            
            # Navigate to page with human-like behavior
            logger.info(f"Navigating to: {url}")
            
            # First go to a common page to establish session
            await page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=10000)
            await page.wait_for_timeout(random.randint(1000, 3000))  # Random delay
            
            # Then navigate to target URL
            response = await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            
            if response and response.status != 200:
                logger.warning(f"Page loaded with status: {response.status}")
                
            # Simulate human behavior
            await self._simulate_human_behavior(page)
            
            # Wait for dynamic content
            await page.wait_for_timeout(random.randint(2000, 5000))
            
            # Get content
            content = await page.content()
            
            # Cleanup
            await page.close()
            await context.close()
            
            logger.info(f"Fetched {len(content)} characters successfully")
            return content
            
        except Exception as e:
            logger.error(f"Advanced fetch failed: {e}")
            return ""
            
    async def _simulate_human_behavior(self, page):
        """Simulate realistic human interactions to avoid bot detection"""
        try:
            # Random mouse movements
            viewport_size = await page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})")
            
            # Move mouse to random positions
            for _ in range(random.randint(3, 7)):
                x = random.randint(0, viewport_size['width'])
                y = random.randint(0, viewport_size['height'])
                await page.mouse.move(x, y)
                await page.wait_for_timeout(random.randint(100, 500))
                
            # Random scrolling
            scroll_height = await page.evaluate("() => document.body.scrollHeight")
            current_pos = 0
            while current_pos < scroll_height:
                scroll_amount = random.randint(100, 500)
                current_pos += scroll_amount
                await page.evaluate(f"window.scrollTo(0, {min(current_pos, scroll_height)})")
                await page.wait_for_timeout(random.randint(200, 1000))
                
            # Random delays to mimic human reading
            await page.wait_for_timeout(random.randint(1000, 3000))
            
        except Exception as e:
            logger.warning(f"Could not simulate human behavior: {e}")

# Enhanced scraper with fallback mechanisms
class EnhancedResourceResolver:
    """Enhanced resource resolver with multiple fallback strategies"""
    
    def __init__(self):
        self.headless = AdvancedHeadlessBrowser()
        self.proxies = [
            # Add proxy servers here if needed
            # "http://proxy1:port",
            # "http://proxy2:port"
        ]
        
    async def fetch_with_fallback(self, url, max_retries=3):
        """Fetch URL with multiple fallback strategies"""
        logger.info(f"Fetching with fallback strategies: {url}")
        
        # Strategy 1: Try with advanced headless browser
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries} with advanced headless browser")
                
                # Rotate proxies
                proxy = random.choice(self.proxies) if self.proxies else None
                
                content = await self.headless.fetch(url, proxy=proxy)
                if content and len(content) > 1000:  # Valid content should be substantial
                    logger.info("Successfully fetched with advanced headless browser")
                    return content
                    
                logger.warning(f"Advanced headless browser returned insufficient content ({len(content)} chars)")
                
            except Exception as e:
                logger.error(f"Advanced headless browser failed: {e}")
                
            # Wait before retry with exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0.1, 1.0)
                logger.info(f"Waiting {wait_time:.2f}s before retry...")
                await asyncio.sleep(wait_time)
        
        # Strategy 2: Try with different browser configurations
        logger.info("Trying alternative browser configurations")
        try:
            # Try with different user agent
            content = await self._fetch_with_alternative_config(url)
            if content and len(content) > 1000:
                return content
        except Exception as e:
            logger.error(f"Alternative configuration failed: {e}")
            
        logger.error("All fallback strategies failed")
        return ""
        
    async def _fetch_with_alternative_config(self, url):
        """Fetch with alternative browser configuration"""
        # Implementation for alternative configuration
        # This could include different viewport sizes, user agents, etc.
        pass

# Example usage
async def main():
    """Example usage of the advanced headless browser"""
    print("🚀 ADVANCED HEADLESS BROWSER WITH ANTI-BOT BYPASS")
    print("=" * 50)
    
    browser = AdvancedHeadlessBrowser()
    
    try:
        # Initialize browser
        success = await browser.init()
        if not success:
            print("❌ Failed to initialize browser")
            return
            
        print("✅ Browser initialized successfully")
        
        # Test with a sample URL
        test_url = "https://httpbin.org/html"
        print(f"🔍 Testing with: {test_url}")
        
        content = await browser.fetch(test_url)
        
        if content:
            print(f"✅ Successfully fetched {len(content)} characters")
            print(f"Preview: {content[:100]}...")
        else:
            print("❌ Failed to fetch content")
            
        # Close browser
        await browser.close()
        print("✅ Browser closed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())