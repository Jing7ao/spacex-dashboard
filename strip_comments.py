import re, os
DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(DIR, "_check.js"), encoding='utf-8') as f:
    js = f.read()

# Remove single-line comments (// ...)
js = re.sub(r'//[^\n]*', '', js)
# Remove multi-line comments (/* ... */)
js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
# Remove empty lines
js = re.sub(r'\n\s*\n', '\n', js)

with open(os.path.join(DIR, "_clean.js"), 'w', encoding='utf-8') as f:
    f.write(js)

print(f"Cleaned: {len(js)} chars")
print(f"Braces: {js.count('{')-js.count('}')}")
