# ic_decay.py — 因子IC衰减监控 + 动态权重输出
# 用法: python ic_decay.py
# 输出: ic_data.json (供面板加载) + 控制台IC趋势
import json, urllib.request, sys, io, math, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

STOCKS = {"603305":"旭升","002466":"天齐","300136":"信维","002281":"光迅","600522":"中天","600089":"特变","688333":"铂力特","300346":"南大","600869":"远东","300408":"三环","688268":"华特","300395":"菲利华","688017":"绿的","688102":"斯瑞","300476":"胜宏","600584":"长电","002149":"西部","600487":"亨通","688300":"联瑞","300502":"新易盛","601689":"拓普","688012":"中微","002050":"三花","601138":"工业富联","002156":"通富","688668":"鼎通","603308":"应流","301522":"上大","605123":"派克","600456":"宝钛","603601":"再升","688629":"华丰","300567":"精测","300308":"中际","300394":"天孚","002463":"沪电","002837":"英维克","002851":"麦格米特"}

def calc_rsi(cl):
    if len(cl)<15: return 50
    g=[max(cl[i]-cl[i-1],0) for i in range(1,len(cl))]; l=[max(cl[i-1]-cl[i],0) for i in range(1,len(cl))]
    ag=sum(g[-14:])/14; al=sum(l[-14:])/14
    return 100-100/(1+ag/al) if al>0 else 50

def ma(cl,n): return sum(cl[-n:])/n if len(cl)>=n else sum(cl)/len(n)

def rank_ic(xs, ys):
    n=len(xs); rx=sorted(range(n),key=lambda j:xs[j]); ry=sorted(range(n),key=lambda j:ys[j])
    rkx=[0]*n; rky=[0]*n
    for j,idx in enumerate(rx): rkx[idx]=j
    for j,idx in enumerate(ry): rky[idx]=j
    d2=sum((rkx[j]-rky[j])**2 for j in range(n))
    return 1-6*d2/(n*(n*n-1))

print("拉取K线...")
stock_data = {}
for code, name in STOCKS.items():
    m="sh" if code.startswith(("6","5")) else "sz"
    try:
        url=f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,200,qfq"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=5) as resp:
            data=json.loads(resp.read())
            klines=(data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines)<100: continue
            closes=[float(k[2]) for k in klines if len(k)>2]; vols=[float(k[5]) for k in klines if len(k)>5]
            dates=[k[0] for k in klines if len(k)>5]
            if len(closes)<100: continue
            stock_data[code]=[]
            for i in range(80,len(closes)-15,5):
                hist_c=closes[i-60:i]; hist_v=vols[i-60:i]; fwd=(closes[i+10]-closes[i])/closes[i]*100
                cp=closes[i]; m5=ma(hist_c,5); m20=ma(hist_c,20); rs=calc_rsi(hist_c)
                rsi_s=100 if rs<=20 else 80 if rs<=30 else 65 if rs<=40 else 55 if rs<=50 else 45 if rs<=60 else 30 if rs<=70 else 15 if rs<=80 else 0
                ma_s=100 if cp>m5 and m5>m20 else 75 if cp>m5 else 60 if cp>m20 else 40
                avg_v=sum(hist_v[-21:])/20; vr=vols[i]/avg_v if avg_v>0 else 1
                pc=(closes[i]-closes[i-1])/closes[i-1]*100
                vol_s=100 if vr>2 and pc>0 else 70 if vr>1.5 and pc>0 else 0 if vr>2 and pc<0 else 30 if vr>1.5 and pc<0 else 50
                bb_sum=sum((hist_c[-j-1]-m20)**2 for j in range(min(20,len(hist_c)))); sd=math.sqrt(bb_sum/min(20,len(hist_c)))
                bu=m20+2*sd; bl=m20-2*sd; bp=(cp-bl)/(bu-bl) if bu>bl else 0.5
                bb_s=80 if bp<0.15 else 65 if bp<0.3 else 20 if bp>0.85 else 35 if bp>0.7 else 50
                chg_p=(closes[i]-closes[i-1])/closes[i-1]*100
                vp_s=100 if (chg_p>0 and vr<0.8) else 20 if (chg_p>2 and vr>1.5) else 80 if (chg_p>0 and vr<1.2) else 50
                m60=ma(hist_c,min(60,len(hist_c))); trend_s=min(100,abs(m20-m60)/m60*500) if m60>0 else 50
                stock_data[code].append({"date":dates[i][:7],"rsi":rsi_s,"ma":ma_s,"vol":vol_s,"bb":bb_s,"vp":vp_s,"trend":trend_s,"fwd":fwd})
    except: pass
    time.sleep(0.2)

# Monthly IC
months=sorted(set(p["date"] for sd in stock_data.values() for p in sd))
factors=["rsi","ma","vol","bb","vp","trend"]; labels=["RSI","均线","成交量","布林带","量价健康","趋势强度"]

results=[]
for month in months:
    xs={f:[] for f in factors}; ys=[]
    for code,points in stock_data.items():
        mp=[p for p in points if p["date"]==month]
        if len(mp)==0: continue
        p=mp[0]
        for f in factors: xs[f].append(p[f])
        ys.append(p["fwd"])
    if len(ys)<5: continue
    row={"month":month,"n":len(ys)}
    for f in factors: row[f]=round(rank_ic(xs[f],ys),3)
    results.append(row)

# Recent 3-month average IC → dynamic weights
recent=results[-3:]
ic_avg={f: sum(r[f] for r in recent)/len(recent) for f in factors}
print(f"\n近期3月平均IC ({recent[0]['month']}~{recent[-1]['month']}):")
for f,l in zip(factors,labels):
    ic=ic_avg[f]; icon="📈" if ic>0.05 else "📉" if ic<-0.05 else "⚪"
    print(f"  {l:<8} IC={ic:+.3f} {icon}")

# Convert IC to weight multipliers: IC>0→boost, IC<0→reduce
# Base: if IC positive and significant (>0.03), boost weight; if negative, reduce
w_mult={f: max(0.3, min(2.0, 1.0+ic_avg[f]*3)) for f in factors}
print(f"\n动态权重乘数 (IC×3, clamp 0.3~2.0):")
for f,l in zip(factors,labels): print(f"  {l:<8} ×{w_mult[f]:.2f}")

output={"updated":time.strftime("%Y-%m-%d %H:%M:%S"),"ic_history":results,"ic_recent":ic_avg,"w_mult":w_mult}
with open(os.path.join(DIR,"ic_data.json"),"w",encoding="utf-8") as f:
    json.dump(output,f,ensure_ascii=False,indent=2)
print("\n✅ 已保存 ic_data.json")
