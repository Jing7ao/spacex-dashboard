# fetch_northbound.py — 北向资金（QFII）持股
import sys, io, json, os, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))
CODES = ["688017","688102","300476","300136","300308","300394","300502","002281","002149","601689","002050","603305","300395","688333","600456","603601","002036","300346","688268","688012","002371","002463","600487","600522","002916","002837","002851","600584","688629","688981","601138","002156","300750","601012","300274","600089","688126","300666","688019","300054","603650","300260","688146","300655","300408","688300","600118","601100","605123","603308","301522","300855","688631","000099"]

results = {}
batch_size = 8
for i in range(0, len(CODES), batch_size):
    batch = CODES[i:i+batch_size]
    secids = ",".join(f"{(1 if c.startswith(('6','5')) else 0)}.{c}" for c in batch)
    url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids={secids}&fields=f12,f14,f132,f133"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read())
            for item in data.get("data",{}).get("diff",[]):
                code = item.get("f12","")
                shares = item.get("f132",0) or 0
                mktval = item.get("f133",0) or 0
                if shares > 0:
                    results[code] = {"name":item.get("f14",""), "shares": shares, "mktval": mktval}
    except Exception as e:
        print(f"  batch error, retrying...")
    time.sleep(1.5)

print(f"🔍 北向资金持股 · {time.strftime('%Y-%m-%d')}")
print("=" * 55)
ranked = sorted(results.items(), key=lambda x: x[1]["mktval"], reverse=True)
for code, d in ranked[:20]:
    print(f"  {code} {d['name']:<8} 市值{d['mktval']:.1f}亿(估算)")
print(f"  ...")
print(f"\n📊 北向持有: {len(results)}/{len(CODES)} 只 | Top3: {', '.join(d['name'] for _,d in ranked[:3])}")

with open(os.path.join(DIR, "northbound_data.json"), "w", encoding="utf-8") as f:
    json.dump({"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "data": results}, f, ensure_ascii=False, indent=2)
print("✅ 已保存")
