import asyncio
import httpx
import json
import sys

# Set encoding to utf-8 for windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def test():
    urls = [
        "https://q.larozavideo.net/home.24",
        "https://q.larozavideo.net/newvideos1.php",
        "https://q.larozavideo.net/category.php?cat=all_movies_13"
    ]
    
    flaresolverr_url = "http://127.0.0.1:8191/v1"
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        for url in urls:
            print(f"\n--- Testing {url} ---")
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            }
            try:
                response = await client.post(flaresolverr_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok':
                        solution = data.get('solution', {})
                        html = solution.get('response', '')
                        title = solution.get('title', '')
                        print(f"Title found: {title}")
                        
                        if "video.php" in html or ".thumbnail" in html or ".box" in html:
                            print("FOUND: Movie items are present in HTML!")
                        else:
                            print("FAILED: No movie items in HTML.")
                            print(f"Snippet: {html[:500]}")
                    else:
                        print(f"FlareSolverr message: {data.get('message')}")
                else:
                    print(f"Server error: {response.status_code}")
            except Exception as e:
                print(f"Script error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
