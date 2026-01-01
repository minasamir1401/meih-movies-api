import httpx
import asyncio
from bs4 import BeautifulSoup

async def dump_html():
    url = "https://q.larozavideo.net/newvideos1.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        print(f"Fetching {url}...")
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Final URL: {resp.url}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        containers = soup.select('.thumbnail, .pm-li-video, .pm-video-thumb, .video-block, .movie-item, li.col-xs-6, .box, .video-box, .video-item, .post-item')
        print(f"Found {len(containers)} item containers.")
        
        if len(containers) == 0:
            print("Snippet of HTML:")
            print(resp.text[:1000])

if __name__ == "__main__":
    asyncio.run(dump_html())
