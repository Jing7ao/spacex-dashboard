import os
DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(DIR, "_check.js"), 'rb') as f:
    data = f.read()

# Convert CRLF to LF
data = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')

# Remove trailing whitespace/newlines
data = data.rstrip(b'\n\r\t ') + b'\n'

with open(os.path.join(DIR, "_check_lf.js"), 'wb') as f:
    f.write(data)

print(f"Written {len(data)} bytes, last 20 bytes: {repr(data[-20:])}")
