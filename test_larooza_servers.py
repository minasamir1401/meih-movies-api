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

async def test_larooza_servers():
    # Test URL from the user's request
    play_url = "https://larooza.site/play.php?vid=08c459f24"
    print(f"Testing server extraction from: {play_url}")
    
    try:
        # Test the _resolve_source_matrix function which extracts servers
        servers = await scraper._resolve_source_matrix(play_url)
        print(f"Servers found: {len(servers)}")
        for i, s in enumerate(servers):
            print(f" {i+1}. {s['name']}: {s['url']}")
    except Exception as e:
        print(f"Error fetching servers: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    os.environ["SCRAPER_API_KEY"] = "aba96c9b1ad64905456a513bfd43fbe9"
    asyncio.run(test_larooza_servers())