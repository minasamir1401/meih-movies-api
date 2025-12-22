from bs4 import BeautifulSoup

def extract_info():
    with open('play_content.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print("--- IFRAMES ---")
    for f in soup.find_all('iframe'):
        print(f.get('src') or f.get('data-src'))
        
    print("\n--- SCRIPTS WITH LINKS ---")
    import re
    scripts = soup.find_all('script')
    for s in scripts:
        if s.string:
            links = re.findall(r'https?://[^\s"\']+', s.string)
            for l in links:
                if 'vid=' in l or 'play.php' in l or 'video.php' in l or 'embed' in l:
                    print(l)
                    
    print("\n--- BUTTONS/LINKS WITH DATA-ID ---")
    for tag in soup.find_all(True, attrs={"data-id": True}):
        print(f"{tag.name} data-id: {tag['data-id']}")
    
    for tag in soup.find_all(True, attrs={"data-url": True}):
        print(f"{tag.name} data-url: {tag['data-url']}")

extract_info()
