import asyncio
import sys
import os

# Add the current directory to path
sys.path.append(os.getcwd())

from scraper.engine import LaroozaScraper

# Set encoding to utf-8 for windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def test():
    scraper = LaroozaScraper()
    print("DEBUG: Fetching latest movies...")
    items = await scraper.fetch_home(page=1)
    print(f"DEBUG: Found {len(items)} items.")
    if items:
        for i, item in enumerate(items[:3]):
            print(f"  {i+1}. {item['title']} - ID: {item['id'][:20]}...")
    else:
        print("DEBUG: ❌ fetch_home returned 0 items.")

if __name__ == "__main__":
    asyncio.run(test())
