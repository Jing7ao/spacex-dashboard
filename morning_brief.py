#!/usr/bin/env python3
"""☀️ 每日早报：美股过夜 + A股竞价 + 持仓预警 + 事件日历"""
import urllib.request, json, ssl, time, os, re
ssl._create_default_https_context = ssl._create_unverified_context

from push_wx import push

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WN = ['周一','周二','周三','周四','周五','周六','周日']
TODAY = time.strftime('%Y-%m-%d ', time.localtime()) + _WN[time.localtime().tm_wday]

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
    """美股核心标的 — 用新浪财经"""
    symbols = {'gb_nvda': '英伟达', 'gb_tsla': '特斯拉', 'gb_smh': '费城半导体'}
    lines = []
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
            name = symbols[key]
            price = float(parts[1]) if parts[1] else 0
            prev = float(parts[2]) if parts[2] else 0
            if price and prev:
                chg = (price/prev - 1) * 100
                lines.append(f'| {name} | ${price:.2f} | **{chg:+.2f}%** |')
    except Exception as e:
        print(f'[US] sina: {e}')
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
    return '- ⚗️ 中报预披露窗口（7/15截止）\n- 持仓标的未触发预警'


def scan_news():
    """扫描财联社快讯，匹配 P0/P1 关键词"""
    try:
        kw = json.loads(open(os.path.join(SCRIPT_DIR, 'keywords.json'), 'r', encoding='utf-8').read())
    except:
        return {'P0': [], 'P1': []}

    # 拉财联社快讯
    headlines = []
    try:
        url = 'https://www.cls.cn/api/sw?app=CailianpressWeb&os=web&sv=8.4.6'
        data = json.loads(_req(url)).get('data', {}).get('roll_data', [])
        for item in data[:60]:  # 最近60条
            title = item.get('title', '')
            brief = item.get('brief', '')
            text = title + ' ' + brief
            headlines.append({'title': title, 'text': text, 'time': item.get('ctime', '')})
    except Exception as e:
        print(f'[News] cls.cn: {e}')

    # Fallback: 东方财富快讯
    if not headlines:
        try:
            url = 'https://np-anotice-stock.eastmoney.com/api/security/ann/announcement/NoticeList?page_size=20&page_index=1&ann_type=SHA'
            data = json.loads(_req(url)).get('data', {}).get('list', [])
            for item in data:
                title = item.get('title', '')
                headlines.append({'title': title, 'text': title, 'time': item.get('notice_date', '')})
        except Exception as e:
            print(f'[News] eastmoney: {e}')

    p0_matches = []
    p1_matches = []

    for cat_name, cat_data in kw.items():
        p0_list = cat_data.get('P0', [])
        p0_with = cat_data.get('P0_with', [])
        p1_list = cat_data.get('P1', [])

        for h in headlines:
            text = h['text']
            # P0: keyword alone or keyword + context
            for kw_word in p0_list:
                if kw_word in text:
                    # Check if context words also match (if P0_with is specified)
                    if p0_with:
                        for ctx in p0_with:
                            if ctx in text:
                                p0_matches.append(f"[{cat_data.get('name','?')}] {h['title']}")
                                break
                    else:
                        p0_matches.append(f"[{cat_data.get('name','?')}] {h['title']}")
                    break

            # P1: simpler matching
            for kw_word in p1_list:
                if kw_word in text:
                    p1_matches.append(f"[{cat_data.get('name','?')}] {h['title']}")
                    break

    # Deduplicate
    p0_matches = list(set(p0_matches))[:8]
    p1_matches = list(set(p1_matches))[:12]
    # Remove P1 items already in P0
    p1_matches = [m for m in p1_matches if m not in p0_matches]

    print(f'[News] P0={len(p0_matches)} P1={len(p1_matches)}')
    return {'P0': p0_matches, 'P1': p1_matches}


def main():
    print(f'[Morning] {TODAY}')

    idx = fetch_a_index()
    us = fetch_us()
    macro = fetch_macro()
    holdings, alerts, total = fetch_holdings()
    calendar = calendar_today()
    news = scan_news()

    # 新闻事件
    news_section = ''
    if news.get('P0'):
        news_section += '\n### 🚨 P0 立即关注\n\n'
        for m in news['P0']:
            news_section += f'- {m}\n'
    if news.get('P1'):
        news_section += '\n### 📰 P1 值得关注\n\n'
        for m in news['P1']:
            news_section += f'- {m}\n'
    if not news.get('P0') and not news.get('P1'):
        news_section = '\n### 📰 新闻扫描\n\n暂无 P0/P1 事件命中\n'

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

{news_section}## 📅 今日关注

{calendar}

---

> 推送时间：{time.strftime("%H:%M")}
'''

    push('☀️ 每日早报', content)


if __name__ == '__main__':
    main()
