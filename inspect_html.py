#!/usr/bin/env python3
"""
Inspect the actual HTML structure to find correct selectors
"""

import asyncio
import sys
import os
from bs4 import BeautifulSoup

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def inspect_html_structure():
    """Inspect the HTML structure"""
    print("🔍 INSPECTING HTML STRUCTURE")
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
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for common video listing patterns
        print("\nLooking for video listing patterns...")
        
        # Try different common selectors
        common_selectors = [
            'li',  # All list items
            'div',  # All divs
            '.video',  # Video classes
            '.item',   # Item classes
            '.post',   # Post classes
            '[class*="video"]',  # Any class containing "video"
            '[class*="item"]',   # Any class containing "item"
            'a[href*="vid="]',   # Links with vid parameter
            'a[href*="video"]',  # Links with video in URL
        ]
        
        for selector in common_selectors:
            elements = soup.select(selector)
            if len(elements) > 0 and len(elements) < 100:  # Only show reasonable counts
                print(f"  {selector}: {len(elements)} elements")
                
        # Look for links with video parameters
        print("\nLooking for video links...")
        all_links = soup.find_all('a', href=True)
        video_links = []
        for link in all_links:
            href = link.get('href', '')
            if 'vid=' in href and 'video.php' in href:
                video_links.append(link)
                
        print(f"Found {len(video_links)} video links")
        
        # Show first few video links
        for i, link in enumerate(video_links[:5]):
            print(f"  {i+1}. href: {link.get('href')}")
            print(f"     text: {link.get_text().strip()[:50]}...")
            
        # Look for images
        print("\nLooking for images...")
        images = soup.find_all('img')
        print(f"Found {len(images)} images")
        
        # Show first few images
        for i, img in enumerate(images[:5]):
            src = img.get('src', img.get('data-src', img.get('data-original', 'No source')))
            alt = img.get('alt', 'No alt')
            print(f"  {i+1}. src: {src[:50]}...")
            print(f"     alt: {alt[:50]}...")
            
        # Look for the actual structure around videos
        print("\nLooking for video containers...")
        
        # Try to find containers that have both links and images
        potential_containers = []
        
        # Look for divs or list items that contain both links and images
        for container in soup.find_all(['div', 'li']):
            links = container.find_all('a', href=True)
            imgs = container.find_all('img')
            
            # Check if this container has video links and images
            video_links_in_container = [link for link in links if 'vid=' in link.get('href', '')]
            
            if video_links_in_container and imgs:
                potential_containers.append((container, video_links_in_container, imgs))
                
        print(f"Found {len(potential_containers)} potential video containers")
        
        # Show details of first container
        if potential_containers:
            container, links, imgs = potential_containers[0]
            print(f"\nFirst container details:")
            print(f"  Container tag: {container.name}")
            print(f"  Container classes: {container.get('class', 'No classes')}")
            print(f"  Video links in container: {len(links)}")
            print(f"  Images in container: {len(imgs)}")
            
            # Show the HTML of this container
            print(f"  Container HTML preview: {str(container)[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(inspect_html_structure())