"""Quick test for the new multi-tier scraping engine"""
import asyncio
import sys
import os

# Disable uvloop on Windows
os.environ['UVLOOP'] = '0'

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_engine():
    from scraper.engine import scraper
    
    print("=" * 60)
    print("TESTING MULTI-TIER SCRAPING ENGINE")
    print("=" * 60)
    
    # Test 1: Get latest content
    print("\n[TEST 1] Fetching latest content...")
    try:
        content = await scraper.get_latest_content(p=1)
        print(f"  Result: {len(content)} items found")
        if content:
            print(f"  First item: {content[0].get('title', 'N/A')[:50]}...")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 2: Search
    print("\n[TEST 2] Search test...")
    try:
        results = await scraper.search_content("movie")
        print(f"  Result: {len(results)} items found")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 3: Stats
    print("\n[TEST 3] Engine statistics...")
    stats = scraper.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_engine())
