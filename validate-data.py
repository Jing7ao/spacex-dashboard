# 数据文件格式校验
# 每次改完 stock-data.json 或 events.json 后跑一次
# 用法: python validate-data.py

import json, sys, os

os.chdir(os.path.dirname(__file__))
errors = 0

# 1. stock-data.json
try:
    with open("stock-data.json", "r", encoding="utf-8") as f:
        stocks = json.load(f)
    required = ["code", "name", "ecosystem", "score_v26", "score_detail", "e1_audit", "risks", "gaps"]
    for s in stocks:
        for k in required:
            if k not in s:
                print(f"  STOCK {s.get('code','?')}: missing field '{k}'")
                errors += 1
        sd = s.get("score_detail", {})
        pts = sum(v for k,v in sd.items() if isinstance(v,(int,float)))
        if pts != s.get("score_v26", 0):
            print(f"  STOCK {s['code']}: score_detail sum={pts} != score_v26={s['score_v26']}")
            errors += 1
    print(f"stock-data.json: {len(stocks)} stocks, {errors} errors")
except Exception as e:
    print(f"stock-data.json FAIL: {e}")
    errors += 1

# 2. events.json
try:
    with open("events.json", "r", encoding="utf-8") as f:
        events = json.load(f)
    with_d20 = sum(1 for e in events if e.get("d20_excess") is not None)
    with_d5 = sum(1 for e in events if e.get("d5_excess") is not None)
    no_code = sum(1 for e in events if not e.get("stock_code"))
    print(f"events.json: {len(events)} events, {with_d20} with d20, {with_d5} with d5, {no_code} missing code")
    if no_code: errors += 1
except Exception as e:
    print(f"events.json FAIL: {e}")
    errors += 1

# 3. history-prices.json
try:
    with open("history-prices.json", "r", encoding="utf-8") as f:
        prices = json.load(f)
    for code, data in prices.items():
        if not isinstance(data, list):
            print(f"  PRICE {code}: not a list")
            errors += 1
        elif len(data) < 5:
            print(f"  PRICE {code}: only {len(data)} days")
    print(f"history-prices.json: {len(prices)} stocks")
except Exception as e:
    print(f"history-prices.json FAIL: {e}")
    errors += 1

# 4. research-tags.json
try:
    with open("research-tags.json", "r", encoding="utf-8") as f:
        tags = json.load(f)
    required_t = ["e", "s", "b"]
    for code, t in tags.items():
        for k in required_t:
            if k not in t:
                print(f"  TAG {code}: missing '{k}'")
                errors += 1
    print(f"research-tags.json: {len(tags)} tags, {errors} errors")
except Exception as e:
    print(f"research-tags.json FAIL: {e}")
    errors += 1

print(f"\n{'ALL OK' if errors==0 else f'TOTAL ERRORS: {errors}'}")
sys.exit(0 if errors == 0 else 1)
