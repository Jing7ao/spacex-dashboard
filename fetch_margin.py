# fetch_margin.py — 融资融券（push2批量+单股降级，f139=余额 f140=净买）
import sys, io, json, os, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

CODES = ["300136","002149","601689","002050","603305","688017","300476","601138","300308","300394","002463","600183","300502","002837","002851","600584","688102","603601","605123","603308","300395","688333","002281","600487","600522","603606","002916","002156","300346","688268","600456","301522","300855","688629","300408","688300","688012","002371","300567","688981","600118","601100","600089","002281","000988","002036"]

results = {}
# Batch fetch: ulist.np with margin fields
batch_size = 30
for i in range(0, len(CODES), batch_size):
    batch = CODES[i:i+batch_size]
    secids = ",".join(f"{(1 if c.startswith(('6','5')) else 0)}.{c}" for c in batch)
    url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids={secids}&fields=f12,f14,f139,f140"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            for item in data.get("data", {}).get("diff", []):
                code = item.get("f12","")
                bal = item.get("f139", 0) or 0
                net = item.get("f140", 0) or 0
                if bal > 0:
                    results[code] = {"name": item.get("f14",""), "margin_bal": bal, "margin_net": net}
    except Exception as e:
        print(f"  batch error: {e}")
    time.sleep(0.3)

for code in results:
    d = results[code]
    net = d["margin_net"]
    print(f"  {code} {d['name']:<8} 余额{d['margin_bal']/1e8:.2f}亿 净{'买' if net>0 else '卖'} {abs(net)/1e8:.2f}亿")

net_buys = sum(1 for d in results.values() if d["margin_net"] > 0)
print(f"\n📊 融资净买入: {net_buys} 只 | 净卖出: {len(results)-net_buys} 只 | 共 {len(results)} 只有效")

with open(os.path.join(DIR, "margin_data.json"), "w", encoding="utf-8") as f:
    json.dump({"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "data": results}, f, ensure_ascii=False, indent=2)
print("✅ 已保存 margin_data.json")
