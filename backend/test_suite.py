import asyncio
import sys
import os
import logging

# Add the parent directory to sys.path to import scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.engine import LaroozaScraper

# Configure Minimal Logging for Tests
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("test_suite")

class ScraperTester:
    def __init__(self):
        self.scraper = LaroozaScraper()
        self.results = {"passed": 0, "failed": 0}

    def log_result(self, name: str, success: bool, message: str = ""):
        if success:
            self.results["passed"] += 1
            print(f"PASS: {name}")
        else:
            self.results["failed"] += 1
            print(f"FAIL: {name} - {message}")

    async def test_dynamic_flow(self):
        """Dynamic Flow: Home -> First Item -> Details"""
        print("\nSTARTING DYNAMIC TEST SUITE...\n" + "="*40)
        
        # 1. Test Home
        try:
            items = await self.scraper.fetch_home(page=1)
            if items and len(items) > 0:
                self.log_result("Home Fetch", True, f"Found {len(items)} items")
                
                # 2. Test Details using the FIRST item from home
                target_item = items[0]
                # Avoid printing Arabic to terminal to prevent encoding errors
                print(f"DEBUG: Testing details for item ID: {target_item['id'][:20]}...")
                data = await self.scraper.fetch_details(target_item['id'])
                
                has_servers = len(data.get('servers', [])) > 0
                has_title = len(data.get('title', '')) > 0
                self.log_result("Details Extraction", has_servers and has_title, f"Servers: {len(data.get('servers', []))}")
            else:
                self.log_result("Home Fetch", False, "No items found")
        except Exception as e:
            self.log_result("Dynamic Flow", False, str(e))

        # 3. Test Trending
        try:
            t_items = await self.scraper.fetch_trending()
            self.log_result("Trending Fetch", len(t_items) > 0)
        except Exception as e:
            self.log_result("Trending Fetch", False, str(e))

    async def run_all(self):
        await self.test_dynamic_flow()
        print("\n" + "="*40)
        print(f"SUMMARY: {self.results['passed']} Passed, {self.results['failed']} Failed")
        
        if self.results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    tester = ScraperTester()
    asyncio.run(tester.run_all())
