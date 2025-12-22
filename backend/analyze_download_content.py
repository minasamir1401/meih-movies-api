# Read and analyze the downloaded content
with open("debug_download_content.html", "r", encoding="utf-8") as f:
    content = f.read()

print(f"Total content length: {len(content)}")

# Check for download-related content
if "download" in content.lower():
    print("Found 'download' in content")
    
if "data-download-url" in content:
    print("Found 'data-download-url' in content")
    
# Look for UL with downloadlist class
if "downloadlist" in content:
    print("Found 'downloadlist' in content")
    
# Show some context around downloadlist
import re
match = re.search(r'ul class="downloadlist".*?</ul>', content, re.DOTALL | re.IGNORECASE)
if match:
    print("\nFound download list:")
    print(match.group(0))
else:
    print("\nNo download list found")
    
# Look for any URLs
urls = re.findall(r'https?://[^\s"<>\]]+', content)
print(f"\nFound {len(urls)} URLs in content")
if urls:
    # Show first 10 URLs
    for i, url in enumerate(urls[:10]):
        print(f"  {i+1}. {url}")