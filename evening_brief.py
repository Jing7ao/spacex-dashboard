#!/usr/bin/env python3
"""🌙 每日晚报：行情复盘 + 持仓盈亏 + 板块轮动 + 明日日历"""
import urllib.request, json, ssl, time, os, re
ssl._create_default_https_context = ssl._create_unverified_context

from push_wx import push as wx_push

HOLDINGS = [
    {'name': '紫光股份', 'code': '000938', 'cost': 26.20, 'shares': 100},
    {'name': '锡业股份', 'code': '000960', 'cost': 45.20, 'shares': 100},
]
CASH = 2664


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


def fetch_us():
    symbols = {'NVDA': '英伟达', 'SMH': '费城半导体', 'QQQ': '纳指ETF', 'VXX': 'VIX'}
    results = {}
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


def main():
    print('[Evening] Fetching...')

    # 指数
    idx = fetch_a_index()
    idx_text = ' | '.join([f'{k}:{v}' for k, v in idx.items()]) if idx else '获取失败'

    # 持仓
    total_value = CASH
    pl_lines = []
    for h in HOLDINGS:
        mkt = 1 if h['code'].startswith('6') else 0
        url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={mkt}.{h["code"]}&fields=f43,f170'
        px = 0
        try:
            data = json.loads(_req(url)).get('data', {})
            px = data.get('f43', 0) / 100
        except:
            pass
        if px > 0:
            pl = (px - h['cost']) * h['shares']
            pl_pct = (px / h['cost'] - 1) * 100
            total_value += px * h['shares']
            emoji = '🟢' if pl > 0 else '🔴'
            pl_lines.append(f'{emoji}{h["name"]}¥{px:.2f}({pl_pct:+.1f}%)')
        else:
            pl_lines.append(f'❓{h["name"]}无数据')
            total_value += h['cost'] * h['shares']

    holdings_text = ' '.join(pl_lines)

    # 美股
    us = fetch_us()
    us_text = ' | '.join([f'{k}:{v}' for k, v in us.items()]) if us else '获取失败'

    # 组装
    title = '🌙 晚报'
    content = f'指数 {idx_text}\n持仓 {holdings_text}'
    remark = f'美股 {us_text}\n总资产≈¥{total_value:.0f}'

    ok = wx_push(title, content[:200], remark[:100])
    print(f'[Evening] Push {"OK" if ok else "FAIL"}')
    print(content)
    print(remark)


if __name__ == '__main__':
    main()
