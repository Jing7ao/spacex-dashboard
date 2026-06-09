# backtest_exit_bear.py — 止损执行时机规则 多市场环境压力测试
import json, urllib.request, sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

STOCKS = {
    "603305":"旭升","002466":"天齐","300136":"信维","002281":"光迅",
    "600522":"中天","600089":"特变","688333":"铂力特","300346":"南大",
    "600869":"远东","300408":"三环","688268":"华特","300395":"菲利华",
    "688017":"绿的","688102":"斯瑞","300476":"胜宏","600584":"长电",
    "002149":"西部","600487":"亨通","601689":"拓普","688012":"中微",
    "002050":"三花","601138":"工业富联","002156":"通富","688668":"鼎通",
    "603308":"应流","600456":"宝钛","603601":"再升","688629":"华丰",
}

# Define market periods
PERIODS = {
    "2022熊市(1-4月)": ("2022-01-01", "2022-04-30"),
    "2022熊市(9-10月)": ("2022-09-01", "2022-10-31"),
    "2024震荡(1-2月)": ("2024-01-01", "2024-02-29"),
    "2024反弹(4-5月)": ("2024-04-01", "2024-05-31"),
    "2025牛市(1-3月)": ("2025-01-01", "2025-03-31"),
    "2026(1-6月)": ("2026-01-01", "2026-06-09"),
}

all_results = {}
for period_name, (start, end) in PERIODS.items():
    period_results = []
    for code, name in STOCKS.items():
        m = "sh" if code.startswith(("6","5")) else "sz"
        try:
            url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,250,qfq"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                          data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
                if not klines or len(klines) < 50: continue

            # Filter by date range
            filtered = [(float(k[2]),float(k[5])) for k in klines if len(k)>5 and start <= k[0] <= end]
            if len(filtered) < 30: continue
            closes = [c for c,v in filtered]
            vols = [v for c,v in filtered]

            for i in range(30, len(closes)-10):
                chg = (closes[i]-closes[i-1])/closes[i-1]*100
                if chg > -3: continue
                avg_v = sum(vols[i-20:i])/min(20,i)
                vr = vols[i]/avg_v if avg_v>0 else 1.0
                sig = "放量跌" if vr>1.2 else "缩量跌" if vr<0.8 else "正常量跌"
                fwd3 = (closes[min(i+3,len(closes)-1)]-closes[i])/closes[i]*100
                fwd5 = (closes[min(i+5,len(closes)-1)]-closes[i])/closes[i]*100
                period_results.append({"sig":sig,"fwd3":round(fwd3,2),"fwd5":round(fwd5,2)})
        except: pass

    all_results[period_name] = period_results

print("止损执行时机 · 多市场环境压力测试")
print("=" * 75)
print(f"{'市场阶段':<20} {'类型':<10} {'样本':>5} {'3日后':>8} {'5日后':>8} {'规则判断'}")
print("-" * 75)

for period_name, results in all_results.items():
    if len(results) < 10: continue
    hi = [r for r in results if r["sig"]=="放量跌"]
    lo = [r for r in results if r["sig"]=="缩量跌"]
    no = [r for r in results if r["sig"]=="正常量跌"]

    for label, group in [("放量跌",hi),("缩量跌",lo),("正常量跌",no)]:
        if len(group) < 5: continue
        avg3 = sum(r["fwd3"] for r in group)/len(group)
        avg5 = sum(r["fwd5"] for r in group)/len(group)

        # Rule judgment
        if label=="放量跌":
            judge = "✅ 立刻执行(反弹小)" if avg3 < 1 else "⚠️ 反弹不小"
        elif label=="缩量跌":
            judge = "✅ 可以等(反弹大)" if avg3 > 0.5 else "🔴 不能等!"
        else:
            judge = "⚪"

        print(f"{period_name:<20} {label:<10} {len(group):>5} {avg3:>+7.2f}% {avg5:>+7.2f}% {judge}")
    print()

# Summary
print("=" * 75)
print("规则稳定性总结:")
print("-" * 75)
for label, tag in [("放量跌","立刻执行"),("缩量跌","等1-3天")]:
    stable = 0; unstable = 0
    for period_name, results in all_results.items():
        group = [r for r in results if r["sig"]==label]
        if len(group) < 5: continue
        avg = sum(r["fwd3"] for r in group)/len(group)
        if label=="放量跌" and avg < 1.5: stable += 1
        elif label=="缩量跌" and avg > 0: stable += 1
        else: unstable += 1
    total = stable + unstable
    status = "✅ 稳定" if unstable==0 else f"⚠️ {unstable}/{total} 个阶段例外"
    print(f"  {label} → {tag}: {status}")
