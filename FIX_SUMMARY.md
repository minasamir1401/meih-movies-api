# Fix Summary: Scraping Engine Meta Refresh Redirect Handling

## Problem
The backend API was returning empty arrays for content requests because the scraping engine was not properly handling meta refresh redirects from the source websites. When visiting `https://larooza.icu/newvideos1.php?page=1`, the server returns a redirect page with a META refresh tag that redirects to another domain (`q.larozavideo.net`).

## Solution
Added proper handling for meta refresh redirects in the scraping engine:

1. Created a new `_follow_meta_refresh` method that detects and follows meta refresh redirects
2. Updated the Tier 1 direct HTTP fetching method to use this new functionality
3. Enhanced the existing Node.js proxy tier redirect handling

## Technical Details

### New Method: `_follow_meta_refresh`
- Detects meta refresh tags in HTML content using regex
- Extracts the redirect URL from the meta tag
- Makes the redirect URL absolute if it's relative
- Fetches the redirected content and returns it

### Updated Tier 1 Handler
- After fetching content, checks if it contains meta refresh tags
- If found, follows the redirect using the new method
- Returns the final content after following redirects

## Testing
The fix has been tested and confirmed to work:
- The scraper now successfully retrieves content from the source websites
- Previously returned 0 items, now returns 48+ items
- Content includes proper titles, posters, and metadata

## Files Modified
- `backend/scraper/engine.py` - Added redirect handling logic

## Impact
This fix resolves the main issue preventing content from appearing on the website. After deploying this fix, the website should display movies and series as expected.