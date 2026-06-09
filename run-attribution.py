# 事件归因分析: 验证E1-A/B/C信号权重
# 输入: history-prices.json + events-data.js
# 输出: 三组信号的d5/d20平均超额收益对比

import json, re

# Load prices
with open("history-prices.json", "r", encoding="utf-8") as f:
    prices = json.load(f)

# Build price lookup: {code: {date: close}}
price_lookup = {}
for code, data in prices.items():
    price_lookup[code] = {d['date']: d['close'] for d in data}

# Load events from JS file
with open("events-data.js", "r", encoding="utf-8") as f:
    js = f.read()

# Extract events array
events = []
for m in re.finditer(r'\{[^}]*?"id":\s*"(evt_\d+)"[^}]*?\}', js, re.DOTALL):
    try:
        evt = json.loads(m.group(0))
        events.append(evt)
    except:
        pass

print(f"Loaded {len(events)} events\n")

# Classify events by E1 signal type
def classify(evt):
    notes = evt.get('notes', '')
    desc = evt.get('event_desc', '')
    ref = evt.get('source_ref', '')
    etype = evt.get('event_type', '')

    # E1-A: 点名客户
    if any(kw in notes + desc + ref for kw in ['点名客户', '点名', 'NVIDIA', '英伟达', '华为技术', '华为直接', 'TEL', 'Lam', 'AMAT', '应用材料', '泛林', '东京电子']):
        if '点名' in notes or '点名' in desc or '点名' in ref or '点名客户' in notes:
            return 'E1-A'
        if '英伟达' in notes + desc + ref and '13次' in notes:
            return 'E1-A'
        if '华为直接' in notes or '华为技术' in ref:
            return 'E1-A'
        if 'TEL' in desc or 'Lam' in desc or '三大半导体' in desc:
            return 'E1-A'

    # E1-C: 客户集中自述
    if any(kw in notes + desc for kw in ['客户集中', '集中度自述', '集中度风险', '客户集中度较高的风险']):
        return 'E1-C'

    # E1-B: 批量交付/批量供货
    if any(kw in notes + desc for kw in ['批量交付', '批量供货', 'E1-B', '批量交付7次', '批量供货8次', '批量交付1次']):
        return 'E1-B'

    # Fallback: check event type
    if etype == 'supply_confirm':
        return 'E1-B'  # default supply confirmation
    if etype == 'order_disclose':
        return 'E1-A'  # order disclosure = named customer
    if etype in ('cert_progress', 'sanction'):
        return None  # exclude policy/sanction events from signal analysis

    return None

# Calculate excess returns
def get_price(code, date_str, offset_days):
    """Get stock price on date + offset trading days"""
    if code not in price_lookup:
        return None
    dates = sorted(price_lookup[code].keys())
    try:
        idx = dates.index(date_str)
    except ValueError:
        # Find nearest trading day
        idx = None
        for i, d in enumerate(dates):
            if d >= date_str:
                idx = i
                break
        if idx is None:
            return None
    target_idx = idx + offset_days
    if target_idx < 0 or target_idx >= len(dates):
        return None
    return price_lookup[code][dates[target_idx]]

def calc_excess(evt, offset):
    code = evt.get('stock_code', '')
    date = evt.get('event_date', '')
    if not code or not date:
        return None
    stock_p = get_price(code, date, offset)
    hs300_p = get_price('000300', date, offset)

    if offset == 0:
        stock_base = get_price(code, date, -1)  # prev close
        hs300_base = get_price('000300', date, -1)
        if stock_base and stock_p:
            return round((stock_p / stock_base - 1) * 100, 2)
        return None

    stock_base = get_price(code, date, 0)
    hs300_base = get_price('000300', date, 0)
    if not stock_base or not stock_p or not hs300_base or not hs300_p:
        return None
    stock_ret = (stock_p / stock_base - 1) * 100
    hs300_ret = (hs300_p / hs300_base - 1) * 100
    return round(stock_ret - hs300_ret, 2)

# Classify and calculate
groups = {'E1-A': [], 'E1-B': [], 'E1-C': []}
for evt in events:
    grp = classify(evt)
    if grp is None:
        continue
    code = evt.get('stock_code', '')
    name = evt.get('stock_name', '')
    date = evt.get('event_date', '')
    d5 = calc_excess(evt, 5)
    d20 = calc_excess(evt, 20)
    if d5 is not None or d20 is not None:
        groups[grp].append({
            'id': evt.get('id', ''),
            'name': name,
            'date': date,
            'd5_excess': d5,
            'd20_excess': d20,
        })

print("=" * 60)
print("E1 Signal Attribution Results")
print("=" * 60)

for grp in ['E1-A', 'E1-B', 'E1-C']:
    items = groups[grp]
    if not items:
        print(f"\n{grp}: NO DATA")
        continue
    d5_vals = [i['d5_excess'] for i in items if i['d5_excess'] is not None]
    d20_vals = [i['d20_excess'] for i in items if i['d20_excess'] is not None]
    avg_d5 = round(sum(d5_vals)/len(d5_vals), 2) if d5_vals else None
    avg_d20 = round(sum(d20_vals)/len(d20_vals), 2) if d20_vals else None

    print(f"\n{grp} (n={len(items)}):")
    print(f"  avg d5 excess:  {avg_d5}% ({len(d5_vals)} valid)")
    print(f"  avg d20 excess: {avg_d20}% ({len(d20_vals)} valid)")
    for i in items:
        print(f"    {i['id']} {i['name'][:8]:8s} {i['date']}  d5={i['d5_excess']}  d20={i['d20_excess']}")

print("\n" + "=" * 60)
print("WEIGHT VALIDATION")
print("=" * 60)
a20 = round(sum([i['d20_excess'] for i in groups['E1-A'] if i['d20_excess'] is not None]) / max(1, len([i for i in groups['E1-A'] if i['d20_excess'] is not None])), 2) if groups['E1-A'] else 0
b20 = round(sum([i['d20_excess'] for i in groups['E1-B'] if i['d20_excess'] is not None]) / max(1, len([i for i in groups['E1-B'] if i['d20_excess'] is not None])), 2) if groups['E1-B'] else 0
c20 = round(sum([i['d20_excess'] for i in groups['E1-C'] if i['d20_excess'] is not None]) / max(1, len([i for i in groups['E1-C'] if i['d20_excess'] is not None])), 2) if groups['E1-C'] else 0

print(f"E1-A (点名客户):       avg d20 = {a20}%")
print(f"E1-B (批量交付):       avg d20 = {b20}%")
print(f"E1-C (客户集中自述):   avg d20 = {c20}%")

if a20 and b20 and c20:
    if a20 > b20 > c20:
        print("\n=> +2/+1/+1 权重方向正确!")
    elif a20 > b20:
        print("\n=> E1-A > E1-B 成立, 但 E1-B vs E1-C 差距不够")
    else:
        print("\n=> 权重需要调整!")
else:
    print("\n=> 数据不足, 无法完整验证")
