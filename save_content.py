#!/usr/bin/env python3
"""
Save fetched content to file for examination
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def save_content():
    """Save fetched content to file"""
    print("💾 SAVING FETCHED CONTENT TO FILE")
    print("=" * 50)
    
    try:
        # Import the scraper
        from backend.scraper.engine import scraper
        
        # Test URL
        test_url = "https://q.larozavideo.net/newvideos1.php?page=1"
        
        print(f"Fetching content from: {test_url}")
        
        # Get content using headless browser
        content = await scraper.headless.fetch(test_url)
        
        if not content:
            print("❌ Failed to fetch content")
            return
            
        print(f"✅ Successfully fetched {len(content)} characters")
        
        # Save to file
        with open('fetched_content.html', 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("✅ Content saved to fetched_content.html")
        
        # Show first 1000 characters
        print("\nFirst 1000 characters of content:")
        print("=" * 50)
        print(content[:1000])
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(save_content())