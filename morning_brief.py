#!/usr/bin/env python3
"""☀️ 每日早报：美股过夜 + A股竞价 + 持仓预警 + 事件日历"""
import urllib.request, json, ssl, time, os, re
ssl._create_default_https_context = ssl._create_unverified_context

from push_wx import push

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY = time.strftime('%Y-%m-%d %A', time.localtime())

HOLDINGS = [
    {'name': '紫光股份', 'code': '000938', 'cost': 26.20, 'shares': 100, 'stop_pct': -8},
    {'name': '锡业股份', 'code': '000960', 'cost': 45.20, 'shares': 100, 'stop_pct': -8},
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
    """A股指数"""
    idx_map = {'1.000001': '上证', '0.399001': '深证', '0.399006': '创业板', '1.000688': '科创50'}
    lines = []
    for sid, name in idx_map.items():
        data = json.loads(_req(f'https://push2.eastmoney.com/api/qt/stock/get?secid={sid}&fields=f43,f170')).get('data',{})
        px = data.get('f43',0)/100
        chg = data.get('f170',0)/100
        lines.append(f'| {name} | {px:.0f} | **{chg:+.2f}%** |')
    return '\n'.join(lines) if lines else '暂无'


def fetch_holdings():
    """持仓详情"""
    total = CASH
    items = []
    alerts = []
    for h in HOLDINGS:
        mkt = 1 if h['code'].startswith('6') else 0
        data = json.loads(_req(f'https://push2.eastmoney.com/api/qt/stock/get?secid={mkt}.{h["code"]}&fields=f43,f170')).get('data',{})
        px = data.get('f43',0)/100
        cost = h['cost']
        stop_px = cost * (1 + h['stop_pct']/100)
        if px > 0:
            pl = (px - cost) * h['shares']
            pl_pct = (px/cost - 1) * 100
            total += px * h['shares']
            dist = px - stop_px
            flag = '🔴' if dist < 0 else '⚠️' if dist < cost*0.03 else '✅'
            items.append(f'| {h["name"]} | {px:.2f} | {pl_pct:+.1f}% | ¥{pl:+.0f} | {flag} ¥{stop_px:.2f} |')
            if dist < cost * 0.05:
                alerts.append(f'> 🚨 **{h["name"]}距止损线仅 ¥{dist:.2f}**')
        else:
            items.append(f'| {h["name"]} | -- | -- | -- | -- |')
            total += cost * h['shares']
            alerts.append(f'> ⚠️ {h["name"]} 数据获取失败')
    return '\n'.join(items), alerts, total


def fetch_us():
    """美股核心标的"""
    symbols = {'NVDA': '英伟达', 'SMH': '费城半导体', 'QQQ': '纳指ETF', 'TSLA': '特斯拉', 'SPCX': 'SpaceX'}
    lines = []
    for sym, name in symbols.items():
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d'
            data = json.loads(_req(url)).get('chart',{}).get('result',[{}])[0].get('meta',{})
            prev = data.get('previousClose', 0)
            curr = data.get('regularMarketPrice', 0)
            if prev and curr:
                chg = (curr/prev-1)*100
                lines.append(f'| {name}({sym}) | ${curr:.2f} | **{chg:+.2f}%** |')
        except:
            lines.append(f'| {name}({sym}) | -- | -- |')
    return '\n'.join(lines) if lines else '暂无'


def fetch_macro():
    """VIX/美元/原油"""
    items = []
    for sym, name in [('^VIX', 'VIX恐慌指数'), ('DX-Y.NYB', '美元指数')]:
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d'
            data = json.loads(_req(url)).get('chart',{}).get('result',[{}])[0].get('meta',{})
            curr = data.get('regularMarketPrice', 0)
            items.append(f'| {name} | {curr:.2f} |')
        except:
            items.append(f'| {name} | -- |')
    return '\n'.join(items)


def calendar_today():
    """今日关注事件"""
    return '- ⚠️ 中报预披露窗口（7/15截止）\n- 持仓标的未触发预警'


def main():
    print(f'[Morning] {TODAY}')

    idx = fetch_a_index()
    us = fetch_us()
    macro = fetch_macro()
    holdings, alerts, total = fetch_holdings()
    calendar = calendar_today()

    content = f'''# ☀️ 每日早报

> {TODAY}

---

## 📊 A股指数

| 指数 | 点位 | 涨跌 |
|------|------|------|
{idx}

---

## 🇺🇸 美股过夜

| 标的 | 价格 | 涨跌 |
|------|------|------|
{us}

---

## 🌐 宏观

| 指标 | 数值 |
|------|------|
{macro}

---

## 💼 我的持仓

| 标的 | 现价 | 涨跌 | 盈亏 | 止损线 |
|------|------|------|------|------|
{holdings}

总资产 ≈ **¥{total:.0f}** | 现金 ¥{CASH}

{chr(10).join(alerts) if alerts else '✅ 持仓无预警'}

---

## 📅 今日关注

{calendar}

---

> 推送时间：{time.strftime("%H:%M")}
'''

    push('☀️ 每日早报', content)


if __name__ == '__main__':
    main()
