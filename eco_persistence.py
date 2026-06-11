# eco_persistence.py — 生态排名持续性回测
# 问题: 连续N天排前2的生态，后续是否持续跑赢？
import json, urllib.request, sys, io, math, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 8生态 + 代表标的
ECOS = {
    "光通信": ["000988","301165","688498","601869","600487","000938","300570","300620","002281","600522","603606"],
    "国产AI算力": ["688629","603986","002371","688012","300567","002281","000938","300570","300620","600487"],
    "英伟达生态": ["300476","688300","300502","002837","002851","300308","300394","601138","600584","002156","002916"],
    "国产机器人": ["688017","603662","601100","603809","002050","601689"],
    "马斯克生态": ["688102","002149","300136","600456","603601","301522","688333","605123","603308","300395","603305","002050","601689","002036"],
    "商业航天": ["600118","688070","600456","603601","688102","002149","301522","688333","605123","603308"],
    "电力能源": ["603191","600362","600869","603606","600089","601179","600312","600406","000400","002335","002364","002028","600875","601126","601877","002270"],
    "低空经济": ["688631","000099"]
}

# Pull daily prices for all stocks, compute daily eco returns
all_codes = list(set(c for codes in ECOS.values() for c in codes))
print(f"拉取 {len(all_codes)} 只标的日线...")
stock_returns = {}  # code -> [(date, return)]
for code in all_codes:
    m = "sh" if code.startswith(("6","5")) else "sz"
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,120,qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                      data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines) < 60: continue
            returns = []
            for i in range(1, len(klines)):
                c0 = float(klines[i-1][2]); c1 = float(klines[i][2])
                if c0 > 0: returns.append((klines[i][0], (c1-c0)/c0*100))
            if len(returns) >= 50: stock_returns[code] = returns
    except: pass
    time.sleep(0.15)

print(f"有效标的: {len(stock_returns)}")

# Compute daily ecosystem returns (equal-weighted average)
dates = set()
for rets in stock_returns.values():
    for d,_ in rets: dates.add(d)
dates = sorted(dates)[-60:]  # last 60 trading days

eco_daily = {}  # eco -> {date: return}
for eco_name, codes in ECOS.items():
    valid = [c for c in codes if c in stock_returns]
    if len(valid) < 3: continue
    eco_daily[eco_name] = {}
    for date in dates:
        day_returns = []
        for c in valid:
            match = [r for r in stock_returns[c] if r[0]==date]
            if match: day_returns.append(match[0][1])
        if len(day_returns) >= 3:
            eco_daily[eco_name][date] = sum(day_returns)/len(day_returns)

# Now test: if eco ranked top-2 for N consecutive days, what's the forward return?
print(f"\n生态持续性回测 ({len(dates)} 个交易日)")
print("=" * 60)

for persistence_days in [1, 2, 3, 5]:
    signals = []  # (eco, date, fwd_return)
    for i in range(len(dates)-10):
        today = dates[i]
        forward_date = dates[i+5]  # 5-day forward
        # Get today's rankings
        today_returns = {}
        for eco_name in eco_daily:
            if today in eco_daily[eco_name]:
                today_returns[eco_name] = eco_daily[eco_name][today]
        if len(today_returns) < 5: continue
        ranked = sorted(today_returns.items(), key=lambda x: x[1], reverse=True)
        top2 = {ranked[0][0], ranked[1][0]}
        # Check: was this eco in top2 for the past N days?
        for eco_name in eco_daily:
            if eco_name not in top2: continue
            if forward_date not in eco_daily[eco_name]: continue
            persistent = True
            for j in range(1, persistence_days+1):
                past_idx = i - j
                if past_idx < 0: persistent = False; break
                past_date = dates[past_idx]
                if past_date not in eco_daily[eco_name]: persistent = False; break
                past_returns = {}
                for e in eco_daily:
                    if past_date in eco_daily[e]: past_returns[e] = eco_daily[e][past_date]
                if len(past_returns) < 5: persistent = False; break
                pr = sorted(past_returns.items(), key=lambda x: x[1], reverse=True)
                pt = {pr[0][0], pr[1][0]}
                if eco_name not in pt: persistent = False; break
            if persistent:
                fwd = eco_daily[eco_name][forward_date]
                signals.append((eco_name, today, fwd))

    if len(signals) >= 5:
        avg_fwd = sum(s[2] for s in signals)/len(signals)
        pos_rate = sum(1 for s in signals if s[2] > 0)/len(signals)*100
        # Baseline: random pick from same days
        all_fwds = []
        for i in range(len(dates)-10):
            fd = dates[i+5]
            for e in eco_daily:
                if fd in eco_daily[e]: all_fwds.append(eco_daily[e][fd])
        baseline = sum(all_fwds)/len(all_fwds) if all_fwds else 0
        print(f"  连续{persistence_days}天前2: {len(signals)}次信号  5日后均值{avg_fwd:+.2f}%  胜率{pos_rate:.0f}%  vs 随机{baseline:+.2f}%")
    else:
        print(f"  连续{persistence_days}天前2: 信号不足")
