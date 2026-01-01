import asyncio
from scraper.engine import LaroozaScraper
from bs4 import BeautifulSoup
import sys

async def main():
    s = LaroozaScraper()
    s.BASE_URL = "https://larooza.mom"
    s.TARGET_URL = "https://larooza.mom/newvideos.php"
    
    print(f"Fetching {s.TARGET_URL}...")
    html = await s._get_html(s.TARGET_URL)
    if not html:
        print("Failed to get HTML")
        return
        
    print(f"HTML Length: {len(html)}")
    soup = BeautifulSoup(html, 'html.parser')
    items = s._extract_items(soup)
    print(f"Found {len(items)} items")
    for item in items[:5]:
        print(f" - {item['title']} ({item['type']})")

if __name__ == "__main__":
    asyncio.run(main())
