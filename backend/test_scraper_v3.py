import asyncio
import base64
import sys
import os
import logging
from bs4 import BeautifulSoup

# Configure logging to see scraper output
logging.basicConfig(level=logging.INFO)
sys.path.append(os.getcwd())
# Fix for Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

from scraper.engine import scraper

async def test_scraper():
    # Target: https://larooza.site/video.php?vid=Yg3SBQkKF
    target_url = "https://larooza.site/video.php?vid=Yg3SBQkKF"
    vid_id = base64.urlsafe_b64encode(target_url.encode()).decode()
    
    print(f"Testing fetch_details for URL: {target_url}")
    print(f"Encoded ID: {vid_id}")
    
    print("\n--- Testing Direct Page Fetches ---")
    
    # 2. Play Page (Servers)
    vid = "Yg3SBQkKF"
    play_url = f"https://larooza.site/play.php?vid={vid}"
    print(f"Fetching Play Page: {play_url}")
    try:
        servers = await scraper._extract_servers_from_play_page(play_url, referer=target_url)
        print(f"Servers found: {len(servers)}")
        for s in servers:
            print(f" - {s['name']}: {s['url']}")
    except Exception as e:
        print(f"Error fetching servers: {e}")

    # 3. Download Page
    download_url = f"https://larooza.site/download.php?vid={vid}"
    print(f"\nFetching Download Page: {download_url}")
    try:
        downloads = await scraper._extract_downloads_from_page(download_url, referer=target_url)
        print(f"Downloads found: {len(downloads)}")
        for d in downloads:
            print(f" - {d['quality']}: {d['url']}")
    except Exception as e:
         print(f"Error fetching downloads: {e}")
    
    print("\n--- Testing Full fetch_details (Parallel) ---")
    res = await scraper.fetch_details(vid_id)
    
    print("\n--- FINAL RESULTS ---")
    print(f"Title: {res.get('title')}")
    print(f"Type: {res.get('type')}")
    print(f"Servers: {len(res.get('servers', []))}")
    print(f"Downloads: {len(res.get('download_links', []))}")

    print("\n\n--- 2. Testing Home Page Images ---")
    # Test fetching the home page to see how images are structured
    try:
        home_url = "https://larooza.site/newvideos.php"
        print(f"Fetching Home Page: {home_url}")
        html = await scraper._fetch_html(home_url, render=False)
        
        # Save HTML to file
        with open('home_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved home_debug.html")

        soup = BeautifulSoup(html, 'html.parser')
        
        # Select first 5 video items
        items = soup.select('.pm-li-video, .video-item, .postBlock')
        if not items:
            # Try generic article or div if specific class not found
            items = soup.find_all('div', class_='video-item') or soup.find_all('article')
            
        print(f"Found {len(items)} items on Home.")
        
        for i, item in enumerate(items[:5]):
            print(f"\nItem {i+1}:")
            img_tag = item.find('img')
            if img_tag:
                print(f"  Raw <img> tag: {img_tag}")
                print(f"  src: {img_tag.get('src')}")
                print(f"  data-src: {img_tag.get('data-src')}")
                print(f"  data-original: {img_tag.get('data-original')}")
            else:
                print("  No <img> tag found")
                
    except Exception as e:
        print(f"Home Page Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraper())
