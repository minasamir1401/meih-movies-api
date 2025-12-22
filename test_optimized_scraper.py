"""
Test script for the optimized headless scraper
"""

import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.optimized_headless_scraper import optimized_scraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_optimized_scraper():
    """Test the optimized headless scraper"""
    logger.info("Testing optimized headless scraper...")
    
    # Test URL - using a sample video page
    test_url = "https://larooza.site/play.php?vid=e265aeeb1"
    
    try:
        # Initialize the scraper
        if not await optimized_scraper.init():
            logger.error("Failed to initialize scraper")
            return
            
        logger.info("Scraper initialized successfully")
        
        # Test fetching content
        logger.info(f"Fetching content from: {test_url}")
        content = await optimized_scraper.fetch(test_url, timeout=15000)
        
        if content:
            logger.info(f"Successfully fetched {len(content)} characters")
            
            # Save content for inspection
            with open("test_fetched_content.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Content saved to test_fetched_content.html")
            
            # Test extracting download links
            logger.info("Extracting download links...")
            download_links = await optimized_scraper.extract_download_links(test_url)
            logger.info(f"Found {len(download_links)} download links")
            
            for i, link in enumerate(download_links):
                logger.info(f"  {i+1}. {link['quality']}: {link['url']}")
                
            # Test extracting servers
            logger.info("Extracting video servers...")
            servers = await optimized_scraper.extract_servers(test_url)
            logger.info(f"Found {len(servers)} video servers")
            
            for i, server in enumerate(servers):
                logger.info(f"  {i+1}. {server['name']}: {server['url']} ({server['type']})")
                
        else:
            logger.error("Failed to fetch content")
            
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close the scraper
        await optimized_scraper.close()
        logger.info("Scraper closed")

if __name__ == "__main__":
    asyncio.run(test_optimized_scraper())