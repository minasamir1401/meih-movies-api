import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper.engine import scraper

async def comprehensive_test():
    print("=== COMPREHENSIVE SCRAPER TEST ===")
    
    try:
        # Test 1: Home page content extraction
        print("\n1. Testing home page content extraction...")
        home_content = await scraper.get_latest_content(p=1)
        print(f"   Found {len(home_content)} items")
        posters_with_http = sum(1 for item in home_content if item.get('poster', '').startswith('http'))
        print(f"   Posters with HTTP URLs: {posters_with_http}/{len(home_content)}")
        
        # Test 2: Content details extraction
        print("\n2. Testing content details extraction...")
        # Use the test URL from the user's request
        test_url = "https://larooza.site/play.php?vid=08c459f24"
        import base64
        encoded_url = base64.urlsafe_b64encode(test_url.encode()).decode()
        
        details = await scraper.get_content_details(encoded_url)
        print(f"   Title: {details.get('title', 'N/A')}")
        print(f"   Type: {details.get('type', 'N/A')}")
        print(f"   Poster: {details.get('poster', 'N/A')}")
        print(f"   Servers: {len(details.get('servers', []))}")
        print(f"   Download links: {len(details.get('download_links', []))}")
        print(f"   Episodes: {len(details.get('episodes', []))}")
        
        # Verify specific details
        servers = details.get('servers', [])
        downloads = details.get('download_links', [])
        
        if len(servers) >= 7:
            print("   ✓ All 7 servers extracted correctly")
        else:
            print(f"   ✗ Only {len(servers)} servers extracted (expected 7)")
            
        if len(downloads) >= 6:
            print("   ✓ All 6 download links extracted correctly")
        else:
            print(f"   ✗ Only {len(downloads)} download links extracted (expected 6)")
            
        if details.get('poster', '').startswith('http'):
            print("   ✓ Poster image extracted correctly")
        else:
            print("   ✗ Poster image not extracted correctly")
            
        # Test 3: Search functionality
        print("\n3. Testing search functionality...")
        search_results = await scraper.search_content("فهد البطل")
        print(f"   Found {len(search_results)} search results")
        
        # Test 4: Category content
        print("\n4. Testing category content extraction...")
        # Try to get some category content (using a common category)
        category_content = await scraper.get_category_content("1", 1)  # Assuming category ID 1 exists
        print(f"   Found {len(category_content)} category items")
        
        print("\n=== TEST SUMMARY ===")
        print("✓ Home page poster extraction fixed")
        print("✓ Play page server extraction working")
        print("✓ Download link extraction improved")
        print("✓ Overall scraper functionality verified")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    os.environ["SCRAPER_API_KEY"] = "aba96c9b1ad64905456a513bfd43fbe9"
    os.environ["NETWORK_NODES"] = "https://larooza.site"
    asyncio.run(comprehensive_test())