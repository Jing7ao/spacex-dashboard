# factor_optimize.py — 因子组合优化: 砍弱因子+拉长窗口+生态加成
import json, urllib.request, sys, io, math, time, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

STOCKS = {"603305":"旭升","300136":"信维","002281":"光迅","600522":"中天","600089":"特变","688333":"铂力特","300346":"南大","600869":"远东","300408":"三环","300395":"菲利华","688017":"绿的","688102":"斯瑞","300476":"胜宏","600584":"长电","002149":"西部","600487":"亨通","601689":"拓普","688012":"中微","002050":"三花","601138":"工业富联","002837":"英维克","688300":"联瑞","601208":"东材","600183":"生益","300308":"中际","300394":"天孚","300502":"新易盛","002916":"深南","600456":"宝钛","688268":"华特","688126":"沪硅","300666":"江丰"}

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

# Top-3 eco classification (simplified: based on recent 20d return)
def classify_eco(code, closes_20d):
    chg20 = (closes_20d[-1]-closes_20d[0])/closes_20d[0]*100
    if chg20 > 3: return "top3"
    if chg20 < -3: return "bottom3"
    return "mid"

print("Pulling data...")
results = []
for code, name in STOCKS.items():
    m="sh" if code.startswith(("6","5")) else "sz"
    try:
        url=f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,150,qfq"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=5) as resp:
            data=json.loads(resp.read())
            klines=(data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                    data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines)<80: continue
            closes=[float(k[2]) for k in klines if len(k)>2]
            vols=[float(k[5]) for k in klines if len(k)>5]
            if len(closes)<80: continue

        for i in range(60,len(closes)-25,5):
            hist_c=closes[i-60:i]; hist_v=vols[i-60:i]
            fwd10=(closes[i+10]-closes[i])/closes[i]*100
            cp=closes[i]; m5=ma(hist_c,5); m20=ma(hist_c,20)
            # Top-3 factors only
            volScore=vols[i]/sum(hist_v[-21:])*20; pc=(closes[i]-closes[i-1])/closes[i-1]*100
            vol_f=100 if volScore>2 and pc>0 else 70 if volScore>1.5 and pc>0 else 30 if volScore>2 and pc<0 else 50
            ma_f=100 if cp>m5 and m5>m20 else 75 if cp>m5 else 60 if cp>m20 else 40
            amts=[vols[j]*closes[j]/10000 for j in range(max(0,i-30),i)]
            amt_avg=sum(amts)/len(amts) if amts else 1
            amt_std=math.sqrt(sum((a-amt_avg)**2 for a in amts)/len(amts)) if amts else 0
            amt_f=100*max(0,min(1,1-amt_std/amt_avg)) if amt_avg>0 else 50
            # 8-factor (existing)
            rs=calc_rsi(hist_c)
            all_f=[100 if rs<=20 else 80 if rs<=30 else 65 if rs<=40 else 55 if rs<=50 else 45 if rs<=60 else 30 if rs<=70 else 15 if rs<=80 else 0,
                   ma_f, vol_f,
                   80 if (cp-m20)/(2*ma(hist_c,20)*0.05+0.01)<0.15 else 50,
                   50, 50, 50, amt_f]
            # Eco boost
            eco=classify_eco(code, hist_c[-20:])
            results.append({"name":name,"fwd10":round(fwd10,2),
                "top3_score":(vol_f+ma_f+amt_f)/3,
                "all8_score":sum(all_f)/8,
                "top3_eco":(vol_f+ma_f+amt_f)/3+(2 if eco=="top3" else -2 if eco=="bottom3" else 0),
                "eco":eco})
    except: pass
    time.sleep(0.15)

n=len(results)
print(f"Sample: {n}\n")

def test_score(label, score_key):
    xs=[r[score_key] for r in results]
    ys=[r["fwd10"] for r in results]
    ic=rank_ic(xs,ys)
    # Top vs bottom decile
    idx=sorted(range(n),key=lambda j:xs[j])
    top_n=n//4; bot_n=n//4
    top_fwd=sum(ys[idx[-top_n+i]] for i in range(top_n))/top_n
    bot_fwd=sum(ys[idx[i]] for i in range(bot_n))/bot_n
    print(f"  {label}: IC={ic:+.3f}  高分组{top_fwd:+.2f}% vs 低分组{bot_fwd:+.2f}%  差值{top_fwd-bot_fwd:+.2f}%")

print("=" * 60)
print("10日预测窗口 · 因子组合对比")
print("-" * 60)
test_score("Top3因子(Vol+MA+Amt)", "top3_score")
test_score("Top3+生态加成", "top3_eco")
test_score("全部8因子等权", "all8_score")

# Shuffle test for best combo
print(f"\nTop3+生态 打乱测试:")
xs=[r["top3_eco"] for r in results]; ys=[r["fwd10"] for r in results]
real_ic=abs(rank_ic(xs,ys)); better=0
random.seed(42)
for _ in range(1000):
    random.shuffle(ys)
    if abs(rank_ic(xs,ys))>real_ic: better+=1
pct=better/10
print(f"  real|IC|={real_ic:.3f}, {pct:.0f}% random > real [{('PASS' if pct<50 else 'NOISE')}]")
