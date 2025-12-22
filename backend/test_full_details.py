import asyncio
import base64
import sys
import os
import logging
from bs4 import BeautifulSoup

# Configure logging to see scraper output
logging.basicConfig(level=logging.INFO)
sys.path.append(os.getcwd())

from scraper.engine import scraper

async def test_full_details():
    # Test URL from the user's request - the main video page
    target_url = "https://larooza.site/video.php?vid=08c459f24"
    print(f"Testing full details extraction from: {target_url}")
    
    # Encode the URL as the API expects
    encoded_id = base64.urlsafe_b64encode(target_url.encode()).decode()
    print(f"Encoded ID: {encoded_id}")
    
    try:
        # Test the full details extraction
        details = await scraper.get_content_details(encoded_id)
        print(f"\nTitle: {details.get('title', 'N/A')}")
        print(f"Type: {details.get('type', 'N/A')}")
        print(f"Description: {details.get('description', 'N/A')[:100]}...")
        print(f"Poster: {details.get('poster', 'N/A')}")
        print(f"Episodes found: {len(details.get('episodes', []))}")
        print(f"Servers found: {len(details.get('servers', []))}")
        print(f"Download links found: {len(details.get('download_links', []))}")
        
        print("\nServers:")
        for i, server in enumerate(details.get('servers', [])):
            print(f" {i+1}. {server['name']}: {server['url']}")
            
        print("\nDownload Links:")
        for i, dl in enumerate(details.get('download_links', [])):
            print(f" {i+1}. {dl['quality']}: {dl['url']}")
            
    except Exception as e:
        print(f"Error fetching details: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    os.environ["SCRAPER_API_KEY"] = "aba96c9b1ad64905456a513bfd43fbe9"
    asyncio.run(test_full_details())