import json, urllib.request, sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ECOS = {
    "马斯克生态": ["688102","002149","300136","600456","603601","301522","688333","605123","603308","300395","603212","002792","603305","002050","601689","002036","300855","301005"],
    "英伟达生态": ["300476","688300","300502","002837","002851","300308","300394","601138","600584","002156","002916","300408"],
    "国产AI算力": ["688629","603986","002371","688012","300567","002281","000938","300570","300620","600487"],
    "国产机器人": ["688017","603662","601100","603809","002050","601689"],
    "商业航天": ["600118","688070","600456","603601","688102","002149","301522","688333","605123","603308"],
    "低空经济": ["688631","000099"],
    "电力能源": ["603191","600362","603290","600869","603606","600089","601179","600312","600406","000400","002335","002364","002028","600875","601126","601877","002270"],
    "光通信": ["000988","301165","688498","601869","600487","000938","300570","300620","002281","600522","603606","688668"],
}

# Fetch all data once
all_data = {}
all_codes = set()
for codes in ECOS.values(): all_codes.update(codes)

for code in all_codes:
    m = "sh" if code.startswith(("6","5")) else "sz"
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,100,qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                      data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
        if not klines or len(klines) < 70: continue
        closes = [float(k[2]) for k in klines if len(k)>2]
        if len(closes) < 70: continue
        all_data[code] = {
            "r60": (closes[-1]-closes[-60])/closes[-60]*100,
            "r20": (closes[-1]-closes[-20])/closes[-20]*100,
            "r5":  (closes[-1]-closes[-5])/closes[-5]*100
        }
    except: pass

print(f"有效标的: {len(all_data)}/{len(all_codes)}\n")
print(f"{'生态':<14} {'n':>2} {'60日':>8} {'20日':>8} {'5日':>7}  {'赢率(60日)'}")
print("-" * 65)

eco_stats = []
for eco_name, codes in ECOS.items():
    valid = [all_data[c] for c in codes if c in all_data]
    if len(valid) < 2: continue
    n = len(valid)
    avg60 = sum(d["r60"] for d in valid)/n
    avg20 = sum(d["r20"] for d in valid)/n
    avg5  = sum(d["r5"] for d in valid)/n
    wr60 = sum(1 for d in valid if d["r60"]>0)/n*100
    print(f"{eco_name:<14} {n:>2} {avg60:>+7.1f}% {avg20:>+7.1f}% {avg5:>+6.1f}%  {wr60:.0f}%")
    eco_stats.append((eco_name, avg60, avg20, avg5, n, wr60))

eco_stats.sort(key=lambda x: x[1], reverse=True)

print()
print("=" * 55)
print("生态排名 (60日收益):")
print("-" * 55)
for i, (name, r60, r20, r5, n, wr) in enumerate(eco_stats):
    bar = "█" * max(1, int((r60 - eco_stats[-1][1]) / 3)) if len(eco_stats)>1 else "█"
    print(f"  {i+1}. {name:<14} {r60:>+6.1f}%  {wr:.0f}%赢  {bar}")

if len(eco_stats) >= 2:
    spread = eco_stats[0][1] - eco_stats[-1][1]
    print(f"\n  生态选择溢价: {spread:.1f}% (60日)")
    if spread > 15:
        print(f"  >> 选对生态的收益差异 >> 任何因子调权重能带来的改善")
        print(f"  >> 核心能力 = 判断哪个生态在上升周期")
