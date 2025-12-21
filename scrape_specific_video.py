import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def scrape_video_servers(url):
    """Scrape video servers from Larooza play page"""
    print(f"Scraping video servers from: {url}")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        servers = []
        
        # Method 1: Look for iframe
        iframe = soup.find('iframe')
        if iframe:
            src = iframe.get('src') or iframe.get('data-src')
            if src:
                if not src.startswith('http'):
                    src = urljoin(url, src)
                # Filter out known problematic domains for main player
                problematic_domains = ['okprime.site', 'film77.xyz']
                if not any(domain in src.lower() for domain in problematic_domains):
                    # Additional filter for homepage redirects and self-links
                    if (src.rstrip('/') != url.rstrip('/') and 
                        'larooza.site' not in src.lower()):
                        servers.append({
                            'name': 'Main Player',
                            'url': src,
                            'type': 'iframe'
                        })
        
        # Method 2: Look for server list items (Larooza specific)
        server_selectors = [
            'ul.WatchList li',
            '.servers-list li', 
            '.player-servers li',
            '.watch-servers a',
            '.list-server-items li',
            'ul.servers a',
            '.video-servers li',
            'div[data-url]',
            'a[data-vid]',
            '.server-item',
            '[data-embed-url]',
            '[data-embed-id]'
        ]
        
        for selector in server_selectors:
            elements = soup.select(selector)
            for elem in elements:
                # Try different attributes
                server_url = (
                    elem.get('data-embed-url') or 
                    elem.get('data-url') or 
                    elem.get('href') or 
                    elem.get('data-id') or 
                    elem.get('data-vid') or 
                    elem.get('data-link') or 
                    elem.get('data-source') or 
                    elem.get('data-embed-id')
                )
                
                if not server_url and elem.name != 'a':
                    # Try to find anchor inside element
                    a_tag = elem.find('a')
                    if a_tag:
                        server_url = a_tag.get('href') or a_tag.get('data-url') or a_tag.get('data-vid')
                
                if server_url and 'javascript' not in server_url.lower():
                    # Handle relative URLs
                    if not server_url.startswith('http'):
                        if server_url.startswith('//'):
                            server_url = "https:" + server_url
                        elif server_url.startswith('/'):
                            server_url = urljoin(url, server_url)
                        else:
                            server_url = urljoin(url, server_url)
                    
                    if server_url and server_url.startswith('http'):
                        # Skip social media and download links
                        if any(x in server_url.lower() for x in ['facebook', 'twitter', 'download.php']):
                            continue
                            
                        # Get server name
                        name_elem = elem.find('strong')
                        name = (name_elem.get_text(strip=True) if name_elem else '') or \
                               elem.get_text(strip=True) or \
                               elem.get('data-embed-id') or \
                               f"Server {len(servers)+1}"
                        
                        # Filter out known problematic domains
                        problematic_domains = ['okprime.site', 'film77.xyz']
                        if any(domain in server_url.lower() for domain in problematic_domains):
                            continue
                        
                        # Avoid duplicates
                        if not any(s['url'] == server_url for s in servers):
                            servers.append({
                                'name': name,
                                'url': server_url,
                                'type': 'iframe'
                            })
        
        # Method 3: Script scanning for embedded URLs
        scripts = soup.find_all('script')
        for script in scripts:
            content = script.string or ""
            # Look for common patterns
            matches = re.finditer(r'(?:url|link|vid|file|src)\s*[:=]\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
            for m in matches:
                server_url = m.group(1)
                if server_url and len(server_url) > 10 and any(x in server_url for x in ['.php', '.html', 'http']):
                    # Clean the link
                    if not server_url.startswith('http'): 
                        if server_url.startswith('//'):
                            server_url = "https:" + server_url
                        else:
                            server_url = urljoin(url, server_url)
                    
                    # Filter out images and social media
                    if any(server_url.lower().endswith(x) for x in ['.jpg', '.png', '.webp', '.jpeg', '.gif', '.svg']):
                        continue
                    if server_url.rstrip('/') == url.rstrip('/'):
                        continue
                    if any(x in server_url.lower() for x in ['facebook', 'twitter', 'google', 'analytics']):
                        continue
                    
                    # Filter out known problematic domains and homepage redirects
                    problematic_domains = ['okprime.site', 'film77.xyz']
                    if any(domain in server_url.lower() for domain in problematic_domains) or \
                       server_url.rstrip('/') == url.rstrip('/'):
                        continue
                    
                    # Avoid duplicates
                    # Additional filter for homepage redirects and self-links
                    if (server_url.rstrip('/') != url.rstrip('/') and 
                        'larooza.site' not in server_url.lower()):
                        # Avoid duplicates
                        if not any(s['url'] == server_url for s in servers):
                            servers.append({
                                'name': f"Mirror {len(servers)+1}",
                                'url': server_url,
                                'type': 'iframe'
                            })
        
        print(f"\n=== FOUND {len(servers)} VIDEO SERVERS ===")
        for i, server in enumerate(servers):
            print(f"{i+1}. {server['name']} - {server['url']}")
            
        return servers
        
    except Exception as e:
        print(f"Error scraping servers: {e}")
        return []

if __name__ == "__main__":
    url = "https://larooza.site/play.php?vid=e265aeeb1"
    servers = scrape_video_servers(url)