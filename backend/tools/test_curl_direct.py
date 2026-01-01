from curl_cffi.requests import AsyncSession
import asyncio

async def test_curl():
    url = "https://q.larozavideo.net/newvideos1.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    async with AsyncSession(impersonate="chrome120") as s:
        print(f"Fetching {url}...")
        try:
            resp = await s.get(url, headers=headers, timeout=15)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"Title: {resp.text.find('<title>')}")
                if "video.php" in resp.text:
                    print("SUCCESS: Found video items!")
                else:
                    print("FAILED: No video items found.")
                    print(f"Snippet: {resp.text[:500]}")
            else:
                print(f"HTTP Error {resp.status_code}")
                # Print headers to see if it's Cloudflare
                print(f"Server: {resp.headers.get('Server')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_curl())
