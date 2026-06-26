#!/usr/bin/env python3
"""☀️ 每日早报：美股过夜 + A股竞价 + P0/P1事件扫描 + 持仓预警"""
import urllib.request, json, ssl, time, os, re
ssl._create_default_https_context = ssl._create_unverified_context

from push_wx import push as wx_push

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 持仓配置 ──
HOLDINGS = [
    {'name': '紫光股份', 'code': '000938', 'cost': 26.20, 'shares': 100, 'stop': -8},
    {'name': '锡业股份', 'code': '000960', 'cost': 45.20, 'shares': 100, 'stop': -8},
]
CASH = 2664  # 神剑卖出后现金


# ═══ 数据拉取 ═══════════════════════════════════

def fetch_tencent(codes):
    """批量拉腾讯行情。codes: list of 'sz000938' / 'sh600584'"""
    results = {}
    for i in range(0, len(codes), 30):
        batch = codes[i:i + 30]
        url = f'https://qt.gtimg.cn/q={",".join(batch)}'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            raw = urllib.request.urlopen(req, timeout=10).read().decode('gbk', errors='replace')
            for line in raw.split('\n'):
                if '~' not in line:
                    continue
                p = line.split('~')
                if len(p) < 40:
                    continue
                results[p[2]] = {
                    'name': p[1], 'price': float(p[3]), 'prev_close': float(p[4]),
                    'chg_pct': float(p[32]) if p[32] else 0,
                    'pe': float(p[39]) if p[39] and float(p[39]) > 0 else -1
                }
        except Exception as e:
            print(f'[Fetch] Error: {e}')
    return results


def get_briefing_codes():
    """从 monitor.html 抽取 184 只标的代码"""
    try:
        with open(os.path.join(SCRIPT_DIR, 'monitor.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        codes = sorted(set(re.findall(r"'([sz]h\d{6})'", html)))
        return codes
    except:
        return []


def fetch_us_market():
    """拉取美股核心标的隔夜涨跌"""
    symbols = ['NVDA', 'SMH', 'SOX', 'TSLA', 'SPCX', 'QQQ', 'DXY']
    results = {}
    url = f'https://qt.gtimg.cn/q={"".join([f"us{s}," for s in symbols]).rstrip(",")}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        raw = urllib.request.urlopen(req, timeout=10).read().decode('gbk', errors='replace')
        for line in raw.split('\n'):
            if '~' not in line:
                continue
            p = line.split('~')
            if len(p) < 10:
                continue
            name = p[1]
            price = float(p[3]) if p[3] else 0
            chg = float(p[32]) if p[32] else 0
            results[name] = f'{chg:+.2f}%'
    except Exception as e:
        print(f'[Fetch US] Error: {e}')
    return results


# ═══ 关键词扫描 ══════════════════════════════════

def load_keywords():
    with open(os.path.join(SCRIPT_DIR, 'keywords.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def scan_keywords(kw_data, results=None):
    """扫描财联社快讯或其他新闻源，返回命中的 P0/P1。
    当前版本用简单的占位——等你接上新闻源后替换。"""
    return {'P0': [], 'P1': []}


# ═══ 持仓检查 ═══════════════════════════════════

def check_holdings(prices):
    lines = []
    alerts = []
    total_value = CASH
    for h in HOLDINGS:
        code = h['code']
        tcode = f'sh{code}' if code.startswith('6') else f'sz{code}'
        d = prices.get(code) or prices.get(tcode, {})
        px = d.get('price', 0)
        if px > 0:
            pl = (px - h['cost']) * h['shares']
            pl_pct = (px / h['cost'] - 1) * 100
            total_value += px * h['shares']
            stop_price = h['cost'] * (1 + h['stop'] / 100)
            dist_stop = px - stop_price
            flag = '⚠️⚠️' if dist_stop < 0 else '⚠️' if dist_stop < h['cost'] * 0.03 else '✅'
            lines.append(f'{flag} {h["name"]} ¥{px:.2f} ({pl_pct:+.1f}%) 止损¥{stop_price:.2f}')
            if dist_stop < h['cost'] * 0.03:
                alerts.append(f'🚨 {h["name"]}距止损线仅¥{dist_stop:.2f}')
        else:
            lines.append(f'❓ {h["name"]} 无数据')
            total_value += h['cost'] * h['shares']

    return '\n'.join(lines), alerts, total_value


# ═══ 竞价热力图 ═════════════════════════════════

def auction_heatmap(all_codes, prices):
    """找出竞价期异常波动的标的"""
    jumpers = []
    for code in all_codes:
        d = prices.get(code, {})
        chg = d.get('chg_pct', 0)
        if abs(chg) > 2:
            jumpers.append(f'{d.get("name","?")} {chg:+.1f}%')
    if not jumpers:
        return '竞价平稳'
    jumpers.sort(key=lambda x: float(x.split()[-1].replace('%', '')), reverse=True)
    return ' | '.join(jumpers[:8])


# ═══ 主流程 ════════════════════════════════════

def main():
    print('[Morning] Fetching data...')

    # 1. 美股
    us = fetch_us_market()
    us_text = ' | '.join([f'{k}:{v}' for k, v in us.items()]) if us else '数据获取失败'

    # 2. A股
    all_codes = get_briefing_codes()
    prices = fetch_tencent(all_codes)

    # 3. 持仓
    holdings_text, alerts, total_value = check_holdings(prices)

    # 4. 竞价
    auction_text = auction_heatmap(all_codes, prices)

    # 5. 关键词扫描
    kw_data = load_keywords()
    events = scan_keywords(kw_data)

    # 6. 组装推送
    p0_count = len(events.get('P0', []))
    p1_count = len(events.get('P1', []))

    title = '☀️ 早报'
    content_lines = [
        f'美股: {us_text}',
        f'竞价: {auction_text}',
        f'事件: P0×{p0_count} P1×{p1_count}',
    ]
    if alerts:
        content_lines.append(' | '.join(alerts))
    content = '\n'.join(content_lines)

    remark_lines = [f'总资产≈¥{total_value:.0f}']
    remark = '\n'.join(remark_lines)

    ok = wx_push(title, content[:200], remark[:100])  # 模板消息有长度限制
    print(f'[Morning] Push {"OK" if ok else "FAIL"}')
    print(f'[Morning] Content:\n{content}\n---\n{holdings_text}')


if __name__ == '__main__':
    main()
