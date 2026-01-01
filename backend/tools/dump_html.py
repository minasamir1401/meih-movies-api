import httpx
import asyncio
from bs4 import BeautifulSoup

async def dump_html():
    url = "https://larooza.mom" # Using the one that gave 0 links
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        print(f"Fetching {url}...")
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        with open("dump.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("HTML dumped to dump.html")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = soup.select('a')
        print(f"Total links: {len(links)}")
        for a in links[:20]:
            print(f"Link: {a.get('href')} | Text: {a.get_text(strip=True)[:30]}")

if __name__ == "__main__":
    asyncio.run(dump_html())
