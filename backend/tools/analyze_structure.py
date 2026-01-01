from bs4 import BeautifulSoup
import sys
import io

# Set encoding for Windows terminal
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_html():
    with open("flaresolverr_output.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print("--- Analyzing Links ---")
    links = soup.find_all('a', href=True)
    for i, a in enumerate(links[:100]):
        href = a['href']
        text = a.get_text(strip=True)
        if 'cat=' in href or 'video' in href or 'movie' in href or 'series' in href:
            print(f"{i}: Text: {text} | Href: {href}")
            
    print("\n--- Analyzing Containers ---")
    # Look for common patterns in classes
    classes = set()
    for tag in soup.find_all(True, class_=True):
        for c in tag['class']:
            classes.add(c)
    
    print(f"Found {len(classes)} unique classes.")
    # Print classes that might be containers
    potential = [c for c in classes if any(x in c.lower() for x in ['item', 'video', 'movie', 'thumb', 'card', 'block', 'col'])]
    print(f"Potential container classes: {potential}")

if __name__ == "__main__":
    analyze_html()
