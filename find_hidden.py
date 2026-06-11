import os, re
DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(DIR, "_check.js"), encoding='utf-8') as f:
    js = f.read()

# Find problematic Unicode
for i, ch in enumerate(js):
    cp = ord(ch)
    # Zero-width characters, control chars, bidi markers
    if cp in [0x200B, 0x200C, 0x200D, 0xFEFF, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
              0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFFF9, 0xFFFA, 0xFFFB,
              0x180E, 0x00AD, 0x034F, 0x061C, 0x115F, 0x1160, 0x17B4, 0x17B5]:
        line = js[:i].count('\n') + 1
        ctx = js[max(0,i-20):i+20]
        print(f"Line {line} pos {i}: U+{cp:04X} context: {repr(ctx)}")
        break

print("Done scanning", len(js), "chars")
