import httpx
try:
    with httpx.Client(timeout=5.0) as client:
        resp = client.get("http://localhost:8000/health")
        print(f"Status: {resp.status_code}")
        print(f"Data: {resp.json()}")
except Exception as e:
    print(f"Error: {e}")
