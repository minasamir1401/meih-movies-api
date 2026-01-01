import asyncio
import sys
import io
from scraper.engine import scraper
from bs4 import BeautifulSoup

# Set encoding for Windows terminal
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_scraper_logic():
    # Test with the HTML we just saved from FlareSolverr
    try:
        with open("flaresolverr_output.html", "r", encoding="utf-8") as f:
            html = f.read()
        
        print(f"Testing extraction from saved HTML (length: {len(html)})...")
        soup = BeautifulSoup(html, 'html.parser')
        items = scraper._extract_items(soup)
        
        print(f"Extracted {len(items)} items.")
        for i, item in enumerate(items[:5]):
            print(f"{i+1}. {item['title']} - {item['type']}")
            print(f"   Poster: {item['poster'][:50]}...")
            
        if not items:
            print("[X] No items extracted! Checking container selectors...")
            # Debug selectors
            selectors = ['.thumbnail', '.pm-li-video', '.pm-video-thumb', '.video-block', '.movie-item', 'li.col-xs-6', '.box', '.video-box', '.video-item', '.post-item']
            for sel in selectors:
                found = soup.select(sel)
                print(f"Selector '{sel}': found {len(found)} elements")
                
    except FileNotFoundError:
        print("[X] flaresolverr_output.html not found. Run test_flaresolverr_direct.py first.")
    except Exception as e:
        print(f"[X] Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraper_logic())
