#!/usr/bin/env python3
"""🌙 每日晚报：行情复盘 + 持仓盈亏 + 板块轮动 + 明日日历"""
import urllib.request, json, ssl, time, os, re
ssl._create_default_https_context = ssl._create_unverified_context

from push_wx import push as wx_push

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

HOLDINGS = [
    {'name': '紫光股份', 'code': '000938', 'cost': 26.20, 'shares': 100},
    {'name': '锡业股份', 'code': '000960', 'cost': 45.20, 'shares': 100},
]
CASH = 2664


# ═══ 行情 ═══════════════════════════════════════

def fetch_index():
    """拉取主要指数"""
    idx_map = {'sh000001': '上证', 'sz399001': '深证', 'sz399006': '创业板', 'sh000688': '科创50'}
    results = {}
    url = f'https://qt.gtimg.cn/q={",".join(idx_map.keys())}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        raw = urllib.request.urlopen(req, timeout=10).read().decode('gbk', errors='replace')
        for line in raw.split('\n'):
            if '~' not in line: continue
            p = line.split('~')
            if len(p) < 40: continue
            code = p[2]
            if code in idx_map:
                results[idx_map[code]] = {
                    'price': float(p[3]), 'chg_pct': float(p[32]) if p[32] else 0,
                    'volume': float(p[45]) / 1e8 if p[45] else 0
                }
    except Exception as e:
        print(f'[Fetch Index] Error: {e}')
    return results


def fetch_tencent(codes):
    results = {}
    for i in range(0, len(codes), 30):
        batch = codes[i:i + 30]
        url = f'https://qt.gtimg.cn/q={",".join(batch)}'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            raw = urllib.request.urlopen(req, timeout=10).read().decode('gbk', errors='replace')
            for line in raw.split('\n'):
                if '~' not in line: continue
                p = line.split('~')
                if len(p) < 40: continue
                results[p[2]] = {'name': p[1], 'price': float(p[3]), 'chg_pct': float(p[32]) if p[32] else 0}
        except Exception as e:
            print(f'[Fetch] Error: {e}')
    return results


def get_briefing_codes():
    try:
        with open(os.path.join(SCRIPT_DIR, 'monitor.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return sorted(set(re.findall(r"'([sz]h\\d{6})'", html)))
    except:
        return []


# ═══ 板块轮动 ═══════════════════════════════════

def sector_rotation(all_codes, prices):
    """统计184只里涨跌比，识别极端分化"""
    ups = sum(1 for _c, d in prices.items() if d.get('chg_pct', 0) > 0)
    downs = len(prices) - ups
    ratio = f'{ups}/{downs}'
    label = '偏多' if ups > downs * 1.5 else '偏空' if downs > ups * 1.5 else '均衡'
    return f'涨跌比 {ratio} ({label})'


# ═══ 美股期货 ═══════════════════════════════════

def fetch_us_futures():
    symbols = ['NASX', 'DXY', 'VXX']
    results = {}
    url = f'https://qt.gtimg.cn/q={",".join([f"us{s}" for s in symbols])}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        raw = urllib.request.urlopen(req, timeout=10).read().decode('gbk', errors='replace')
        for line in raw.split('\n'):
            if '~' not in line: continue
            p = line.split('~')
            if len(p) < 10: continue
            results[p[1]] = f'{float(p[32]):+.2f}%' if p[32] else '--'
    except:
        pass
    return results


# ═══ 主流程 ════════════════════════════════════

def main():
    print('[Evening] Fetching closing data...')

    # 1. 指数
    idx = fetch_index()
    idx_text = ' | '.join([f'{k} {v["chg_pct"]:+.2f}%' for k, v in idx.items()]) if idx else '获取失败'

    # 2. 持仓
    all_codes = get_briefing_codes()
    h_codes = []
    for h in HOLDINGS:
        h_codes.append(f'sh{h["code"]}' if h['code'].startswith('6') else f'sz{h["code"]}')
    prices = fetch_tencent(h_codes)

    total_value = CASH
    pl_lines = []
    for h in HOLDINGS:
        px = 0
        for _k, v in prices.items():
            if v['name'] == h['name']: px = v['price']; break
        if px > 0:
            pl = (px - h['cost']) * h['shares']
            pl_pct = (px / h['cost'] - 1) * 100
            total_value += px * h['shares']
            emoji = '🟢' if pl > 0 else '🔴' if pl < 0 else '⚪'
            pl_lines.append(f'{emoji} {h["name"]} ¥{px:.2f} ({pl_pct:+.1f}% ¥{pl:+.0f})')
        else:
            pl_lines.append(f'❓ {h["name"]} 无数据')
            total_value += h['cost'] * h['shares']

    holdings_text = ' | '.join(pl_lines)

    # 3. 板块轮动
    all_prices = fetch_tencent(all_codes[:50])  # sample for speed
    rotation_text = sector_rotation(all_codes, all_prices)

    # 4. 美股期货
    us_fut = fetch_us_futures()
    fut_text = ' | '.join([f'{k}:{v}' for k, v in us_fut.items()]) if us_fut else '获取失败'

    # 5. 明日日历（从催化日历提取）
    calendar_text = '中报预披露窗口（7/15截止）'

    # 6. 组装推送
    title = '🌙 晚报'
    content = f'指数: {idx_text}\n持仓: {holdings_text}\n轮动: {rotation_text}'
    remark = f'美股期货: {fut_text}\n明日: {calendar_text}\n总资产≈¥{total_value:.0f}'

    ok = wx_push(title, content[:200], remark[:100])
    print(f'[Evening] Push {"OK" if ok else "FAIL"}')
    print(f'[Evening]\n{content}\n---\n{remark}')


if __name__ == '__main__':
    main()
