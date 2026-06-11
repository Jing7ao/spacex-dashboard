# factor_check.py — 全因子IC分析（使用研究池，262只标的）
import json, urllib.request, sys, io, math, time, random, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

# Load research pool
try:
    with open(os.path.join(DIR, "research_pool.json"), encoding="utf-8") as f:
        pool = json.load(f)["codes"][:200]  # First 200 to keep runtime manageable
except:
    pool = list({"603305":1,"300136":1,"002281":1,"600522":1,"600089":1,"688017":1,"300476":1,"600487":1,"601689":1,"002050":1,"601138":1,"002837":1,"300308":1,"300394":1,"300502":1,"002916":1,"600456":1,"688300":1,"601208":1,"600183":1,"688102":1,"002149":1,"600584":1,"688012":1,"002156":1,"688268":1,"300346":1,"300666":1,"688126":1,"300274":1,"601012":1,"300750":1}.keys())

def calc_rsi(cl):
    if len(cl)<15: return 50
    g=[max(cl[i]-cl[i-1],0) for i in range(1,len(cl))]
    l=[max(cl[i-1]-cl[i],0) for i in range(1,len(cl))]
    ag=sum(g[-14:])/14; al=sum(l[-14:])/14
    return 100-100/(1+ag/al) if al>0 else 50
def ma(cl,n): return sum(cl[-n:])/n if len(cl)>=n else sum(cl)/len(cl)
def rank_ic(xs,ys):
    n=len(xs); rx=sorted(range(n),key=lambda j:xs[j]); ry=sorted(range(n),key=lambda j:ys[j])
    rkx=[0]*n; rky=[0]*n
    for j,idx in enumerate(rx): rkx[idx]=j
    for j,idx in enumerate(ry): rky[idx]=j
    d2=sum((rkx[j]-rky[j])**2 for j in range(n))
    return 1-6*d2/(n*(n*n-1))

print(f"Research pool: {len(pool)} stocks")
print("Pulling K-line...")
results = []
for code in pool:
    m="sh" if code.startswith(("6","5")) else "sz"
    try:
        url=f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,100,qfq"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=5) as resp:
            data=json.loads(resp.read())
            klines=(data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                    data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines)<70: continue
            closes=[float(k[2]) for k in klines if len(k)>2]
            vols=[float(k[5]) for k in klines if len(k)>5]
            if len(closes)<70: continue
        for i in range(50,len(closes)-15,5):
            hist_c=closes[i-50:i]; hist_v=vols[i-50:i]
            fwd5=(closes[i+5]-closes[i])/closes[i]*100
            fwd10=(closes[i+10]-closes[i])/closes[i]*100
            cp=closes[i]; m5=ma(hist_c,5); m20=ma(hist_c,20)
            rs=calc_rsi(hist_c)
            rsi_s=100 if rs<=20 else 80 if rs<=30 else 65 if rs<=40 else 55 if rs<=50 else 45 if rs<=60 else 30 if rs<=70 else 15 if rs<=80 else 0
            ma_s=100 if cp>m5 and m5>m20 else 75 if cp>m5 else 60 if cp>m20 else 40
            avg_v=sum(hist_v[-21:])/20; vr=vols[i]/avg_v if avg_v>0 else 1
            pc=(closes[i]-closes[i-1])/closes[i-1]*100
            vol_s=100 if vr>2 and pc>0 else 70 if vr>1.5 and pc>0 else 0 if vr>2 and pc<0 else 30 if vr>1.5 and pc<0 else 50
            m60=ma(hist_c,min(50,len(hist_c)))
            trend_s=min(100,abs(m20-m60)/m60*500) if m60>0 else 50
            results.append({"fwd5":round(fwd5,2),"fwd10":round(fwd10,2),
                "rsi":rsi_s,"ma":ma_s,"vol":vol_s,"trend":trend_s})
    except: pass
    time.sleep(0.1)

n=len(results)
print(f"Observations: {n}\n")
factors=["rsi","ma","vol","trend"]; labels=["RSI","MA Trend","Volume","Trend Str"]

print("=" * 60)
print(f"Expanded Pool ({len(pool)} stocks) · Factor IC")
print("-" * 60)
print(f"{'Factor':<16} {'5d IC':>7} {'10d IC':>7}")
print("-" * 60)
for f,l in zip(factors,labels):
    xs=[r[f] for r in results]; y5=[r["fwd5"] for r in results]; y10=[r["fwd10"] for r in results]
    ic5=rank_ic(xs,y5); ic10=rank_ic(xs,y10)
    print(f"{l:<16} {ic5:+.3f}   {ic10:+.3f}")

# Top-3 composite
xs_top3=[]
for r in results:
    top3=(r["vol"]+r["ma"]+50)/3  # vol+ma+neutral
    xs_top3.append(top3)
ic_top3_5=rank_ic(xs_top3,[r["fwd5"] for r in results])
ic_top3_10=rank_ic(xs_top3,[r["fwd10"] for r in results])
print(f"\nTop3 Composite    {ic_top3_5:+.3f}   {ic_top3_10:+.3f}")

# Shuffle
ys=[r["fwd10"] for r in results]
real=abs(ic_top3_10); better=0; random.seed(42)
for _ in range(1000):
    random.shuffle(ys)
    if abs(rank_ic(xs_top3,ys))>real: better+=1
print(f"Shuffle: {better/10:.0f}% random > real [{'PASS' if better/10<50 else 'NOISE'}]")
