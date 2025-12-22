# Read and analyze the redirected download content
with open("debug_redirected_download.html", "r", encoding="utf-8") as f:
    content = f.read()

print(f"Total content length: {len(content)}")

# Check for download-related content
indicators = [
    "data-download-url",
    "downloadlist",
    "download",
    "data-download",
    "ul class=\"downloadlist\"",
    "li data-download-url"
]

found_indicators = []
for indicator in indicators:
    if indicator in content:
        found_indicators.append(indicator)
        print(f"Found '{indicator}' in content")

if found_indicators:
    print(f"\nFound {len(found_indicators)} download indicators")
else:
    print("\nNo download indicators found")
    
# Look for UL with downloadlist class
import re
match = re.search(r'ul class="downloadlist".*?</ul>', content, re.DOTALL | re.IGNORECASE)
if match:
    print("\nFound download list:")
    download_list_content = match.group(0)
    print(download_list_content)
    
    # Look for data-download-url attributes within the download list
    url_matches = re.findall(r'data-download-url="([^"]+)"', download_list_content)
    if url_matches:
        print(f"\nFound {len(url_matches)} data-download-url attributes:")
        for i, url in enumerate(url_matches):
            print(f"  {i+1}. {url}")
    else:
        print("\nNo data-download-url attributes found in download list")
else:
    print("\nNo download list found")
    
    # Try to find data-download-url attributes anywhere in the content
    url_matches = re.findall(r'data-download-url="([^"]+)"', content)
    if url_matches:
        print(f"\nFound {len(url_matches)} data-download-url attributes in content:")
        for i, url in enumerate(url_matches):
            print(f"  {i+1}. {url}")
    
# Look for any URLs
urls = re.findall(r'https?://[^\s"<>\]]+', content)
print(f"\nFound {len(urls)} URLs in content")
if urls:
    # Show first 10 URLs
    for i, url in enumerate(urls[:10]):
        print(f"  {i+1}. {url}")