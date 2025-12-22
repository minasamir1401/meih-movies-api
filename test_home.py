import asyncio
import os
import sys

sys.path.append(os.getcwd())
from scraper.engine import scraper

async def test_home():
    print("Testing fetch_home...")
    items = await scraper.fetch_home(page=1)
    print(f"Items found: {len(items)}")
    for item in items[:5]:
        print(f" - {item['title']} ({item['id'][:20]}...)")

if __name__ == "__main__":
    asyncio.run(test_home())
