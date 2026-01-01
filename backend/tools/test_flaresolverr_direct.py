import httpx
import json
import time
import sys

# Set encoding for Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_flaresolverr():
    url = "http://localhost:8191/v1"
    target_url = "https://q.larozavideo.net/newvideos1.php"
    
    payload = {
        "cmd": "request.get",
        "url": target_url,
        "maxTimeout": 60000
    }
    
    print(f"Sending request to FlareSolverr for {target_url}...")
    start_time = time.time()
    try:
        with httpx.Client(timeout=90.0) as client:
            response = client.post(url, json=payload)
            duration = time.time() - start_time
            print(f"Status Code: {response.status_code}")
            print(f"Duration: {duration:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"FlareSolverr Status: {data.get('status')}")
                if data.get('status') == 'ok':
                    solution = data.get('solution', {})
                    html = solution.get('response', '')
                    print(f"HTML Length: {len(html)}")
                    print(f"Cookies: {len(solution.get('cookies', []))}")
                    print(f"User-Agent: {solution.get('userAgent')}")
                    
                    if "challenge-running" in html or "cf-ray" in html:
                        print("[X] Challenge still present in HTML!")
                    else:
                        print("[OK] Challenge solved (or not present)!")
                        
                    # Save HTML for inspection
                    with open("flaresolverr_output.html", "w", encoding="utf-8") as f:
                        f.write(html)
                else:
                    print(f"[X] FlareSolverr Error: {data.get('message')}")
            else:
                print(f"[X] HTTP Error: {response.text}")
    except Exception as e:
        print(f"[X] Exception: {e}")

if __name__ == "__main__":
    test_flaresolverr()
