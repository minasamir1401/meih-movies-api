import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

def scrape_download_links(play_url):
    """Scrape download links for a specific video"""
    print(f"Scraping download links for: {play_url}")
    
    try:
        # Extract VID from play URL
        parsed = urlparse(play_url)
        vid = None
        if 'vid=' in parsed.query:
            vid = parsed.query.split('vid=')[1].split('&')[0]
        elif 'video-' in play_url:
            match = re.search(r'video-([a-f0-9]+)-', play_url)
            if match:
                vid = match.group(1)
        
        if not vid:
            print("Could not extract VID from URL")
            return []
        
        # Construct download URL
        download_url = f"https://larooza.site/download.php?vid={vid}"
        print(f"Download page URL: {download_url}")
        
        # Fetch the download page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(download_url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        download_links = []
        
        # Look for Larooza download list structure
        download_items = soup.select('ul.downloadlist li[data-download-url]')
        
        for item in download_items:
            download_url_attr = item.get('data-download-url')
            if not download_url_attr:
                # Try to get href from anchor tag
                a_tag = item.find('a')
                if a_tag:
                    download_url_attr = a_tag.get('href')
            
            if download_url_attr:
                # Get label from spans
                spans = item.find_all('span')
                if spans:
                    # Get domain from URL for labeling
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', download_url_attr)
                    domain = domain_match.group(1) if domain_match else ''
                    
                    # Get descriptive text from spans
                    label_parts = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]
                    if label_parts:
                        quality = label_parts[0] if len(label_parts) > 0 else domain
                    else:
                        quality = domain if domain else f"Download Link {len(download_links)+1}"
                else:
                    # Extract domain for labeling
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', download_url_attr)
                    quality = domain_match.group(1) if domain_match else f"Download Link {len(download_links)+1}"
                
                # Clean URL
                abs_url = urljoin(download_url, download_url_attr) if not download_url_attr.startswith('http') else download_url_attr
                abs_url = abs_url.strip()
                
                # Avoid duplicates
                if not any(dl['url'] == abs_url for dl in download_links):
                    download_links.append({
                        'quality': quality,
                        'url': abs_url
                    })
        
        print(f"\n=== FOUND {len(download_links)} DOWNLOAD LINKS ===")
        for i, dl in enumerate(download_links):
            print(f"{i+1}. {dl['quality']} - {dl['url']}")
            
        return download_links
        
    except Exception as e:
        print(f"Error scraping download links: {e}")
        return []

if __name__ == "__main__":
    play_url = "https://larooza.site/play.php?vid=e265aeeb1"
    download_links = scrape_download_links(play_url)