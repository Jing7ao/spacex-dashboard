#!/usr/bin/env python3
"""🌙 每日晚报：行情复盘 + 持仓盈亏 + 美股盘前 + 明日日历"""
import urllib.request, json, ssl, time, os, re
ssl._create_default_https_context = ssl._create_unverified_context

from push_wx import push

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WN = ['周一','周二','周三','周四','周五','周六','周日']
TODAY = time.strftime('%Y-%m-%d ', time.localtime()) + _WN[time.localtime().tm_wday]

HOLDINGS = [
    {'name': '紫光股份', 'code': '000938', 'cost': 26.20, 'shares': 100},
    {'name': '锡业股份', 'code': '000960', 'cost': 45.20, 'shares': 100},
]
CASH = 2664


def _req(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode('utf-8', errors='replace') if 'eastmoney' in url or 'cls' in url else \
               resp.read().decode('gbk', errors='replace')
    except:
        return ''


def fetch_a_index():
    idx_map = {'1.000001': '上证', '0.399001': '深证', '0.399006': '创业板', '1.000688': '科创50'}
    lines = []
    for sid, name in idx_map.items():
        data = json.loads(_req(f'https://push2.eastmoney.com/api/qt/stock/get?secid={sid}&fields=f43,f170,f47')).get('data',{})
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
                alerts.append(f'> 🚨 {h["name"]} 今日跌幅超5%，距-8%止损仅差 {-pl_pct-8:.1f}%')
        else:
            items.append(f'| ❓ {h["name"]} | -- | -- | -- |')
            total += h['cost'] * h['shares']
    return '\n'.join(items), alerts, total


def fetch_us():
    symbols = {'gb_nvda': '英伟达', 'gb_tsla': '特斯拉', 'gb_smh': '费城半导体'}
    results = {}
    url = 'https://hq.sinajs.cn/list=' + ','.join(symbols.keys())
    try:
        raw = _req(url, timeout=10)
        for chunk in raw.split('var '):
            if '=' not in chunk: continue
            key = chunk.split('=')[0].strip()
            val = chunk.split('"')[1] if '"' in chunk else ''
            if key not in symbols: continue
            parts = val.split(',')
            if len(parts) < 5: continue
            price = float(parts[1]) if parts[1] else 0
            prev = float(parts[2]) if parts[2] else 0
            if price and prev:
                results[symbols[key]] = f'{(price/prev-1)*100:+.2f}%'
    except Exception as e:
        print(f'[US] {e}')
    return results


def fetch_turnover():
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


def scan_news():
    try:
        kw = json.loads(open(os.path.join(SCRIPT_DIR, 'keywords.json'), 'r', encoding='utf-8').read())
    except:
        return {'P0': [], 'P1': []}

    headlines = []
    try:
        url = 'https://www.cls.cn/api/sw?app=CailianpressWeb&os=web&sv=8.4.6'
        data = json.loads(_req(url)).get('data', {}).get('roll_data', [])
        for item in data[:60]:
            title = item.get('title', '')
            brief = item.get('brief', '')
            text = title + ' ' + brief
            headlines.append({'title': title, 'text': text})
    except:
        pass

    p0_matches = []
    p1_matches = []
    for cat_name, cat_data in kw.items():
        p0_list = cat_data.get('P0', [])
        p0_with = cat_data.get('P0_with', [])
        p1_list = cat_data.get('P1', [])
        for h in headlines:
            text = h['text']
            for kw_word in p0_list:
                if kw_word in text:
                    if p0_with:
                        for ctx in p0_with:
                            if ctx in text:
                                p0_matches.append(f"[{cat_data.get('name','?')}] {h['title']}")
                                break
                    else:
                        p0_matches.append(f"[{cat_data.get('name','?')}] {h['title']}")
                    break
            for kw_word in p1_list:
                if kw_word in text:
                    p1_matches.append(f"[{cat_data.get('name','?')}] {h['title']}")
                    break
    p0_matches = list(set(p0_matches))[:8]
    p1_matches = list(set(p1_matches))[:12]
    p1_matches = [m for m in p1_matches if m not in p0_matches]
    return {'P0': p0_matches, 'P1': p1_matches}


def main():
    print(f'[Evening] {TODAY}')

    idx = fetch_a_index()
    vol_label = fetch_turnover()
    holdings, alerts, total = fetch_holdings()
    us = fetch_us()
    news = scan_news()

    news_section = ''
    if news.get('P0'):
        news_section += '\n### 🚨 P0 今日事件\n\n'
        for m in news['P0']:
            news_section += f'- {m}\n'
    if news.get('P1'):
        news_section += '\n### 📰 P1 今日事件\n\n'
        for m in news['P1']:
            news_section += f'- {m}\n'

    us_text = ' | '.join([f'{k}:{v}' for k, v in us.items()]) if us else '暂无'

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

{news_section}## 🇺🇸 美股盘前

{us_text}

---

## 📅 明日关注

{calendar_tomorrow()}

---

> 推送时间：{time.strftime("%H:%M")}
'''

    push('🌙 每日晚报', content)


if __name__ == '__main__':
    main()
