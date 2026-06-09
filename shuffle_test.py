import json, urllib.request, sys, io, math, random
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
    "300567":"精测","002179":"中航","000099":"中信","300395":"菲利华",
    "688102":"斯瑞","600118":"卫星","603606":"东方","603662":"柯力"
}

def calc_rsi(cl):
    if len(cl)<15: return 50
    g=[max(cl[i]-cl[i-1],0) for i in range(1,len(cl))]
    l=[max(cl[i-1]-cl[i],0) for i in range(1,len(cl))]
    ag=sum(g[-14:])/14; al=sum(l[-14:])/14
    if al==0: return 100
    return 100-100/(1+ag/al)

def ma(cl,n): return sum(cl[-n:])/n if len(cl)>=n else sum(cl)/len(cl)

results = []
for code, name in STOCKS.items():
    m = "sh" if code.startswith(("6","5")) else "sz"
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,80,qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                      data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines)<65: continue
            closes = [float(k[2]) for k in klines if len(k)>2]
            vols = [float(k[5]) for k in klines if len(k)>5]
            if len(closes)<65: continue

        for offset in [6, 12, 18, 24, 30]:  # 5 different time points
            idx = -offset
            if len(closes) < abs(idx)+30: continue
            hist = closes[idx-60:idx]
            if len(hist) < 30: continue
            fwd = (closes[idx+5]-closes[idx])/closes[idx]*100 if idx+5 < 0 else 0
            cp = closes[idx]; m5=ma(hist,5); m20=ma(hist,20)
            rs=calc_rsi(hist)
            rsi_s=100 if rs<=20 else 80 if rs<=30 else 65 if rs<=40 else 55 if rs<=50 else 45 if rs<=60 else 30 if rs<=70 else 15 if rs<=80 else 0
            ma_s=100 if cp>m5 and m5>m20 else 75 if cp>m5 else 60 if cp>m20 else 40
            avg_v=sum(vols[max(0,idx-26):idx-1])/20 if idx-1>0 else sum(vols)/max(len(vols),1)
            vr=vols[idx-1]/avg_v if avg_v>0 else 1
            pc2=(closes[idx]-closes[idx-1])/closes[idx-1]*100
            vol_s=100 if vr>2 and pc2>0 else 70 if vr>1.5 and pc2>0 else 0 if vr>2 and pc2<0 else 30 if vr>1.5 and pc2<0 else 50
            bb_sum=sum((hist[-i-1]-m20)**2 for i in range(min(20,len(hist))))
            sd=math.sqrt(bb_sum/min(20,len(hist)))
            bu=m20+2*sd; bl=m20-2*sd; bp=(cp-bl)/(bu-bl) if bu>bl else 0.5
            bb_s=80 if bp<0.15 else 65 if bp<0.3 else 20 if bp>0.85 else 35 if bp>0.7 else 50
            chg_p=(closes[idx]-closes[idx-1])/closes[idx-1]*100
            vp_s=100 if (chg_p>0 and vr<0.8) else 20 if (chg_p>2 and vr>1.5) else 80 if (chg_p>0 and vr<1.2) else 50
            m60=ma(hist, min(60,len(hist)))
            trend_s=min(100,abs(m20-m60)/m60*500) if m60>0 else 50
            comp=rsi_s*0.22+ma_s*0.25+vol_s*0.15+bb_s*0.15+50*0.15+vp_s*0.0+trend_s*0.08
            results.append({"name":name,"comp":round(comp),"fwd":round(fwd,2)})
    except: pass

n=len(results)
print(f"样本: {n} 个 (多时间点)\n")

# Real correlation
xs=[r["comp"] for r in results]
ys=[r["fwd"] for r in results]
avg_x=sum(xs)/n; avg_y=sum(ys)/n
cov=sum((xs[i]-avg_x)*(ys[i]-avg_y) for i in range(n))
sx=math.sqrt(sum((x-avg_x)**2 for x in xs))
sy=math.sqrt(sum((v-avg_y)**2 for v in ys))
real_r=cov/(sx*sy) if sx>0 and sy>0 else 0

print(f"真实评分 vs 收益: r = {real_r:+.3f}")

# Shuffle test: 1000 iterations
random.seed(42)
shuffled_rs = []
better_count = 0
for _ in range(1000):
    shuffled_y = ys[:]
    random.shuffle(shuffled_y)
    cov2=sum((xs[i]-avg_x)*(shuffled_y[i]-avg_y) for i in range(n))
    sr=cov2/(sx*sy) if sx>0 and sy>0 else 0
    shuffled_rs.append(abs(sr))
    if abs(sr) > abs(real_r): better_count += 1

avg_shuf = sum(shuffled_rs)/len(shuffled_rs)
max_shuf = max(shuffled_rs)
pct_better = better_count/10  # as percentage

print(f"打乱后平均 |r| = {avg_shuf:.3f}")
print(f"打乱后最大 |r| = {max_shuf:.3f}")
print(f"打乱后 {better_count/10:.0f}% 的随机结果比真实效果好")

print()
if abs(real_r) < avg_shuf:
    print(">> 🔴 致命: 打乱标签后的平均相关性 > 真实相关性")
    print(">> 评分结构几乎完全是噪音——和扔骰子没有显著区别")
elif pct_better > 20:
    print(f">> 🔴 严重: {better_count/10:.0f}% 的随机标签比真实标签产生更好的拟合")
    print(">> 评分有过拟合嫌疑——但样本量太小，无法定论")
else:
    print(">> 🟢 通过: 真实相关性显著优于随机")
    print(">> 评分结构捕捉到了真实信号（虽然很弱）")

# Bonus: what DOES predict returns?
print()
print("=" * 50)
print("什么在真正预测收益？")
print("-" * 50)
for label, scorer in [("纯趋势强度", lambda r: r["comp"]*0 if True else 0)]: pass

# Check: do E1-confirmed stocks have better risk-adjusted returns?
# (This is the supply chain diagnosis test)
print("(需要E1/E2标注数据，待供应链rn字段映射后补充)")
