import json, urllib.request, sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

STOCKS_DATA = [
    ("688017","绿的谐波","E1"),("600487","亨通光电","E1"),("688102","斯瑞新材","E1"),
    ("601877","正泰电器","E1"),("600362","江西铜业","E1"),("002149","西部材料","E1"),
    ("002050","三花智控","E1"),("601689","拓普集团","E1"),("300395","菲利华","E1"),
    ("300476","胜宏科技","E1"),("002281","光迅科技","E1"),("300346","南大光电","E1"),
    ("002179","中航光电","E1"),("600456","宝钛股份","E1"),("603308","应流股份","E1"),
    ("688300","联瑞新材","E1"),("603601","再升科技","E1"),
    ("300136","信维通信","E2"),("300308","中际旭创","E2"),("002036","联创电子","E2"),
    ("301522","上大股份","E2"),("605123","派克新材","E2"),("688333","铂力特","E2"),
    ("002792","通宇通讯","E2"),
    ("600869","远东股份","E3"),("688268","华特气体","E3"),("300408","三环集团","E3"),
    ("601138","工业富联","E3"),("600584","长电科技","E3"),("603305","旭升集团","E3"),
    ("002156","通富微电","E3"),("002916","深南电路","E3"),("300502","新易盛","E3"),
    ("600745","闻泰科技","E3"),("688668","鼎通科技","E3"),("603606","东方电缆","E3"),
    ("600089","特变电工","E3"),("600522","中天科技","E3"),("002466","天齐锂业","E3"),
]

results = []
for code, name, level in STOCKS_DATA:
    m = "sh" if code.startswith(("6","5")) else "sz"
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,130,qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                      data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines) < 100: continue
            closes = [float(k[2]) for k in klines if len(k)>2]
            if len(closes) < 100: continue

        # Multiple windows: look at max drawdown and tail risk
        for window in [20, 40, 60]:
            for start in range(0, len(closes)-window-10, 20):
                segment = closes[start:start+window]
                peak = segment[0]
                max_dd = 0
                for p in segment:
                    if p > peak: peak = p
                    dd = (peak-p)/peak*100
                    if dd > max_dd: max_dd = dd

                # Also track: how often does it drop >10%?
                big_drops = 0
                for i in range(1, len(segment)):
                    drop = (segment[i]-segment[i-1])/segment[i-1]*100
                    if drop < -5: big_drops += 1

                # 5-day forward return
                fwd_5 = (closes[start+window]-segment[-1])/segment[-1]*100 if start+window < len(closes) else 0

                results.append({
                    "name":name,"code":code,"level":level,
                    "window":window,"max_dd":round(max_dd,1),
                    "big_drops":big_drops,"fwd_5":round(fwd_5,2)
                })
    except: pass

n = len(results)
print(f"样本: {n} 个观测 (多窗口)\n")

# Group by evidence level
for level, label in [("E1","E1 年报实锤"),("E2","E2 推断"),("E3","E3 虚/弱")]:
    group = [r for r in results if r["level"]==level]
    if not group: continue
    n_g = len(group)
    avg_dd = sum(r["max_dd"] for r in group)/n_g
    avg_drops = sum(r["big_drops"] for r in group)/n_g
    # Tail risk: 95th percentile max drawdown
    dds = sorted([r["max_dd"] for r in group])
    tail_dd = dds[int(n_g*0.95)] if n_g>20 else dds[-1]
    # Crash frequency: % of windows with >15% drawdown
    crashes = sum(1 for r in group if r["max_dd"]>15)/n_g*100

    print(f"{label} (n={n_g}):")
    print(f"  平均最大回撤: {avg_dd:.1f}%")
    print(f"  95%分位回撤: {tail_dd:.1f}%")
    print(f"  >15%回撤概率: {crashes:.0f}%")
    print(f"  单日>5%暴跌(每窗口): {avg_drops:.1f}次")
    print()

# Head to head
e1_dds = [r["max_dd"] for r in results if r["level"]=="E1"]
e3_dds = [r["max_dd"] for r in results if r["level"]=="E3"]

if e1_dds and e3_dds:
    n1,n3 = len(e1_dds),len(e3_dds)
    avg1,avg3 = sum(e1_dds)/n1,sum(e3_dds)/n3
    v1 = sum((x-avg1)**2 for x in e1_dds)/(n1-1)
    v3 = sum((x-avg3)**2 for x in e3_dds)/(n3-1)
    se = math.sqrt(v1/n1+v3/n3)
    t = (avg3-avg1)/se if se>0 else 0

    print("=" * 55)
    print(f"E3 平均回撤 - E1 平均回撤 = {avg3-avg1:+.1f}%")
    print(f"t = {t:+.2f} {'✅ E3显著更惨' if t>1.96 else '⚪ 差异不显著'}")
    print()

    if avg3 > avg1:
        print(f">> E3标的比E1多回撤{avg3-avg1:.1f}%")
        print(f">> E1的价值: 在同样持有期内, E1帮你少亏{avg3-avg1:.1f}%")
        if t > 1.5:
            print(f">> 接近显著(t={t:.1f})——样本再大一点可能就确认了")
    else:
        print(f">> 回撤上E1和E3没有差异——年报实锤不等于抗跌")

# Bonus: worst-case analysis
print()
print("=" * 55)
print("极端风险对比 (最大回撤>20%的窗口):")
print("-" * 55)
for level, label in [("E1","E1"),("E3","E3")]:
    group = [r for r in results if r["level"]==level]
    extreme = [r for r in group if r["max_dd"]>20]
    print(f"  {label}: {len(extreme)}/{len(group)} = {len(extreme)/len(group)*100:.0f}% 的窗口出现>20%回撤")
    if extreme:
        # Show worst 3
        worst = sorted(extreme, key=lambda r: r["max_dd"], reverse=True)[:3]
        for w in worst:
            print(f"    {w['name']} {w['window']}日窗 最大回撤{w['max_dd']:.0f}%")
