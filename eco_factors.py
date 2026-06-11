# eco_factors.py — 分生态因子IC分析（11个经典因子 + 8个生态）
import json, urllib.request, sys, io, math, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

ECOS = {
    "nvidia":{"name":"英伟达","codes":["300476","601138","300308","300394","002463","600183","300502","002837","002851","600584","002916","002156","688300"]},
    "musk":{"name":"马斯克","codes":["688102","002149","300136","600456","603601","301522","688333","605123","603308","300395","603305","601689","002050","688017","603662"]},
    "ai_domestic":{"name":"AI算力","codes":["688629","603986","002371","688012","300567","002281","000938","600487","002916","688981","688256"]},
    "optical":{"name":"光通信","codes":["300308","300394","300502","002281","000988","688498","600487","000938","301165"]},
    "robot_domestic":{"name":"机器人","codes":["688017","603662","601689","601100","300124","002050","300660"]},
    "semimat":{"name":"半导体材料","codes":["601208","688300","600183","688268","300346","688126","300666","688019","300054","603650","300260","002378"]},
    "cooling":{"name":"液冷","codes":["002837","301018","300499","300249","002126","688668"]},
    "power":{"name":"电力","codes":["600089","601179","601877","600875","600406","000400","002335","002364","002028","300274","601012","600487","600522"]},
}

all_codes = set()
for eco in ECOS.values(): all_codes.update(eco["codes"])
print(f"Stocks: {len(all_codes)}")

def ma(cl,n): return sum(cl[-n:])/n if len(cl)>=n else sum(cl)/len(cl)
def rank_ic(xs,ys):
    n=len(xs); rx=sorted(range(n),key=lambda j:xs[j]); ry=sorted(range(n),key=lambda j:ys[j])
    rkx=[0]*n; rky=[0]*n
    for j,idx in enumerate(rx): rkx[idx]=j
    for j,idx in enumerate(ry): rky[idx]=j
    d2=sum((rkx[j]-rky[j])**2 for j in range(n))
    return 1-6*d2/(n*(n*n-1))

stock_data = {}
for code in all_codes:
    m="sh" if code.startswith(("6","5")) else "sz"
    try:
        url=f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,120,qfq"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=5) as resp:
            data=json.loads(resp.read())
            klines=(data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                    data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines)<70: continue
            closes=[float(k[2]) for k in klines if len(k)>2]
            vols=[float(k[5]) for k in klines if len(k)>5]
            opens=[float(k[1]) for k in klines if len(k)>1]
            highs=[float(k[3]) for k in klines if len(k)>3]
            lows=[float(k[4]) for k in klines if len(k)>4]
            if len(closes)<70: continue
        stock_data[code]={"c":closes,"v":vols,"o":opens,"h":highs,"l":lows}
    except: pass
    time.sleep(0.1)

print(f"Valid: {len(stock_data)}")

# ── 因子计算（11个经典因子）──
def compute_factors(closes, vols, opens, highs, lows, idx):
    """At index idx, compute all 11 factors"""
    hist_c = closes[idx-50:idx+1]; hist_v = vols[idx-50:idx+1]
    cp=closes[idx]; pp=closes[idx-1]
    avg_v=sum(hist_v[-21:])/20; vr=vols[idx]/avg_v if avg_v>0 else 1
    pc=(cp-pp)/pp*100
    m5=ma(hist_c,5); m20=ma(hist_c,20); m10=ma(hist_c,10)

    f = {}
    # 1. RSI
    g=[max(hist_c[i]-hist_c[i-1],0) for i in range(1,len(hist_c))]
    l=[max(hist_c[i-1]-hist_c[i],0) for i in range(1,len(hist_c))]
    ag=sum(g[-14:])/14; al=sum(l[-14:])/14
    rs=100-100/(1+ag/al) if al>0 else 50
    f["rsi"]=100 if rs<=20 else 80 if rs<=30 else 65 if rs<=40 else 55 if rs<=50 else 45 if rs<=60 else 30 if rs<=70 else 15 if rs<=80 else 0
    # 2. MA Trend
    f["ma"]=100 if cp>m5 and m5>m20 else 75 if cp>m5 else 60 if cp>m20 else 40
    # 3. Volume ratio
    f["vol"]=100 if vr>2 and pc>0 else 70 if vr>1.5 and pc>0 else 0 if vr>2 and pc<0 else 30 if vr>1.5 and pc<0 else 50
    # 4. Momentum (5d return)
    ret5=(closes[idx]-closes[idx-5])/closes[idx-5]*100 if idx>=5 else 0
    f["mom5"]=80 if ret5>5 else 65 if ret5>2 else 35 if ret5<-5 else 20 if ret5<-2 else 50
    # 5. Reversal (-mom5)
    f["rev5"]=100-f["mom5"]
    # 6. Turnover volatility (amt stability)
    amts=[hist_v[j]*hist_c[j]/10000 for j in range(max(0,len(hist_v)-30),len(hist_v))]
    amt_avg=sum(amts)/len(amts) if amts else 1
    amt_std=math.sqrt(sum((a-amt_avg)**2 for a in amts)/len(amts)) if amts else 0
    f["amt_stab"]=100*max(0,min(1,1-amt_std/amt_avg)) if amt_avg>0 else 50
    # 7. Gap up (连续跳空, Alpha 015 simplified)
    gap_sum=0; valid_gaps=0
    for gi in range(idx-2,idx+1):
        if gi>0 and opens[gi]>0 and closes[gi-1]>0:
            gap_sum+=(opens[gi]-closes[gi-1])/closes[gi-1]*100
            valid_gaps+=1
    f["gap"]=80 if gap_sum>3 else 60 if gap_sum>1 else 20 if gap_sum<-3 else 40 if gap_sum<-1 else 50
    # 8. CLV (close location value, Alpha 002 K-line pattern)
    clv_vals=[]
    for ci in range(idx-4,idx+1):
        if ci>0 and highs[ci]>lows[ci]:
            clv_vals.append((closes[ci]-lows[ci])-(highs[ci]-closes[ci])/(highs[ci]-lows[ci]))
    clv_delta=sum(clv_vals)/len(clv_vals) if clv_vals else 0
    f["clv"]=80 if clv_delta>0.3 else 60 if clv_delta>0 else 20 if clv_delta<-0.3 else 40
    # 9. VWAP deviation (Alpha 120)
    vwap=sum(hist_v[j]*hist_c[j] for j in range(len(hist_v)))/sum(hist_v) if sum(hist_v)>0 else cp
    vwap_dev=(vwap-cp)/cp*100
    f["vwap"]=80 if vwap_dev>2 else 60 if vwap_dev>0 else 20 if vwap_dev<-2 else 40
    # 10. Shadow line ratio (Alpha 171 影线)
    body=abs(cp-opens[idx]); upper_shadow=highs[idx]-max(cp,opens[idx]); lower_shadow=min(cp,opens[idx])-lows[idx]
    total_range=highs[idx]-lows[idx]
    shadow_ratio=(upper_shadow+lower_shadow)/total_range if total_range>0 else 0
    f["shadow"]=80 if shadow_ratio>0.6 and pc<0 else 60 if shadow_ratio>0.4 else 40 if shadow_ratio<0.2 else 50
    # 11. Volume-price divergence (42号)
    vp_corr=0
    if idx>=10:
        daily_highs=[highs[j] for j in range(idx-9,idx+1)]
        daily_vols=[vols[j] for j in range(idx-9,idx+1)]
        n2=len(daily_highs); ax=sum(daily_highs)/n2; ay=sum(daily_vols)/n2
        cov=sum((daily_highs[i]-ax)*(daily_vols[i]-ay) for i in range(n2))
        sx=math.sqrt(sum((h-ax)**2 for h in daily_highs))
        sy=math.sqrt(sum((v-ay)**2 for v in daily_vols))
        vp_corr=cov/(sx*sy) if sx>0 and sy>0 else 0
    f["vp_div"]=80 if vp_corr<-0.3 else 60 if vp_corr<0 else 40 if vp_corr>0.3 else 50
    # 12. 换手率变化 (volume as turnover proxy, shares outstanding ≈ constant)
    vol_ma5=sum(hist_v[-5:])/5 if len(hist_v)>=5 else avg_v
    vol_ma20=sum(hist_v[-20:])/20 if len(hist_v)>=20 else avg_v
    turn_chg=(vol_ma5-vol_ma20)/vol_ma20 if vol_ma20>0 else 0
    f["turn_chg"]=80 if turn_chg>0.5 else 60 if turn_chg>0.2 else 20 if turn_chg<-0.3 else 40 if turn_chg<-0.1 else 50
    # 13. 日内振幅
    amp=(highs[idx]-lows[idx])/closes[idx-1]*100 if idx>0 and closes[idx-1]>0 else 0
    f["amplitude"]=80 if amp<3 and pc>0 else 60 if amp<5 and pc>0 else 40 if amp>8 else 50
    # 14. 量价相关性 (5日)
    if idx>=5:
        rets=[(closes[j]-closes[j-1])/closes[j-1] for j in range(idx-4,idx+1)]
        vcs=[(vols[j]-vols[j-1])/vols[j-1] if vols[j-1]>0 else 0 for j in range(idx-4,idx+1)]
        ar2=sum(rets)/5; av2=sum(vcs)/5
        cov3=sum((rets[i]-ar2)*(vcs[i]-av2) for i in range(5))
        sr2=math.sqrt(sum((r-ar2)**2 for r in rets))
        sv2=math.sqrt(sum((v-av2)**2 for v in vcs))
        pv_corr_val=cov3/(sr2*sv2) if sr2>0 and sv2>0 else 0
    else: pv_corr_val=0
    f["pv_corr"]=80 if pv_corr_val>0.5 else 60 if pv_corr_val>0 else 40 if pv_corr_val<-0.5 else 50
    # 15. 放量下跌反转 (Alpha#12: sign(Δvol)×(-Δprice), 正值=恐慌出清→买)
    if idx>0 and vols[idx-1]>0 and closes[idx-1]>0:
        vol_delta=(vols[idx]-vols[idx-1])/vols[idx-1]
        price_delta=(closes[idx]-closes[idx-1])/closes[idx-1]
        vpr=(1 if vol_delta>0 else -1)*(-price_delta)
    else: vpr=0
    f["vol_price_rev"]=80 if vpr>0.03 else 60 if vpr>0.01 else 20 if vpr<-0.03 else 40 if vpr<-0.01 else 50
    # 16. 跌速放缓 (Alpha#49: 近期跌速 vs 早期跌速, 跌速放缓=触底)
    if idx>=20 and closes[idx-20]>0 and closes[idx-10]>0:
        early_chg=(closes[idx-10]-closes[idx-20])/closes[idx-20]
        recent_chg=(closes[idx]-closes[idx-10])/closes[idx-10]
        decl_delta=recent_chg-early_chg
    else: decl_delta=0
    f["decl_slow"]=80 if decl_delta>0.05 else 60 if decl_delta>0.02 else 20 if decl_delta<-0.05 else 40 if decl_delta<-0.02 else 50
    # 17. 开盘吸筹 (Alpha#6: -corr(open, vol, 10), 负相关=低开放量吸筹)
    if idx>=10:
        o10=opens[idx-9:idx+1]; v10=vols[idx-9:idx+1]
        n6=len(o10); ao2=sum(o10)/n6; av3=sum(v10)/n6
        cov5=sum((o10[i]-ao2)*(v10[i]-av3) for i in range(n6))
        so2=math.sqrt(sum((o-ao2)**2 for o in o10))
        sv3=math.sqrt(sum((v-av3)**2 for v in v10))
        oa_corr=cov5/(so2*sv3) if so2>0 and sv3>0 else 0
    else: oa_corr=0
    f["open_accum"]=80 if oa_corr<-0.3 else 60 if oa_corr<0 else 40 if oa_corr>0.3 else 50
    # 18. VWAP乖离标准化 (Z-score of VWAP deviation)
    vwap_devs=[]
    for j in range(max(20,idx-19),idx+1):
        hv_j=vols[j-20:j+1]; hc_j=closes[j-20:j+1]
        vw_j=sum(hv_j[k]*hc_j[k] for k in range(len(hv_j)))/sum(hv_j) if sum(hv_j)>0 else closes[j]
        if closes[j]>0: vwap_devs.append((vw_j-closes[j])/closes[j]*100)
    if len(vwap_devs)>=5:
        vwap_mu=sum(vwap_devs)/len(vwap_devs)
        vwap_sd=math.sqrt(sum((d-vwap_mu)**2 for d in vwap_devs)/len(vwap_devs))
        vwz=(vwap_devs[-1]-vwap_mu)/vwap_sd if vwap_sd>0 else 0
    else: vwz=0
    f["vwap_z"]=80 if vwz>1 else 60 if vwz>0 else 20 if vwz<-1 else 40 if vwz<0 else 50

    return f

# ── Per-ecosystem IC ──
factor_names={
    "rsi":"RSI","ma":"均线","vol":"成交量","mom5":"5日动量","rev5":"5日反转",
    "amt_stab":"成交额稳定","gap":"跳空","clv":"K线形态","vwap":"VWAP偏离","shadow":"影线","vp_div":"量价背离",
    "turn_chg":"换手率变化","amplitude":"日内振幅","pv_corr":"量价相关性",
    "vol_price_rev":"放量下跌反转","decl_slow":"跌速放缓","open_accum":"开盘吸筹","vwap_z":"VWAP乖离Z"
}

eco_results = {}
for eco_key, eco in ECOS.items():
    results = []
    for code in eco["codes"]:
        if code not in stock_data: continue
        sd = stock_data[code]
        closes=sd["c"]; vols=sd["v"]; opens=sd["o"]; highs=sd["h"]; lows=sd["l"]
        for i in range(55, len(closes)-15, 5):
            f = compute_factors(closes, vols, opens, highs, lows, i)
            f["fwd10"] = round((closes[i+10]-closes[i])/closes[i]*100, 2)
            results.append(f)
    if len(results) < 20: continue

    ics = {}
    for fkey,fname in factor_names.items():
        xs=[r[fkey] for r in results]; ys=[r["fwd10"] for r in results]
        ics[fkey] = rank_ic(xs,ys)
    ranked = sorted(ics.items(), key=lambda x: abs(x[1]), reverse=True)
    eco_results[eco_key] = {
        "name": eco["name"], "n": len([c for c in eco["codes"] if c in stock_data]),
        "obs": len(results),
        "top_factors": [(f, round(ic,3), factor_names[f], ic<0) for f, ic in ranked[:3]]
    }

print(f"\n{'='*75}")
print(f"{'Ecosystem':<12} {'N':>3} {'Obs':>5} {'Factor 1':>22} {'Factor 2':>22} {'Factor 3':>22}")
print(f"{'-'*75}")
for eco_key in ["nvidia","musk","optical","ai_domestic","semimat","robot_domestic","cooling","power"]:
    if eco_key not in eco_results: continue
    r = eco_results[eco_key]
    def fmt_f(fi):
        fname, ic, label, rev = fi
        icon = "🔄" if rev else "→"
        return f"{icon}{label} {ic:+.3f}"
    print(f"{r['name']:<12} {r['n']:>3} {r['obs']:>5} {fmt_f(r['top_factors'][0]):>22} {fmt_f(r['top_factors'][1]):>22} {fmt_f(r['top_factors'][2]):>22}")

with open(os.path.join(DIR, "eco_factors.json"), "w", encoding="utf-8") as f:
    json.dump(eco_results, f, ensure_ascii=False, indent=2)
print(f"\n✅ Saved eco_factors.json")
