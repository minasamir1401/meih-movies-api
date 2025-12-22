import sys
import traceback

try:
    print("Testing imports...")
    import nest_asyncio
    print("✓ nest_asyncio imported")
    
    nest_asyncio.apply()
    print("✓ nest_asyncio applied")
    
    from scraper.engine import scraper
    print("✓ scraper imported")
    
    from fastapi import FastAPI
    print("✓ FastAPI imported")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
