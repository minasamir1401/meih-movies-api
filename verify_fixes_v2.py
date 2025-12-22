import asyncio
import sys
import os

# Add the current directory to sys.path to import the scraper
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.scraper.engine import scraper

async def test_scraper():
    print("🚀 Testing Scraper Engine with new fixes...")
    print(f"📡 Primary Node: {scraper.ROOT}")
    
    try:
        # Test 1: Fetch Latest Content
        print("\n🔍 Fetching latest content...")
        latest = await scraper.get_latest_content(p=1)
        
        if latest and len(latest) > 0:
            print(f"✅ Success! Found {len(latest)} items.")
            print(f"📌 Sample Item: {latest[0]['title']}")
        else:
            print("❌ Failed to fetch latest content (empty list).")
            
        # Test 2: Search Content
        print("\n🔍 Testing search for 'طاش'...")
        search_res = await scraper.search_content("طاش")
        if search_res:
             print(f"✅ Search Success! Found {len(search_res)} items.")
        else:
             print("⚠️ Search returned empty (might be no results or blocked).")

    except Exception as e:
        print(f"💥 Critical Error during test: {e}")
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_scraper())
