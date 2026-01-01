import asyncio
import logging
from scraper.engine import scraper

async def test():
    logging.basicConfig(level=logging.INFO)
    print("Testing LaroozaScraper.fetch_home(1)...")
    try:
        items = await scraper.fetch_home(1)
        print(f"Success! Found {len(items)} items.")
        if items:
            print(f"First item: {items[0]['title']}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
