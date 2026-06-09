# backtest_exit_timing.py — 止损执行时机规则回测
# 验证: "放量跌→立刻执行" vs "缩量跌→等15分钟" 是否正确
import json, urllib.request, sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

STOCKS = {
    "603305":"旭升","002466":"天齐","300136":"信维","002281":"光迅",
    "600522":"中天","600089":"特变","688333":"铂力特","300346":"南大",
    "600869":"远东","300408":"三环","688268":"华特","300395":"菲利华",
    "688017":"绿的","688102":"斯瑞","300476":"胜宏","600584":"长电",
    "002149":"西部","600487":"亨通","688300":"联瑞","300502":"新易盛",
    "601689":"拓普","688012":"中微","002050":"三花","601138":"工业富联",
    "002156":"通富","688668":"鼎通","603308":"应流","301522":"上大",
    "605123":"派克","600456":"宝钛","603601":"再升","688629":"华丰",
    "300567":"精测","002179":"中航","000099":"中信","603606":"东方",
    "603662":"柯力","688631":"莱斯","600118":"卫星"
}

results = []
for code, name in STOCKS.items():
    m = "sh" if code.startswith(("6","5")) else "sz"
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,130,qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                      data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines) < 80: continue
            closes = [float(k[2]) for k in klines if len(k)>2]
            vols   = [float(k[5]) for k in klines if len(k)>5]
            if len(closes) < 80: continue

        # Slide through history: at each point, check if a big drop happened
        for i in range(40, len(closes)-20):
            chg = (closes[i]-closes[i-1])/closes[i-1]*100
            if chg > -3: continue  # only check days with >3% drop

            # Volume ratio: today vs 20-day avg
            avg_v = sum(vols[i-20:i])/20 if i>=20 else sum(vols[:i])/i
            vr = vols[i]/avg_v if avg_v>0 else 1.0

            # Classify: 放量跌 or 缩量跌
            is_high_vol = vr > 1.2
            is_low_vol = vr < 0.8

            # Post-drop outcomes
            fwd_1d = (closes[i+1]-closes[i])/closes[i]*100 if i+1<len(closes) else 0
            fwd_3d = (closes[min(i+3,len(closes)-1)]-closes[i])/closes[i]*100
            fwd_5d = (closes[min(i+5,len(closes)-1)]-closes[i])/closes[i]*100

            # Did it bounce or keep falling?
            bounced_1d = 1 if fwd_1d > 0 else 0
            bounced_3d = 1 if fwd_3d > 0 else 0

            sig = "放量跌" if is_high_vol else "缩量跌" if is_low_vol else "正常量跌"
            rule = "立刻执行(放量)" if is_high_vol else "等15分钟(缩量)" if is_low_vol else "按原规则"

            results.append({
                "name":name,"code":code,"chg":round(chg,2),"vr":round(vr,2),
                "sig":sig,"rule":rule,
                "fwd1":round(fwd_1d,2),"fwd3":round(fwd_3d,2),"fwd5":round(fwd_5d,2),
                "bounced1":bounced_1d,"bounced3":bounced_3d
            })
    except: pass

n = len(results)
print(f"样本: {n} 次跌幅>3%事件 (39只标的多时间点)\n")

# Group by signal
for label, selector in [("放量跌(>1.2x)", lambda r: r["sig"]=="放量跌"),
                         ("缩量跌(<0.8x)", lambda r: r["sig"]=="缩量跌"),
                         ("正常量跌", lambda r: r["sig"]=="正常量跌")]:
    group = [r for r in results if selector(r)]
    if len(group) < 5: continue
    ng = len(group)
    avg1 = sum(r["fwd1"] for r in group)/ng
    avg3 = sum(r["fwd3"] for r in group)/ng
    avg5 = sum(r["fwd5"] for r in group)/ng
    bounce1 = sum(r["bounced1"] for r in group)/ng*100
    bounce3 = sum(r["bounced3"] for r in group)/ng*100

    print(f"{label} (n={ng}):")
    print(f"  次日均值: {avg1:+.2f}%  反弹率: {bounce1:.0f}%")
    print(f"  3日均值:  {avg3:+.2f}%  反弹率: {bounce3:.0f}%")
    print(f"  5日均值:  {avg5:+.2f}%")
    action = "✅ 规则正确(继续跌)" if avg1<0 and avg3<0 else "⚠️ 规则存疑(居然反弹)" if avg1>0 else "⚪"
    print(f"  → 执行建议: {action}")
    print()

# Head-to-head: 放量 vs 缩量
hi = [r for r in results if r["sig"]=="放量跌"]
lo = [r for r in results if r["sig"]=="缩量跌"]
if len(hi)>10 and len(lo)>10:
    hi_avg = sum(r["fwd3"] for r in hi)/len(hi)
    lo_avg = sum(r["fwd3"] for r in lo)/len(lo)
    hi_bounce = sum(r["bounced3"] for r in hi)/len(hi)*100
    lo_bounce = sum(r["bounced3"] for r in lo)/len(lo)*100
    print("=" * 55)
    print(f"放量跌 3日: {hi_avg:+.2f}%  反弹率 {hi_bounce:.0f}% → 立刻执行")
    print(f"缩量跌 3日: {lo_avg:+.2f}%  反弹率 {lo_bounce:.0f}% → 等15分钟")
    print(f"差值: {lo_avg-hi_avg:+.2f}% (缩量比放量多反弹 {lo_avg-hi_avg:.1f} 个百分点)")
    if lo_avg > hi_avg and lo_bounce > hi_bounce:
        print("✅ 规则成立！缩量跌确实比放量跌更容易反弹")
    else:
        print("⚠️ 规则存疑——缩量跌没有比放量跌更容易反弹")
