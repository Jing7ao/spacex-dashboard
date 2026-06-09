import json, urllib.request, sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

STOCKS = {
    "603305":"旭升集团","002466":"天齐锂业","300136":"信维通信","002281":"光迅科技",
    "600522":"中天科技","600089":"特变电工","688333":"铂力特","300346":"南大光电",
    "600869":"远东股份","300408":"三环集团","688268":"华特气体","300395":"菲利华",
    "688017":"绿的谐波","688102":"斯瑞新材","300476":"胜宏科技","600584":"长电科技",
    "002149":"西部材料","600487":"亨通光电","600456":"宝钛股份","688300":"联瑞新材",
    "605589":"圣泉集团","300567":"精测电子","603601":"再升科技","688629":"华丰科技",
    "601689":"拓普集团","300308":"中际旭创","688012":"中微公司","002371":"北方华创",
    "002050":"三花智控","601138":"工业富联","002156":"通富微电","002916":"深南电路",
    "300502":"新易盛","603606":"东方电缆","688668":"鼎通科技","603308":"应流股份",
    "301522":"上大股份","605123":"派克新材","600118":"中国卫星"
}

def calc_rsi(closes):
    if len(closes) < 15: return 50
    gains = [max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    losses = [max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    avg_gain = sum(gains[-14:])/14; avg_loss = sum(losses[-14:])/14
    if avg_loss == 0: return 100
    return 100 - 100/(1+avg_gain/avg_loss)

def calc_ma(cl, n):
    if len(cl) < n: return sum(cl)/len(cl)
    return sum(cl[-n:])/n

results = []
for code, name in STOCKS.items():
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

        # Factors: computed on day -6 (5 trading days ago)
        # Forward return: from day -6 to today
        hist_cl = closes[-65:-6]
        fwd_ret = (closes[-1] - closes[-6]) / closes[-6] * 100

        cp = closes[-6]; m5_val = calc_ma(hist_cl, 5); m20_val = calc_ma(hist_cl, 20)
        rs = calc_rsi(hist_cl)

        rsi_sc = 100 if rs<=20 else 80 if rs<=30 else 65 if rs<=40 else 55 if rs<=50 else 45 if rs<=60 else 30 if rs<=70 else 15 if rs<=80 else 0
        ma_sc = 100 if cp>m5_val and m5_val>m20_val else 75 if cp>m5_val else 60 if cp>m20_val else 40

        avg_v = sum(vols[-26:-7])/20 if len(vols)>26 else sum(vols[:-1])/max(len(vols)-1,1)
        vr = vols[-7]/avg_v if avg_v>0 else 1
        pc = (closes[-6]-closes[-7])/closes[-7]*100 if len(closes)>6 else 0
        vol_sc = 100 if vr>2 and pc>0 else 70 if vr>1.5 and pc>0 else 0 if vr>2 and pc<0 else 30 if vr>1.5 and pc<0 else 50

        bb_sum = sum((hist_cl[-i-1]-m20_val)**2 for i in range(min(20,len(hist_cl))))
        sd = math.sqrt(bb_sum/min(20,len(hist_cl)))
        bu = m20_val+2*sd; bl = m20_val-2*sd
        bp = (cp-bl)/(bu-bl) if bu>bl else 0.5
        bb_sc = 80 if bp<0.15 else 65 if bp<0.3 else 20 if bp>0.85 else 35 if bp>0.7 else 50

        chg_pct = (closes[-6]-closes[-7])/closes[-7]*100
        vp_sc = 100 if (chg_pct>0 and vr<0.8) else 20 if (chg_pct>2 and vr>1.5) else 80 if (chg_pct>0 and vr<1.2) else 50

        fund_sc = 50
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
                    fund_sc = 100 if fp>0.001 else 80 if fp>0.0005 else 65 if fp>0 else 35 if fp>-0.0005 else 20 if fp>-0.001 else 0
        except: pass

        m60_val = calc_ma(hist_cl, min(60,len(hist_cl)))
        trend_sc = min(100, abs(m20_val-m60_val)/m60_val*500) if m60_val>0 else 50

        results.append({"name":name,"fwd_ret":round(fwd_ret,2),
            "rsi":rsi_sc,"ma":ma_sc,"vol":vol_sc,"bb":bb_sc,"fund":fund_sc,"vp":vp_sc,"trend":trend_sc})
    except: pass

n = len(results)
print(f"样本: {n} 只 | 因子=5天前 | 收益=最近5天\n")

factors = ["rsi","ma","vol","bb","fund","vp","trend"]
labels = ["RSI","均线","成交量","布林带","资金流","量价健康","趋势强度"]

# Univariate
print("=" * 60)
print("单因子 vs 5日收益:")
print("-" * 60)
for i,(f,l) in enumerate(zip(factors,labels)):
    xs = [r[f] for r in results]; ys = [r["fwd_ret"] for r in results]
    avg_x=sum(xs)/n; avg_y=sum(ys)/n
    cov=sum((xs[j]-avg_x)*(ys[j]-avg_y) for j in range(n))
    sx=math.sqrt(sum((x-avg_x)**2 for x in xs)); sy=math.sqrt(sum((v-avg_y)**2 for v in ys))
    r_val=cov/(sx*sy) if sx>0 and sy>0 else 0
    # IC
    rx=sorted(range(n),key=lambda j:xs[j]); ry=sorted(range(n),key=lambda j:ys[j])
    rkx=[0]*n; rky=[0]*n
    for j,idx in enumerate(rx): rkx[idx]=j
    for j,idx in enumerate(ry): rky[idx]=j
    d2=sum((rkx[j]-rky[j])**2 for j in range(n))
    ic=1-6*d2/(n*(n*n-1))
    d="POS" if r_val>0.05 else "NEG" if r_val<-0.05 else "~0"
    print(f"  {l:<8} r={r_val:+.3f} IC={ic:+.3f} ({d})")

# OLS
print()
print("=" * 60)
print("OLS 多元回归权重:")
print("-" * 60)
X=[[r[f] for f in factors] for r in results]
y=[r["fwd_ret"] for r in results]
XTX=[[sum(X[k][i]*X[k][j] for k in range(n)) for j in range(len(factors))] for i in range(len(factors))]
XTy=[sum(X[k][i]*y[k] for k in range(n)) for i in range(len(factors))]

def solve(A,b):
    n2=len(A); M=[A[i][:]+[b[i]] for i in range(n2)]
    for col in range(n2):
        pv=max(range(col,n2),key=lambda r:abs(M[r][col]))
        if abs(M[pv][col])<1e-10: continue
        M[col],M[pv]=M[pv],M[col]
        for row in range(n2):
            if row==col: continue
            f2=M[row][col]/M[col][col]
            for j in range(n2+1): M[row][j]-=f2*M[col][j]
    return [M[i][n2]/M[i][i] if abs(M[i][i])>1e-10 else 0 for i in range(n2)]

w=solve(XTX,XTy)
ta=sum(abs(x) for x in w)
nw=[x/ta*100 for x in w] if ta>0 else w

yp=[sum(w[j]*X[i][j] for j in range(len(factors))) for i in range(n)]
ssr=sum((y[i]-yp[i])**2 for i in range(n))
sst=sum((v-sum(y)/n)**2 for v in y)
r2=1-ssr/sst if sst>0 else 0

for i,(l,wt) in enumerate(zip(labels,w)):
    bar="█"*max(1,int(abs(nw[i])/2))
    print(f"  {l:<8} {wt:+.4f} ({nw[i]:+5.1f}%) {bar}")

print(f"\n  R^2 = {r2:.3f} ({r2*100:.0f}% 方差被7因子解释)")

# Current vs OLS
print()
print("=" * 60)
print("当前手拍权重 vs OLS最优:")
print("-" * 60)
cw={"rsi":.22,"ma":.25,"vol":.15,"bb":.15,"fund":.15,"vp":0,"trend":.08}
for i,(l,f) in enumerate(zip(labels,factors)):
    cur=cw.get(f,0); opt=nw[i]/100; d=opt-cur
    ic2="!!" if abs(d)>.05 else "OK"
    print(f"  {l:<8} {cur:.0%} -> {opt:.0%} ({d:+.0%}) {ic2}")

# Cross validation: hold out 30%
import random
random.seed(42)
idx=list(range(n)); random.shuffle(idx)
split=int(n*0.7)
train=idx[:split]; test=idx[split:]

# Train on 70%
XTX2=[[sum(X[k][i]*X[k][j] for k in train) for j in range(len(factors))] for i in range(len(factors))]
XTy2=[sum(X[k][i]*y[k] for k in train) for i in range(len(factors))]
w2=solve(XTX2,XTy2)

# Predict on test 30%
yp2=[sum(w2[j]*X[i][j] for j in range(len(factors))) for i in test]
ya=[y[i] for i in test]
avg_p=sum(yp2)/len(yp2); avg_a=sum(ya)/len(ya)
cov2=sum((yp2[i]-avg_p)*(ya[i]-avg_a) for i in range(len(test)))
sp=math.sqrt(sum((p-avg_p)**2 for p in yp2))
sa=math.sqrt(sum((a-avg_a)**2 for a in ya))
r_test=cov2/(sp*sa) if sp>0 and sa>0 else 0

print(f"\n  样本外30%验证: r_pred_vs_actual = {r_test:+.3f}")
print(f"  (r>0=正向预测力, r<0=反向, r~0=无效)")
if r2>0.1 and r_test>0:
    print(f"\n  >> 模型有预测力但很弱。当前手拍权重和OLS方向一致则不改。")
elif r_test<0:
    print(f"\n  >> 样本外反向预测！当前因子组合不能预测5日收益。")
    print(f"  >> 这验证了此前的发现: 评分不预测收益(r=-0.22)")
