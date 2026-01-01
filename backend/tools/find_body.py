import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("flaresolverr_output.html", "r", encoding="utf-8") as f:
    content = f.read()
    
    body_idx = content.find("<body")
    if body_idx != -1:
        print(f"Found <body> at index {body_idx}")
        print(content[body_idx:body_idx+2000])
    else:
        print("<body> tag NOT found!")
        # Check if it's all in scripts
        print(f"Total length: {len(content)}")
        print("Last 1000 chars:")
        print(content[-1000:])
