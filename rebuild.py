# rebuild.py — 用 _check.js 重建 monitor.html 的 script 块
import os
DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(DIR, "monitor.html"), encoding='utf-8') as f:
    html = f.read()

with open(os.path.join(DIR, "_check.js"), encoding='utf-8') as f:
    js = f.read()

# 找到内联 script 块并替换
start = html.index('<script>', 200) + 8
end = html.index('</script>', start)
new_html = html[:start] + js + html[end:]

# 保存
with open(os.path.join(DIR, "monitor.html"), 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"Rebuilt. Script block now: {len(js)} chars")
print(f"Starts: {repr(js[:50])}")
print(f"Ends: {repr(js[-50:])}")
