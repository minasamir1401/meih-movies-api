import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time

def scrape_download_links_advanced(url):
    """Advanced scraper for Larooza download links that handles JavaScript-generated content"""
    print(f"Scraping download links from: {url}")
    
    try:
        # Extract VID from URL
        parsed = urlparse(url)
        vid = None
        if 'vid=' in parsed.query:
            vid = parsed.query.split('vid=')[1].split('&')[0]
        
        if not vid:
            print("Could not extract VID from URL")
            return []
        
        # Method 1: Try direct HTML parsing first
        print("Attempting direct HTML parsing...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        download_links = []
        
        # Look for download list items
        download_items = soup.select('ul.downloadlist li')
        print(f"Found {len(download_items)} download list items")
        
        for i, item in enumerate(download_items):
            # Try multiple attributes for download URL
            download_url = (
                item.get('data-download-url') or 
                item.get('data-url') or 
                item.get('data-link')
            )
            
            # Try to get URL from anchor tag
            a_tag = item.find('a')
            if not download_url and a_tag:
                download_url = a_tag.get('href') or a_tag.get('data-href')
            
            # Get label/description
            label = ""
            spans = item.find_all('span')
            if spans:
                label_parts = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]
                label = ' '.join(label_parts) if label_parts else ""
            
            if not label:
                if a_tag:
                    label = a_tag.get_text(strip=True) or a_tag.get('title', '')
            
            # Clean and validate URL
            if download_url:
                # Handle relative URLs
                if not download_url.startswith('http'):
                    download_url = urljoin(url, download_url)
                
                # Filter out obviously bad URLs
                if (download_url and 
                    not any(bad in download_url.lower() for bad in ['javascript:', '#', 'void']) and
                    len(download_url) > 10):
                    
                    # Avoid duplicates
                    if not any(dl['url'] == download_url for dl in download_links):
                        download_links.append({
                            'quality': label or f"Download Link {len(download_links)+1}",
                            'url': download_url
                        })
                        print(f"  Found link {len(download_links)}: {label[:30]}... -> {download_url[:50]}...")
        
        if download_links:
            print(f"Successfully extracted {len(download_links)} download links via HTML parsing")
            return download_links
        
        # Method 2: Look for script-generated links
        print("Looking for script-generated download links...")
        scripts = soup.find_all('script')
        script_links = []
        
        for script in scripts:
            content = script.string or ""
            if content:
                # Look for common download URL patterns
                patterns = [
                    r'downloadUrl["\']?\s*[:=]\s*["\']([^"\']+)',
                    r'href["\']?\s*[:=]\s*["\']([^"\']+download[^"\']*)',
                    r'location\.href\s*=\s*["\']([^"\']+)',
                    r'window\.open\s*\(\s*["\']([^"\']+)',
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        download_url = match.group(1)
                        if download_url and len(download_url) > 10:
                            if not download_url.startswith('http'):
                                download_url = urljoin(url, download_url)
                            
                            # Filter out bad URLs
                            if not any(bad in download_url.lower() for bad in ['javascript:', '#', 'void']):
                                if not any(dl['url'] == download_url for dl in script_links):
                                    script_links.append({
                                        'quality': f"Script Link {len(script_links)+1}",
                                        'url': download_url
                                    })
                                    print(f"  Found script link {len(script_links)}: {download_url[:50]}...")
        
        if script_links:
            print(f"Found {len(script_links)} script-generated download links")
            return script_links
            
        # Method 3: Look for any links that might be download links
        print("Searching for potential download links in all anchor tags...")
        all_links = soup.find_all('a', href=True)
        potential_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            title = link.get('title', '').lower()
            
            # Check if this looks like a download link
            if (any(keyword in href.lower() for keyword in ['download', 'dl=', 'get_file', '.mp4', '.mkv', '.avi']) or
                any(keyword in text for keyword in ['تحميل', 'download', 'تحميل مباشر']) or
                any(keyword in title for keyword in ['تحميل', 'download'])):
                
                full_url = urljoin(url, href) if not href.startswith('http') else href
                
                # Filter out bad URLs
                if not any(bad in full_url.lower() for bad in ['javascript:', '#', 'void', 'facebook', 'twitter']):
                    if not any(dl['url'] == full_url for dl in potential_links):
                        label = link.get_text(strip=True) or link.get('title', '') or 'Download Link'
                        potential_links.append({
                            'quality': label,
                            'url': full_url
                        })
                        print(f"  Found potential link: {label[:30]}... -> {full_url[:50]}...")
        
        if potential_links:
            print(f"Found {len(potential_links)} potential download links")
            return potential_links
        
        print("No download links found through any method")
        return []
        
    except Exception as e:
        print(f"Error scraping download links: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_specific_download_page():
    """Test the scraper with the specific download page"""
    url = "https://larooza.site/download.php?vid=0c02940bb"
    
    print("=" * 60)
    print("Larooza Download Link Scraper")
    print("=" * 60)
    
    download_links = scrape_download_links_advanced(url)
    
    print(f"\n{'='*60}")
    print(f"RESULTS: Found {len(download_links)} download links")
    print("=" * 60)
    
    for i, link in enumerate(download_links, 1):
        print(f"{i:2d}. {link['quality']}")
        print(f"     URL: {link['url']}")
        print()
    
    return download_links

if __name__ == "__main__":
    links = test_specific_download_page()