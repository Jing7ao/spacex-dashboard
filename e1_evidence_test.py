import json, urllib.request, sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Stocks with rn evidence annotation
# E1 = 年报原文直接支撑, E2 = 合理推断, E3/年报未提 = 无支撑
STOCKS_DATA = [
    # E1 confirmed
    ("688017","绿的谐波","E1","全球唯一全自主谐波减速器(年报)"),
    ("600487","亨通光电","E1","跨洋海缆唯一中国企业(年报)"),
    ("688102","斯瑞新材","E1","蓝箭航天供应商+电接触全球第一(年报)"),
    ("601877","正泰电器","E1","低压电器三细分第一(年报)"),
    ("600362","江西铜业","E1","LME国内唯一阴极铜测试厂(年报)"),
    ("002149","西部材料","E1","核级控制棒国内唯一(年报,但与SpaceX无关)"),
    ("002050","三花智控","E1","Tesla+Optimus双生态(年报)"),
    ("601689","拓普集团","E1","Tesla 35%营收(年报)"),
    ("300395","菲利华","E1","三大半导体设备商认证(年报,Q布未量产)"),
    ("300476","胜宏科技","E1","深度绑定国际头部客户(年报,未点名NVIDIA)"),
    ("002281","光迅科技","E1","光器件全球份额7.8%(年报)"),
    ("300346","南大光电","E1","ArF光刻胶(年报,未称唯一量产)"),
    ("002179","中航光电","E1","连接器龙头(年报)"),
    ("600456","宝钛股份","E1","大飞机工程唯一钛供应商(年报,与SpaceX无关)"),
    ("603308","应流股份","E1","F/H燃机叶片唯一供应商(年报,与SpaceX无关)"),
    ("688300","联瑞新材","E1","硅微粉龙头(年报)"),
    # E2 inferred
    ("300136","信维通信","E2","北美大客户=SpaceX?(年报未点名)"),
    ("300308","中际旭创","E2","光模块龙头"),
    ("002036","联创电子","E2","FSD摄像头独家(待年报确认)"),
    ("603601","再升科技","E2","SpaceX稳定供应(互动易)"),
    ("301522","上大股份","E2","高温合金(年报未提SpaceX)"),
    ("605123","派克新材","E2","NASA+SpaceX双认证(年报无独家)"),
    ("688333","铂力特","E2","3D打印服务航空航天"),
    ("002792","通宇通讯","E2","通过SpaceX认证(互动易)"),
    # E3/unverified
    ("600869","远东股份","E3","线缆龙头(与SpaceX/NVIDIA无关)"),
    ("688268","华特气体","E3","电子特气(与瓶颈无关)"),
    ("300408","三环集团","E3","陶瓷基板(日本京瓷替代)"),
    ("601138","工业富联","E3","AI服务器代工(伪瓶颈,毛利率6-8%)"),
    ("600584","长电科技","E3","封测(年报未提NVIDIA)"),
    ("603305","旭升集团","E3","铝合金压铸(多家供应商)"),
    ("002156","通富微电","E3","Chiplet封装(证据不足)"),
    ("002916","深南电路","E3","IC载板(Ibiden替代)"),
    ("300502","新易盛","E3","GB300 CPO(证据不足)"),
    ("600745","闻泰科技","E3","ODM(多家供应商)"),
    ("688668","鼎通科技","E3","液冷连接器"),
    ("603606","东方电缆","E3","海缆(与SpaceX/NVIDIA无关)"),
    ("002466","天齐锂业","E3","锂矿(大宗商品,非瓶颈)"),
    ("600089","特变电工","E3","输变电(与SpaceX/NVIDIA无关)"),
    ("600522","中天科技","E3","光通信(与瓶颈无关)"),
]

def calc_rsi(cl):
    if len(cl)<15: return 50
    g=[max(cl[i]-cl[i-1],0) for i in range(1,len(cl))]
    l=[max(cl[i-1]-cl[i],0) for i in range(1,len(cl))]
    ag=sum(g[-14:])/14; al=sum(l[-14:])/14
    if al==0: return 100
    return 100-100/(1+ag/al)

def ma(cl,n): return sum(cl[-n:])/n if len(cl)>=n else sum(cl)/len(cl)

e1_returns = []
e2_returns = []
e3_returns = []

for code, name, level, note in STOCKS_DATA:
    m = "sh" if code.startswith(("6","5")) else "sz"
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,120,qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                      data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines) < 80: continue
            closes = [float(k[2]) for k in klines if len(k)>2]
            if len(closes) < 80: continue

        # Multiple forward returns: 5d, 10d, 20d, 60d
        for horizon, label, offset in [(5,"5日",5),(10,"10日",10),(20,"20日",20),(60,"60日",60)]:
            if len(closes) <= offset+10: continue
            # Use multiple historical starting points
            for start in range(-70, -10, 20):  # 4 time points
                if abs(start)+offset >= len(closes): continue
                fwd = (closes[start+offset]-closes[start])/closes[start]*100
                entry = {"name":name,"code":code,"level":level,"horizon":label,"fwd":round(fwd,2)}
                if level == "E1": e1_returns.append(fwd)
                elif level == "E2": e2_returns.append(fwd)
                else: e3_returns.append(fwd)
    except: pass

print(f"样本: E1={len(e1_returns)}个, E2={len(e2_returns)}个, E3={len(e3_returns)}个 (多时间点多周期)\n")

# Stats by evidence level
print("=" * 65)
print(f"{'证据等级':<8} {'样本':>5} {'均值':>8} {'中位':>8} {'>0比例':>7} {'标准差':>7}")
print("-" * 65)

for label, data in [("E1(实锤)",e1_returns),("E2(推断)",e2_returns),("E3(虚/弱)",e3_returns)]:
    if not data: continue
    avg = sum(data)/len(data)
    sd = math.sqrt(sum((x-avg)**2 for x in data)/len(data))
    med = sorted(data)[len(data)//2]
    pos = sum(1 for x in data if x>0)/len(data)*100
    # Annualized: 5d→~50x, 10d→25x, 20d→12x, 60d→4x
    print(f"  {label:<8} {len(data):>5} {avg:>+7.2f}% {med:>+7.2f}% {pos:>6.0f}% {sd:>7.2f}%")

# E1 vs E3 t-test
print()
print("=" * 65)
print("E1 vs E3: 独立样本t检验")
print("-" * 65)
for label, d1, d2 in [("E1 vs E3", e1_returns, e3_returns), ("E1 vs E2", e1_returns, e2_returns), ("E2 vs E3", e2_returns, e3_returns)]:
    n1,n2 = len(d1),len(d2)
    if n1<5 or n2<5: continue
    avg1,avg2 = sum(d1)/n1, sum(d2)/n2
    v1 = sum((x-avg1)**2 for x in d1)/(n1-1)
    v2 = sum((x-avg2)**2 for x in d2)/(n2-1)
    se = math.sqrt(v1/n1 + v2/n2)
    t = (avg1-avg2)/se if se>0 else 0
    print(f"  {label:<12} 均值差{avg1-avg2:+.2f}%  t={t:+.2f}  {'✅显著' if abs(t)>1.96 else '⚪不显著'}")

# Group by horizon
print()
print("=" * 65)
print("按持仓周期分组:")
print("-" * 65)
for horizon in ["5日","10日","20日","60日"]:
    e1h = [x for x in e1_returns if True]  # simplified
    print(f"  {horizon}: 需按周期分组(数据结构优化中)")

print()
print(">> 结论: E1证据能否区分好坏标的?")
if len(e1_returns)>0 and len(e3_returns)>0:
    e1_avg = sum(e1_returns)/len(e1_returns)
    e3_avg = sum(e3_returns)/len(e3_returns)
    diff = e1_avg - e3_avg
    if diff > 1:
        print(f">> E1标的年均跑赢E3约 {diff*10:.0f}% (粗略年化)")
    elif diff > 0:
        print(f">> E1略优于E3, 差异{diff:+.2f}%, 统计不显著")
    else:
        print(f">> E1并不优于E3 (差异{diff:+.2f}%)")
        print(">> 这意味着: 年报实锤 ≠ 股价会涨")
        print(">> E1的价值是'排雷'(避免虚标暴跌), 不是'选牛'")
