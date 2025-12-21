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

async def test_larooza_download():
    # Test URL from the user's request
    download_url = "https://larooza.site/download.php?vid=08c459f24"
    print(f"Testing download extraction from: {download_url}")
    
    try:
        # Test the _resolve_vectors function which extracts download links
        downloads = await scraper._resolve_vectors(download_url)
        print(f"Downloads found: {len(downloads)}")
        for i, d in enumerate(downloads):
            print(f" {i+1}. {d['quality']}: {d['url']}")
    except Exception as e:
        print(f"Error fetching downloads: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    os.environ["SCRAPER_API_KEY"] = "aba96c9b1ad64905456a513bfd43fbe9"
    asyncio.run(test_larooza_download())