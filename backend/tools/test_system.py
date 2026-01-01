import asyncio
import httpx
import time
import sys
import os

# Set encoding for Windows CLI
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def test_system():
    print("\n" + "="*50)
    print("🔍 MEIH SYSTEM HEALTH CHECK")
    print("="*50 + "\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Test FlareSolverr
        print("📡 Checking FlareSolverr...")
        try:
            resp = await client.get("http://localhost:8191/health")
            if resp.status_code == 200:
                print("✅ FlareSolverr: ONLINE")
            else:
                print(f"❌ FlareSolverr: ERROR (Status {resp.status_code})")
        except Exception as e:
            print(f"❌ FlareSolverr: OFFLINE ({e})")

        # 2. Test FastAPI Backend
        print("\n⚙️  Checking FastAPI Backend...")
        try:
            resp = await client.get("http://localhost:8000/")
            if resp.status_code == 200:
                print("✅ Backend: ONLINE")
                data = resp.json()
                print(f"   Mirror Active: {data.get('active_mirror')}")
                print(f"   Engine Status: {data.get('engine_status')}")
            else:
                print(f"❌ Backend: ERROR (Status {resp.status_code})")
        except Exception as e:
            print(f"❌ Backend: OFFLINE ({e})")

        # 3. Test Scrapper (Latest Movies)
        print("\n🎬 Testing Movie Scrapper (Live Fetch)...")
        try:
            start_time = time.time()
            resp = await client.get("http://localhost:8000/latest")
            duration = time.time() - start_time
            if resp.status_code == 200:
                items = resp.json()
                print(f"✅ Scrapper: SUCCESS")
                print(f"   Items Found: {len(items)}")
                print(f"   Time Taken: {duration:.2f}s")
                if items:
                    print(f"   Top Item: {items[0]['title']}")
            else:
                print(f"❌ Scrapper: FAILED (Status {resp.status_code})")
        except Exception as e:
            print(f"❌ Scrapper: ERROR ({e})")

        # 4. Test Category (Fast Path)
        print("\n📂 Testing Category (Prefetch Integrity)...")
        try:
            start_time = time.time()
            resp = await client.get("http://localhost:8000/category/arabic-movies")
            duration = time.time() - start_time
            if resp.status_code == 200:
                items = resp.json()
                print(f"✅ Category Path: STABLE")
                print(f"   Items: {len(items)}")
                print(f"   Time Taken: {duration:.2f}s (Should be < 0.5s if cached)")
            else:
                print(f"❌ Category: FAILED")
        except Exception as e:
            print(f"❌ Category: ERROR ({e})")

    print("\n" + "="*50)
    print("✨ ALL TESTS COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(test_system())
