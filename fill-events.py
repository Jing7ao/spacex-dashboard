# 自动回填事件 d0/d5/d20 超额收益（使用历史价格数据）
import json, re

with open("history-prices.json", "r", encoding="utf-8") as f:
    prices = json.load(f)

with open("events-data.js", "r", encoding="utf-8") as f:
    js = f.read()

# Extract events
events = []
for m in re.finditer(r'\{[^}]*?"id":\s*"(evt_\d+)"[^}]*?\}', js, re.DOTALL):
    try:
        evt = json.loads(m.group(0))
        events.append(evt)
    except:
        pass

def get_close(code, date_str):
    """Get closing price for a stock on a specific date"""
    if code not in prices or not prices[code]:
        return None
    data = prices[code]
    # Find exact match or nearest trading day >= date
    for i, d in enumerate(data):
        if d['date'] >= date_str:
            return d['close'], i
    return None, -1

def calc_return(code, event_date, offset_days):
    """Calculate return over offset trading days. offset=0 uses prev_close as base."""
    if code not in prices or not prices[code]:
        return None
    data = prices[code]
    dates = [d['date'] for d in data]
    closes = [d['close'] for d in data]

    # Find event date index
    idx = None
    for i, d in enumerate(dates):
        if d >= event_date:
            idx = i
            break
    if idx is None or idx + offset_days >= len(data):
        return None

    if offset_days == 0:
        # d0 return: (event close - prev close) / prev close
        if idx == 0:
            return None
        return round((closes[idx] - closes[idx-1]) / closes[idx-1] * 100, 2)

    # d5/d20: return from event close to target close
    base = closes[idx]
    target = closes[idx + offset_days]
    return round((target - base) / base * 100, 2)

def calc_excess(code, event_date, offset_days):
    """Calculate excess return over HS300"""
    stock_ret = calc_return(code, event_date, offset_days)
    if stock_ret is None and offset_days > 0:
        # Try with offset 1 first
        stock_ret = calc_return(code, event_date, offset_days)
    if stock_ret is None:
        return None

    hs300_ret = calc_return('000300', event_date, offset_days)
    if hs300_ret is None:
        return None

    return round(stock_ret - hs300_ret, 2)

filled = 0
for evt in events:
    code = evt.get('stock_code', '')
    date = evt.get('event_date', '')

    # Skip if no code or date
    if not code or not date:
        continue

    # Skip if already has d20
    if evt.get('d20_excess') is not None:
        continue

    # Calculate d5 and d20
    d0 = calc_return(code, date, 0)
    d5 = calc_excess(code, date, 5)
    d20 = calc_excess(code, date, 20)

    if d0 is not None or d5 is not None or d20 is not None:
        # Update in JS string
        if d0 is not None:
            js = js.replace(
                f'"id": "{evt["id"]}"',
                f'"d0_return": {d0}, "id": "{evt["id"]}"',
            )
            # Remove duplicate if exists
            js = js.replace(f'"d0_return": null,\n    "d0_return": {d0}', f'"d0_return": {d0}')
        if d5 is not None:
            js = js.replace(
                f'"d5_excess": null,\n    "d20_excess"',
                f'"d5_excess": {d5},\n    "d20_excess"',
            )
        if d20 is not None:
            js = js.replace(
                f'"d20_excess": null',
                f'"d20_excess": {d20}',
            )
        filled += 1

with open("events-data.js", "w", encoding="utf-8") as f:
    f.write(js)

print(f"Filled {filled} events with d0/d5/d20 data")

# Re-count
new_events = []
for m in re.finditer(r'\{[^}]*?"id":\s*"(evt_\d+)"[^}]*?\}', js, re.DOTALL):
    try:
        new_events.append(json.loads(m.group(0)))
    except:
        pass

with_d20 = sum(1 for e in new_events if e.get('d20_excess') is not None)
print(f"d20 fill rate: {with_d20}/{len(new_events)} ({round(with_d20/len(new_events)*100)}%)")
