import asyncio
import httpx
from curl_cffi.requests import AsyncSession

async def check_mirrors():
    mirrors = [
        "https://larooza.mom",
        "https://larooza.site",
        "https://laroza-tv.net",
        "https://larozavideo.net",
        "https://larooza.video",
        "https://q.larozavideo.net"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    for mirror in mirrors:
        print(f"Checking {mirror}...")
        try:
            # Try curl-cffi first
            async with AsyncSession(impersonate="chrome110") as s:
                resp = await s.get(mirror, headers=headers, timeout=10)
                print(f"  [curl-cffi] {mirror}: {resp.status_code} | Title: {resp.text[:100].replace('\n', ' ')}")
                
            async with httpx.AsyncClient(http2=True, timeout=10) as client:
                resp = await client.get(mirror, headers=headers)
                print(f"  [httpx] {mirror}: {resp.status_code} | Title: {resp.text[:100].replace('\n', ' ')}")
        except Exception as e:
            print(f"  [Error] {mirror}: {e}")

if __name__ == "__main__":
    asyncio.run(check_mirrors())
