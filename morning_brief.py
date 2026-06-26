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
CASH = 2664


# ═══ 数据拉取 ═══════════════════════════════════

def _req(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode('utf-8', errors='replace') if 'eastmoney' in url else \
               resp.read().decode('gbk', errors='replace')
    except Exception as e:
        print(f'[Req] {url[:60]}: {e}')
        return ''


def fetch_a_index():
    """用东方财富 API 拉A股指数（比腾讯更稳定）"""
    idx_map = {'1.000001': '上证', '0.399001': '深证', '0.399006': '创业板', '1.000688': '科创50'}
    results = {}
    for sid, name in idx_map.items():
        url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={sid}&fields=f43,f170'
        try:
            data = json.loads(_req(url)).get('data', {})
            px = data.get('f43', 0) / 100
            chg_pct = data.get('f170', 0) / 100
            results[name] = f'{chg_pct:+.2f}%'
        except:
            results[name] = '--'
    return results


def fetch_holdings():
    """拉持仓现价"""
    codes = []
    for h in HOLDINGS:
        mkt = 1 if h['code'].startswith('6') else 0
        codes.append(f'{mkt}.{h["code"]}')
    url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={",".join(codes)}'
    try:
        raw = _req(url)
        # Eastmoney batch API returns differently, fetch one by one
        pass
    except:
        pass

    # Fallback: one by one
    results = {}
    for h in HOLDINGS:
        mkt = 1 if h['code'].startswith('6') else 0
        url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={mkt}.{h["code"]}&fields=f43,f170'
        try:
            data = json.loads(_req(url)).get('data', {})
            px = data.get('f43', 0) / 100
            results[h['code']] = {'name': h['name'], 'price': px, 'cost': h['cost'], 'shares': h['shares'],
                                   'stop': h['cost'] * (1 + h['stop'] / 100)}
        except:
            results[h['code']] = {'name': h['name'], 'price': 0, 'cost': h['cost'], 'shares': h['shares'],
                                   'stop': h['cost'] * (1 + h['stop'] / 100)}
    return results


def fetch_us():
    """拉美股核心标的"""
    symbols = {'NVDA': '英伟达', 'SMH': '费城半导体ETF', 'QQQ': '纳斯达克ETF', 'TSLA': '特斯拉', 'SPCX': 'SpaceX'}
    results = {}
    # Use Yahoo Finance API via a free proxy
    for sym, name in symbols.items():
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
            prev = meta.get('previousClose', 0)
            curr = meta.get('regularMarketPrice', 0)
            if prev and curr:
                chg = (curr / prev - 1) * 100
                results[name] = f'{chg:+.2f}%'
        except Exception as e:
            print(f'[US] {sym}: {e}')
    return results


# ═══ 主流程 ════════════════════════════════════

def main():
    print('[Morning] Fetching...')

    # 1. A股指数
    idx = fetch_a_index()
    idx_text = ' | '.join([f'{k}:{v}' for k, v in idx.items()]) if idx else '指数获取失败'

    # 2. 美股
    us = fetch_us()
    us_text = ' | '.join([f'{k}:{v}' for k, v in us.items()]) if us else '美股获取失败'

    # 3. 持仓
    holdings = fetch_holdings()
    total_value = CASH
    pl_lines = []
    alerts = []
    for h in HOLDINGS:
        d = holdings.get(h['code'], {})
        px = d.get('price', 0)
        if px > 0:
            pl = (px - h['cost']) * h['shares']
            pl_pct = (px / h['cost'] - 1) * 100
            total_value += px * h['shares']
            dist_stop = px - d.get('stop', h['cost'] * 0.92)
            flag = '⚠️' if dist_stop < 0 else '✅'
            pl_lines.append(f'{flag}{h["name"]}¥{px:.2f}({pl_pct:+.1f}%)')
            if dist_stop < h['cost'] * 0.03:
                alerts.append(f'距止损¥{dist_stop:.2f}')
        else:
            pl_lines.append(f'❓{h["name"]}无数据')
            total_value += h['cost'] * h['shares']

    holdings_text = ' '.join(pl_lines)

    # 4. 组装推送
    title = '☀️ 早报'
    content_lines = [f'指数 {idx_text}', f'美股 {us_text}']
    if pl_lines:
        content_lines.append(f'持仓 {holdings_text}')
    if alerts:
        content_lines.append(' | '.join(alerts))
    content = '\n'.join(content_lines)
    remark = f'总资产≈¥{total_value:.0f}'

    ok = wx_push(title, content[:200], remark[:100])
    print(f'[Morning] Push {"OK" if ok else "FAIL"}')
    print(content)
    print(remark)


if __name__ == '__main__':
    main()
