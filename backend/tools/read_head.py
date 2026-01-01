import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("flaresolverr_output.html", "r", encoding="utf-8") as f:
    content = f.read(2000)
    print(content)
