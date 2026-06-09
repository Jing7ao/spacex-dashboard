# 批量拉取历史收盘价 — 新浪API (本地运行)
# 用法: C:/Users/13639/AppData/Local/Python/bin/python.exe fetch-history.py
# 输出: history-prices.json

import urllib.request, json, re

STOCKS = [
    ("sz300476", "胜宏科技"),
    ("sz002851", "麦格米特"),
    ("sz300136", "信维通信"),
    ("sh688017", "绿的谐波"),
    ("sh688629", "华丰科技"),
    ("sz001270", "铖昌科技"),
    ("sh688631", "莱斯信息"),
    ("sh600584", "长电科技"),
    ("sz300395", "菲利华"),
    ("sz002463", "沪电股份"),
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
result = {}

print("Fetching historical prices via Sina API (2026-01-01 ~ 2026-06-06)\n")

for symbol, name in STOCKS:
    try:
        url = f'https://quotes.sina.cn/cn/api/jsonp_v2.php/data/CN_MarketDataService.getKLineData?symbol={symbol}&scale=240&datalen=200'
        req = urllib.request.Request(url, headers=HEADERS)
        raw = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
        m = re.search(r'\(([\s\S]*)\)', raw)
        if not m:
            print(f"  FAIL {name}: no JSON match")
            result[symbol] = []
            continue
        data = json.loads(m.group(1))
        prices = []
        for d in data:
            dt = d['day']
            if '2026-' in dt:
                prices.append({
                    "date": dt,
                    "open": float(d['open']),
                    "close": float(d['close']),
                    "high": float(d['high']),
                    "low": float(d['low']),
                    "volume": int(d['volume']),
                })
        code = symbol[2:]
        result[code] = prices
        print(f"  OK {name}: {len(prices)} days ({prices[0]['date']} ~ {prices[-1]['date']})")
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        result[symbol[2:]] = []

# 沪深300 via Sina
print("\n  Fetching HS300...")
try:
    url = 'https://quotes.sina.cn/cn/api/jsonp_v2.php/data/CN_MarketDataService.getKLineData?symbol=sh000300&scale=240&datalen=200'
    req = urllib.request.Request(url, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
    m = re.search(r'\(([\s\S]*)\)', raw)
    if m:
        data = json.loads(m.group(1))
        hs = []
        for d in data:
            if '2026-' in d['day']:
                hs.append({"date": d['day'], "close": float(d['close'])})
        result['000300'] = hs
        print(f"  OK HS300: {len(hs)} days")
    else:
        result['000300'] = []
        print("  FAIL HS300: no match")
except Exception as e:
    print(f"  FAIL HS300: {e}")
    result['000300'] = []

with open("history-prices.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\nDone: history-prices.json ({sum(1 for v in result.values() if v)} stocks with data)")
