import urllib.request, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Try multiple JS bundles
chunks = [
    ('company', 'ebb7c3144b9d117fe2e7'),
    ('app', '8a374358faf983ceb548'),
    ('interactiveAnswer', '7c1187560b97b730ae0b'),
    ('chunk-commons', 'e8aed863572b4e161982'),
]

for name, hash_val in chunks:
    url = f'https://irm.cninfo.com.cn/{name}.{hash_val}.js'
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            js = r.read().decode('utf-8', errors='replace')
            urls = re.findall(r'["\']([^"\']{10,200})["\']', js)
            api_urls = [u for u in urls if ('api' in u.lower() or 'ircs' in u.lower() or 'question' in u.lower()) and u.startswith('/')]
            if api_urls:
                print(f'\n=== {name} ({len(js)} chars) ===')
                for u in set(api_urls): print(f'  {u[:120]}')
    except Exception as e:
        print(f'{name}: {str(e)[:60]}')
