#!/usr/bin/env python3
"""🌙 每日晚报：行情复盘 + 持仓盈亏 + 美股期货 + 明日日历"""
import urllib.request, json, ssl, time, os
ssl._create_default_https_context = ssl._create_unverified_context

from push_wx import push

TODAY = time.strftime('%Y-%m-%d %A', time.localtime())

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
    except:
        return ''


def fetch_a_index():
    idx_map = {'1.000001': '上证', '0.399001': '深证', '0.399006': '创业板', '1.000688': '科创50'}
    lines = []
    for sid, name in idx_map.items():
        data = json.loads(_req(f'https://push2.eastmoney.com/api/qt/stock/get?secid={sid}&fields=f43,f170,f47,f48')).get('data',{})
        px = data.get('f43',0)/100
        chg = data.get('f170',0)/100
        vol = data.get('f47',0)/1e8 if data.get('f47') else 0
        lines.append(f'| {name} | {px:.0f} | **{chg:+.2f}%** | {vol:.0f}亿 |')
    return '\n'.join(lines) if lines else '暂无'


def fetch_holdings():
    total = CASH
    items = []
    alerts = []
    for h in HOLDINGS:
        mkt = 1 if h['code'].startswith('6') else 0
        data = json.loads(_req(f'https://push2.eastmoney.com/api/qt/stock/get?secid={mkt}.{h["code"]}&fields=f43,f170')).get('data',{})
        px = data.get('f43',0)/100
        if px > 0:
            pl = (px - h['cost']) * h['shares']
            pl_pct = (px/h['cost'] - 1) * 100
            total += px * h['shares']
            emoji = '🟢' if pl > 0 else '🔴'
            items.append(f'| {emoji} {h["name"]} | ¥{px:.2f} | {pl_pct:+.1f}% | ¥{pl:+.0f} |')
            if pl_pct < -5:
                alerts.append(f'> 🚨 {h["name"]} 今日跌幅超5%，距成本-8%止损还差 {-pl_pct-8:.1f}%')
        else:
            items.append(f'| ❓ {h["name"]} | -- | -- | -- |')
            total += h['cost'] * h['shares']
    return '\n'.join(items), alerts, total


def fetch_us():
    symbols = {'NVDA': '英伟达', 'SMH': '费城半导体', 'QQQ': '纳指ETF', 'VXX': 'VIX'}
    lines = []
    for sym, name in symbols.items():
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d'
            data = json.loads(_req(url)).get('chart',{}).get('result',[{}])[0].get('meta',{})
            prev = data.get('previousClose',0)
            curr = data.get('regularMarketPrice',0)
            if prev and curr:
                chg = (curr/prev-1)*100
                lines.append(f'| {name}({sym}) | ${curr:.2f} | **{chg:+.2f}%** |')
        except:
            pass
    return '\n'.join(lines) if lines else '暂无'


def fetch_turnover():
    """市场情绪"""
    try:
        data = json.loads(_req('https://push2.eastmoney.com/api/qt/stock/get?secid=1.000001&fields=f47')).get('data',{})
        vol = data.get('f47',0)/1e8
        if vol > 35000: return f'**{vol:.0f}亿** 天量 🔥'
        elif vol > 25000: return f'{vol:.0f}亿 放量'
        elif vol > 15000: return f'{vol:.0f}亿 正常'
        else: return f'{vol:.0f}亿 缩量'
    except:
        return '--'


def calendar_tomorrow():
    return '- 中报预披露窗口继续\n- 关注美股期货夜盘方向\n- 明日开盘前关注竞价热力图'


def main():
    print(f'[Evening] {TODAY}')

    idx = fetch_a_index()
    vol_label = fetch_turnover()
    holdings, alerts, total = fetch_holdings()
    us = fetch_us()

    content = f'''# 🌙 每日晚报

> {TODAY} 收盘

---

## 📊 今日收盘

| 指数 | 点位 | 涨跌 | 成交额 |
|------|------|------|------|
{idx}

市场状态：{vol_label}

---

## 💼 我的持仓

| 标的 | 现价 | 涨跌 | 盈亏 |
|------|------|------|------|
{holdings}

总资产 ≈ **¥{total:.0f}** | 现金 ¥{CASH}

{chr(10).join(alerts) if alerts else '✅ 持仓正常'}

---

## 🇺🇸 美股盘前

{us}

---

## 📅 明日关注

{calendar_tomorrow()}

---

> 推送时间：{time.strftime("%H:%M")}
'''

    push('🌙 每日晚报', content)


if __name__ == '__main__':
    main()
