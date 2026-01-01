import requests
import json
import sys

# Ensure UTF-8 output for Arabic characters
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass # Not available in all environments

try:
    r = requests.get('http://localhost:8000/latest', timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Items found: {len(data)}")
        if data:
            print(f"First item title: {data[0].get('title')}")
            print(f"First item ID: {data[0].get('id')}")
        else:
            print("Response body:")
            print(r.text[:500])
    else:
        print(f"Error body: {r.text[:500]}")
except Exception as e:
    print(f"Request failed: {e}")
