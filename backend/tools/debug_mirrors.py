import asyncio
import httpx
from bs4 import BeautifulSoup

async def debug_fetch():
    mirrors = ["https://q.larozavideo.net", "https://larooza.mom", "https://larooza.site", "https://m.laroza-tv.net"]
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for mirror in mirrors:
            print(f"\n--- Checking mirror: {mirror} ---")
            try:
                resp = await client.get(mirror, headers={"User-Agent": "Mozilla/5.0"})
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    title = soup.title.string if soup.title else "No title"
                    print(f"Title: {title}")
                    
                    selectors = ['.thumbnail', '.pm-li-video', '.pm-video-thumb', '.video-block', '.movie-item', 'li.col-xs-6', '.box', '.video-box', '.video-item', '.post-item']
                    found = False
                    for sel in selectors:
                        count = len(soup.select(sel))
                        if count > 0:
                            print(f"  Found {count} items with selector {sel}")
                            found = True
                    
                    if not found:
                        video_links = len(soup.select('a[href*="video.php"], a[href*="watch.php"]'))
                        print(f"  Found {video_links} video/watch links.")
                else:
                    print(f"  Snippet: {resp.text[:200]}")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_fetch())
