import json, urllib.request, sys, io, math, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Random 50 stocks from different sectors (NOT in supply chain universe)
RANDOM_STOCKS = {
    "600519":"贵州茅台","000858":"五粮液","601318":"中国平安","600036":"招商银行",
    "000333":"美的集团","002415":"海康威视","600276":"恒瑞医药","000651":"格力电器",
    "600030":"中信证券","000002":"万科A","601166":"兴业银行","600887":"伊利股份",
    "000725":"京东方A","002594":"比亚迪","300750":"宁德时代","601012":"隆基绿能",
    "600809":"山西汾酒","000568":"泸州老窖","002714":"牧原股份","300059":"东方财富",
    "601888":"中国中免","600585":"海螺水泥","000063":"中兴通讯","002230":"科大讯飞",
    "300124":"汇川技术","600031":"三一重工","000792":"盐湖股份","002352":"顺丰控股",
    "300274":"阳光电源","600900":"长江电力","601088":"中国神华","000001":"平安银行",
    "600048":"保利发展","002475":"立讯精密","300015":"爱尔眼科","000625":"长安汽车",
    "600690":"海尔智家","002142":"宁波银行","300014":"亿纬锂能","000338":"潍柴动力",
    "600050":"中国联通","002129":"中环股份","300450":"先导智能","600104":"上汽集团",
    "000100":"TCL科技","002027":"分众传媒","300122":"智飞生物","600436":"片仔癀",
    "000776":"广发证券","601899":"紫金矿业"
}

def calc_rsi(closes):
    if len(closes) < 15: return 50
    gains = [max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    losses = [max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    ag=sum(gains[-14:])/14; al=sum(losses[-14:])/14
    if al==0: return 100
    return 100-100/(1+ag/al)

def calc_ma(cl,n):
    if len(cl)<n: return sum(cl)/len(cl)
    return sum(cl[-n:])/n

scored = []
for code, name in RANDOM_STOCKS.items():
    m = "sh" if code.startswith(("6","5")) else "sz"
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,80,qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                      data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines) < 65: continue
            closes = [float(k[2]) for k in klines if len(k)>2]
            vols   = [float(k[5]) for k in klines if len(k)>5]
            if len(closes) < 65: continue

        hist_cl = closes[-65:-6]
        fwd_ret = (closes[-1]-closes[-6])/closes[-6]*100
        cp = closes[-6]; m5 = calc_ma(hist_cl,5); m20 = calc_ma(hist_cl,20)
        rs = calc_rsi(hist_cl)

        rsi_s = 100 if rs<=20 else 80 if rs<=30 else 65 if rs<=40 else 55 if rs<=50 else 45 if rs<=60 else 30 if rs<=70 else 15 if rs<=80 else 0
        ma_s = 100 if cp>m5 and m5>m20 else 75 if cp>m5 else 60 if cp>m20 else 40
        avg_v = sum(vols[-26:-7])/20 if len(vols)>26 else sum(vols)/max(len(vols),1)
        vr = vols[-7]/avg_v if avg_v>0 else 1
        pc = (closes[-6]-closes[-7])/closes[-7]*100 if len(closes)>6 else 0
        vol_s = 100 if vr>2 and pc>0 else 70 if vr>1.5 and pc>0 else 0 if vr>2 and pc<0 else 30 if vr>1.5 and pc<0 else 50
        bb_sum = sum((hist_cl[-i-1]-m20)**2 for i in range(min(20,len(hist_cl))))
        sd = math.sqrt(bb_sum/min(20,len(hist_cl)))
        bu=m20+2*sd; bl=m20-2*sd; bp=(cp-bl)/(bu-bl) if bu>bl else 0.5
        bb_s = 80 if bp<0.15 else 65 if bp<0.3 else 20 if bp>0.85 else 35 if bp>0.7 else 50
        chg_p = (closes[-6]-closes[-7])/closes[-7]*100
        vp_s = 100 if (chg_p>0 and vr<0.8) else 20 if (chg_p>2 and vr>1.5) else 80 if (chg_p>0 and vr<1.2) else 50
        m60 = calc_ma(hist_cl, min(60,len(hist_cl)))
        trend_s = min(100, abs(m20-m60)/m60*500) if m60>0 else 50

        # Fund flow
        fund_s = 50
        try:
            em_m = 1 if code.startswith(("6","5")) else 0
            url3 = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids={em_m}.{code}&fields=f12,f20,f62"
            req3 = urllib.request.Request(url3, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req3, timeout=3) as resp3:
                j = json.loads(resp3.read())
                if j.get("data") and j["data"].get("diff"):
                    d = j["data"]["diff"][0]
                    mf = d.get("f62",0) or 0; mc = d.get("f20",0) or 1e10
                    fp = mf/mc
                    fund_s = 100 if fp>0.001 else 80 if fp>0.0005 else 65 if fp>0 else 35 if fp>-0.0005 else 20 if fp>-0.001 else 0
        except: pass

        # Weighted score using current manual weights
        comp = rsi_s*0.22 + ma_s*0.25 + vol_s*0.15 + bb_s*0.15 + fund_s*0.15 + vp_s*0.0 + trend_s*0.08
        scored.append({"name":name,"code":code,"comp":round(comp),"fwd":round(fwd_ret,2)})
    except: pass

n = len(scored)
print(f"随机50只(有效{n}只) | 评分=手拍权重 | 收益=5日后\n")

# Sort by score, compare top vs bottom
scored.sort(key=lambda x: x["comp"], reverse=True)
top_n = max(3, n//4)
top = scored[:top_n]
bot = scored[-top_n:]

print("=" * 70)
print(f"高分组 (评分>{top[-1]['comp']}, n={len(top)}) vs 低分组 (评分<{bot[0]['comp']}, n={len(bot)}):")
print("-" * 70)
for s in top:
    print(f"  {s['name']:<8} 评分{s['comp']:>3}  5日收益{s['fwd']:>+6.2f}%")
print("  ...")
for s in bot:
    print(f"  {s['name']:<8} 评分{s['comp']:>3}  5日收益{s['fwd']:>+6.2f}%")

avg_top = sum(s["fwd"] for s in top)/len(top)
avg_bot = sum(s["fwd"] for s in bot)/len(bot)
print(f"\n  高分组均值: {avg_top:+.2f}%")
print(f"  低分组均值: {avg_bot:+.2f}%")
print(f"  差值: {avg_top-avg_bot:+.2f}%")

# All stocks: score vs return correlation
xs = [s["comp"] for s in scored]
ys = [s["fwd"] for s in scored]
avg_x = sum(xs)/n; avg_y = sum(ys)/n
cov = sum((xs[i]-avg_x)*(ys[i]-avg_y) for i in range(n))
sx = math.sqrt(sum((x-avg_x)**2 for x in xs))
sy = math.sqrt(sum((v-avg_y)**2 for v in ys))
r_val = cov/(sx*sy) if sx>0 and sy>0 else 0

print(f"\n  全样本 r = {r_val:+.3f}")
print(f"  供应链池 r = -0.22 (此前验证)")
print(f"  随机池 r = {r_val:+.3f}")

if abs(r_val) < 0.1:
    print(f"\n  >> 结论: 评分在随机池上也无效 (r~0)")
    print(f"  >> 这不是'评分只在供应链有效'——是'评分在哪都无效'")
    print(f"  >> 评分应作为风控过滤器使用，不作为收益预测器")
elif abs(r_val) > 0.2:
    print(f"\n  >> 评分在随机池上有一定效果")
    print(f"  >> 说明评分捕捉的是通用市场因子，非供应链特有alpha")
