# expand_pool.py — 同赛道扩容（半导体+光通信+机器人+新能源+军工材料）
import json, urllib.request, sys, io, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

# 同赛道板块
SECTORS = {
    "半导体": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",  # 半导体+芯片+设备
    "光通信": "b:BK0593",  # 光通信板块
    "机器人": "b:BK1143",  # 机器人概念
    "新能源": "b:BK0493",  # 新能源
    "军工航天": "b:BK0546",  # 军工
    "液冷散热": "b:BK1188",  # 液冷概念
}

existing_codes = set()
try:
    with open(os.path.join(DIR, "monitor.html"), encoding="utf-8") as f:
        import re
        codes = re.findall(r"\{c:'(\d+)'", f.read())
        existing_codes = set(codes)
except: pass

all_new = {}
for sector, fs in SECTORS.items():
    url = f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=0&np=1&fields=f12,f14,f20&fid=f20&fs={fs}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            stocks = data.get("data",{}).get("diff",[])
            new = [s for s in stocks if s["f12"] not in existing_codes]
            print(f"{sector}: {len(stocks)} total, {len(new)} new")
            for s in new[:30]:  # Top 30 per sector
                all_new[s["f12"]] = {"n": s["f14"], "sector": sector}
    except Exception as e:
        print(f"{sector}: error {e}")
    time.sleep(0.3)

print(f"\nTotal new unique: {len(all_new)}")

# Build expanded research pool (existing + new)
expanded = list(existing_codes) + list(all_new.keys())
print(f"Research pool: {len(expanded)} stocks")

with open(os.path.join(DIR, "research_pool.json"), "w", encoding="utf-8") as f:
    json.dump({"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "total": len(expanded),
               "existing": len(existing_codes), "new": len(all_new),
               "codes": expanded, "new_stocks": all_new}, f, ensure_ascii=False, indent=2)
print("✅ Saved research_pool.json")
