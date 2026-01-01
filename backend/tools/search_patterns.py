import sys
import io
import re

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("flaresolverr_output.html", "r", encoding="utf-8") as f:
    content = f.read()
    
    print(f"Total length: {len(content)}")
    
    # Search for common patterns
    patterns = ['thumbnail', 'pm-li-video', 'video-block', 'movie-item', 'video.php', 'watch.php']
    for p in patterns:
        count = len(re.findall(p, content))
        print(f"Pattern '{p}': found {count} times")
        
    # If not found, show some snippets from the middle
    if len(content) > 10000:
        print("\n--- Snippet from middle (50000:51000) ---")
        print(content[50000:51000])
