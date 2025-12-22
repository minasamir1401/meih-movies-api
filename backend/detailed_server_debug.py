import asyncio
from backend.scraper.engine import scraper
from bs4 import BeautifulSoup
import re

async def detailed_server_debug():
    """Detailed debug of server extraction to pinpoint the issue"""
    
    print("=" * 60)
    print("DETAILED SERVER EXTRACTION DEBUG")
    print("=" * 60)
    
    # Test with the specific video URL from the user's query
    test_entry_id = "aHR0cHM6Ly9sYXJvb3phLnNpdGUvdmlkZW8ucGhwP3ZpZD0xZDViMjcxOTc="  # vid=1d5b27197
    
    try:
        # Decode the entry ID to get the actual URL
        import base64
        entry_url = base64.urlsafe_b64decode(test_entry_id + '=' * (-len(test_entry_id) % 4)).decode()
        print(f"Decoded URL: {entry_url}")
        
        # Extract VID
        v_match = re.search(r'vid=([^&]+)', entry_url)
        vid = v_match.group(1) if v_match else None
        print(f"Extracted VID: {vid}")
        
        if not vid:
            print("❌ Could not extract VID")
            return
        
        # Fetch play page
        base_play = f"https://larooza.site/play.php?vid={vid}"
        print(f"\nFetching play page: {base_play}")
        raw_play = await scraper._invoke_remote(base_play, extended=True)
        
        if not raw_play:
            print("❌ Failed to fetch play page")
            return
            
        print(f"✅ Successfully fetched play page ({len(raw_play)} characters)")
        
        # Manually process the servers like the _process_node_matrix function does
        s = BeautifulSoup(raw_play, 'html.parser')
        matrix = []
        
        print("\n--- MANUAL SERVER EXTRACTION ---")
        
        # Check the specific selectors we know should work
        selectors_to_check = ['ul.WatchList li', '[data-embed-url]']
        
        for selector in selectors_to_check:
            print(f"\nChecking selector: '{selector}'")
            items = s.select(selector)
            print(f"  Found {len(items)} items")
            
            for i, item in enumerate(items):
                # Try larooza-specific attributes first
                u = item.get('data-embed-url') or item.get('data-url') or \
                    item.get('href') or item.get('data-id') or \
                    item.get('data-vid') or item.get('data-link') or item.get('data-source') or \
                    item.get('data-embed-id')
                
                print(f"  Item {i+1}:")
                print(f"    Raw item: {str(item)[:100]}...")
                print(f"    data-embed-url: {item.get('data-embed-url')}")
                print(f"    data-embed-id: {item.get('data-embed-id')}")
                print(f"    Extracted URL: {u}")
                
                if not u:
                    print(f"    ❌ No URL found")
                    continue
                    
                if 'javascript' in u.lower():
                    print(f"    ❌ Skipping javascript URL")
                    continue
                
                # Handle IDs vs URLs
                if not u.startswith('http') and len(u) > 5:
                    if u.isalnum() and not '/' in u:
                        u = f"https://larooza.site/play.php?vid={u}"
                    else:
                        u = scraper.ROOT.rstrip('/') + '/' + u.lstrip('/')
                elif not u.startswith('http') and u:
                     u = scraper.ROOT.rstrip('/') + '/' + u.lstrip('/')
                        
                print(f"    Final URL: {u}")
                
                if u and u.startswith('http'):
                    # Try to get a better name for larooza servers
                    name_elem = item.find('strong')
                    name = (name_elem.get_text(strip=True) if name_elem else '') or \
                           item.get_text(strip=True) or \
                           item.get('data-embed-id') or \
                           f"Server {len(matrix)+1}"
                    print(f"    Server name: {name}")
                    
                    # Check for problematic domains
                    problematic_domains = ['okprime.site', 'film77.xyz']
                    has_problematic_domain = any(domain in u.lower() for domain in problematic_domains)
                    has_social_media = any(x in u.lower() for x in ['facebook', 'twitter'])
                    
                    print(f"    Has problematic domain: {has_problematic_domain}")
                    print(f"    Has social media: {has_social_media}")
                    
                    if has_social_media or has_problematic_domain:
                        print(f"    ❌ Skipping problematic server")
                        continue
                        
                    # Check for duplicates
                    is_duplicate = any(m['url'] == u for m in matrix)
                    print(f"    Is duplicate: {is_duplicate}")
                    
                    if not is_duplicate:
                        matrix.append({"name": name, "url": u, "type": "iframe"})
                        print(f"    ✅ Added server to matrix")
                    else:
                        print(f"    ❌ Duplicate server, skipping")
                else:
                    print(f"    ❌ Invalid URL, skipping")
        
        print(f"\n🎯 Final matrix has {len(matrix)} servers:")
        for i, server in enumerate(matrix):
            print(f"  {i+1:2d}. {server.get('name', 'N/A')} - {server.get('url', 'N/A')}")
            
        # Now let's run the actual _process_node_matrix function to compare
        print("\n--- ACTUAL _process_node_matrix FUNCTION ---")
        actual_matrix = scraper._process_node_matrix(raw_play)
        print(f"Actual matrix has {len(actual_matrix)} servers:")
        for i, server in enumerate(actual_matrix):
            print(f"  {i+1:2d}. {server.get('name', 'N/A')} - {server.get('url', 'N/A')}")
            
        # Compare the differences
        print(f"\n--- COMPARISON ---")
        print(f"Manual extraction: {len(matrix)} servers")
        print(f"Function extraction: {len(actual_matrix)} servers")
        
        manual_urls = {s['url'] for s in matrix}
        actual_urls = {s['url'] for s in actual_matrix}
        
        print(f"Manual URLs: {manual_urls}")
        print(f"Actual URLs: {actual_urls}")
        
        missing_urls = manual_urls - actual_urls
        extra_urls = actual_urls - manual_urls
        
        if missing_urls:
            print(f"❌ Missing URLs in function: {missing_urls}")
        if extra_urls:
            print(f"❓ Extra URLs in function: {extra_urls}")
        if not missing_urls and not extra_urls:
            print("✅ Both methods produce the same results")
                        
    except Exception as e:
        print(f"❌ Error during detailed debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(detailed_server_debug())