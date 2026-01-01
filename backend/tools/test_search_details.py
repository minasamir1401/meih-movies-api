import requests
import sys

# Ensure UTF-8 output for console
sys.stdout.reconfigure(encoding='utf-8')

def test_search(query):
    url = f"http://localhost:8000/search?q={query}"
    print(f"Searching for: {query}...")
    try:
        r = requests.get(url, timeout=30)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Results found: {len(data)}")
            if data:
                print(f"First result title: {data[0].get('title')}")
                print(f"First result ID: {data[0].get('id')}")
                return data[0].get('id')
        else:
            print(f"Error: {r.text[:500]}")
    except Exception as e:
        print(f"Search failed: {e}")
    return None

def test_details(safe_id):
    url = f"http://localhost:8000/details/{safe_id}"
    print(f"\nFetching details for: {safe_id}...")
    try:
        r = requests.get(url, timeout=30)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Title: {data.get('title')}")
            print(f"Servers count: {len(data.get('servers', []))}")
            print(f"Download links count: {len(data.get('download_links', []))}")
        else:
            print(f"Error: {r.text[:500]}")
    except Exception as e:
        print(f"Details failed: {e}")

if __name__ == "__main__":
    # Test with a likely existing movie title
    movie_id = test_search("%D9%87%D9%8A%D8%A8%D8%AA%D8%A7") # "هيبتا"
    if movie_id:
        test_details(movie_id)
