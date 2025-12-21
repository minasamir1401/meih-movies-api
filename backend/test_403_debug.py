"""
Debug script to identify the root cause of 403 errors
"""

import asyncio
import httpx
import sys

# Windows asyncio fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_direct_request():
    """Test direct request without proxy"""
    print("\n=== TEST 1: Direct Request (No Proxy) ===")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Upgrade-Insecure-Requests': '1',
    }
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
            response = await client.get('https://larooza.site', headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Content Length: {len(response.text)}")
            print(f"Headers: {dict(response.headers)[:500] if len(str(response.headers)) > 500 else dict(response.headers)}")
            if response.status_code == 403:
                print(f"Response Body Preview: {response.text[:500]}")
            return response.status_code
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

async def test_curl_cffi():
    """Test with curl_cffi for TLS fingerprint bypass"""
    print("\n=== TEST 2: curl_cffi (TLS Fingerprint Bypass) ===")
    try:
        from curl_cffi.requests import AsyncSession
        async with AsyncSession() as session:
            response = await session.get('https://larooza.site', impersonate="chrome120", timeout=15)
            print(f"Status: {response.status_code}")
            print(f"Content Length: {len(response.text)}")
            if response.status_code == 403:
                print(f"Response Body Preview: {response.text[:500]}")
            return response.status_code
    except ImportError:
        print("curl_cffi not installed - pip install curl_cffi")
        return None
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

async def test_scraperapi_proxy():
    """Test with ScraperAPI proxy"""
    print("\n=== TEST 3: ScraperAPI Proxy ===")
    import os
    token = os.getenv("SCRAPER_API_KEY", "aba96c9b1ad64905456a513bfd43fbe9")
    proxy_url = f"http://scraperapi:{token}@proxy-server.scraperapi.com:8001"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=45.0, verify=False, follow_redirects=True) as client:
            response = await client.get('https://larooza.site', headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Content Length: {len(response.text)}")
            if response.status_code == 403:
                print(f"Response Body Preview: {response.text[:500]}")
            return response.status_code
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

async def test_scraperapi_render():
    """Test with ScraperAPI render mode"""
    print("\n=== TEST 4: ScraperAPI Render Mode ===")
    import os
    token = os.getenv("SCRAPER_API_KEY", "aba96c9b1ad64905456a513bfd43fbe9")
    proxy_url = f"http://scraperapi.render=true:{token}@proxy-server.scraperapi.com:8001"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=60.0, verify=False, follow_redirects=True) as client:
            response = await client.get('https://larooza.site', headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Content Length: {len(response.text)}")
            if response.status_code == 403:
                print(f"Response Body Preview: {response.text[:500]}")
            return response.status_code
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

async def test_playwright():
    """Test with Playwright headless browser"""
    print("\n=== TEST 5: Playwright Headless Browser ===")
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
            )
            
            # Add stealth script
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)
            
            page = await context.new_page()
            response = await page.goto('https://larooza.site', wait_until='load', timeout=30000)
            
            print(f"Status: {response.status if response else 'Unknown'}")
            content = await page.content()
            print(f"Content Length: {len(content)}")
            
            if response and response.status == 403:
                print(f"Response Body Preview: {content[:500]}")
            
            await browser.close()
            return response.status if response else None
    except ImportError:
        print("Playwright not installed - pip install playwright && playwright install chromium")
        return None
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

async def main():
    print("=" * 60)
    print("403 DEBUGGING ANALYSIS")
    print("=" * 60)
    
    results = {}
    
    results['direct'] = await test_direct_request()
    results['curl_cffi'] = await test_curl_cffi()
    results['scraperapi'] = await test_scraperapi_proxy()
    results['scraperapi_render'] = await test_scraperapi_render()
    results['playwright'] = await test_playwright()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for method, status in results.items():
        status_str = str(status) if status else "FAILED"
        emoji = "✓" if status == 200 else "✗" if status else "?"
        print(f"  {emoji} {method}: {status_str}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    
    if results.get('direct') == 403 and results.get('curl_cffi') == 200:
        print("  → TLS fingerprinting detected. Use curl_cffi or Playwright.")
    elif results.get('direct') == 403 and results.get('playwright') == 200:
        print("  → JavaScript challenge detected. Use Playwright fallback.")
    elif all(v == 403 for v in results.values() if v):
        print("  → IP/geo-based blocking. Need residential proxy or VPN.")
    elif results.get('scraperapi') == 403:
        print("  → ScraperAPI proxy may be blocked or rate-limited.")
    elif results.get('direct') == 200:
        print("  → Direct requests work! No anti-bot protection detected.")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
