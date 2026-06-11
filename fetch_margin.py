# fetch_margin.py — 融资融券数据（AKShare，API已恢复！）
import sys, io, json, os, time, akshare as ak
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

CODES = ["688017","688102","300476","300136","300308","300394","300502","002281","002149","601689","002050","603305","300395","688333","600456","603601","002036","300346","688268","688012","002371","002463","600487","600522","002916","002837","002851","600584","688629","688981","601138","002156","300750","601012","300274","600089","688126","300666","688019","300054","603650","300260","600183","688300","601208","603662","600118","601100","300660","002378"]

date_y = time.strftime('%Y%m%d')
results = {}

# SSE (6xxxxx, 5xxxxx)
try:
    df_sse = ak.stock_margin_detail_sse(date=date_y)
    sse_stocks = df_sse[df_sse.iloc[:,1].astype(str).str.match(r'^[56]\d{5}$')]
    for _, row in sse_stocks.iterrows():
        code = str(row.iloc[1])
        buy = int(row.iloc[3]) if row.iloc[3] else 0
        repay = int(row.iloc[4]) if row.iloc[4] else 0
        bal = int(row.iloc[5]) if row.iloc[5] else 0
        if code in CODES and bal > 0:
            results[code] = {"name": str(row.iloc[2]), "margin_buy": buy, "margin_repay": repay, "margin_bal": bal}
    print(f"SSE: {len([c for c in CODES if c in results])} 只")
except Exception as e:
    print(f"SSE error: {e}")

# SZSE (0xxxxx, 3xxxxx)
try:
    df_sz = ak.stock_margin_detail_szse(date=time.strftime('%Y-%m-%d'))
    for _, row in df_sz.iterrows():
        try:
            code = str(int(row.iloc[1])).zfill(6)
        except:
            continue
        try: buy = int(row.iloc[3])
        except: buy = 0
        try: repay = int(row.iloc[4])
        except: repay = 0
        try: bal = int(row.iloc[5])
        except: bal = 0
        if code in CODES and bal > 0:
            results[code] = {"name": str(row.iloc[2]), "margin_buy": buy, "margin_repay": repay, "margin_bal": bal}
    print(f"SZSE: {len([c for c in CODES if c in results and not c.startswith(('6','5'))])} 只")
except Exception as e:
    print(f"SZSE error: {e}")

print(f"\n📊 融资融券 · {time.strftime('%Y-%m-%d')} · {len(results)} 只")
net_buys = 0
for code in sorted(results.keys()):
    d = results[code]
    net = d["margin_buy"] - d["margin_repay"]
    if net > 0: net_buys += 1
    arrow = "↑" if net > 0 else "↓"
    print(f"  {code} {d['name']:<8} 买入{d['margin_buy']/1e8:.1f}亿 偿还{d['margin_repay']/1e8:.1f}亿 余额{d['margin_bal']/1e8:.1f}亿 {arrow}")
print(f"\n融资净买入: {net_buys}/{len(results)} 只")

with open(os.path.join(DIR, "margin_data.json"), "w", encoding="utf-8") as f:
    json.dump({"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "data": results}, f, ensure_ascii=False, indent=2)
print("✅ 已保存 margin_data.json")
