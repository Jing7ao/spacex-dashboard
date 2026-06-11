# fetch_irm_backup.py — 巨潮投资者关系活动记录表（机构调研纪要，E1级）
import sys, io, json, os, time, urllib.request, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

CODES = ["688017","688102","300476","300136","300308","300394","300502","002281",
         "002149","002837","002851","600584","688300","601208","600183","603662"]

print(f"📋 投资者关系记录表 · {time.strftime('%Y-%m-%d')}")
print("=" * 60)

results = {}
for code in CODES:
    try:
        url = f"https://www.cninfo.com.cn/new/disclosure/detail?stockCode={code}&pageNum=1&pageSize=5&column=szse_latest&tabName=fulltext"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.cninfo.com.cn/"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            matches = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]*调研[^<]*|[^<]*活动记录[^<]*|[^<]*业绩说明[^<]*)</a>', html)
            if matches:
                items = []
                for href, title in matches[:5]:
                    full_url = href if href.startswith("http") else "https://www.cninfo.com.cn"+href
                    items.append({"title": title.strip(), "url": full_url})
                results[code] = items
                print(f"  {code}: {items[0]['title'][:80]}")
    except Exception as e:
        pass
    time.sleep(0.3)

print(f"\n📊 {len(results)}/16 只有调研纪要")

with open(os.path.join(DIR, "irm_data.json"), "w", encoding="utf-8") as f:
    json.dump({"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "data": results, "source": "cninfo_investor_relation", "note": "机构调研纪要(E1级)，点击URL查看完整PDF"}, f, ensure_ascii=False, indent=2)
print("✅ 已保存 irm_data.json")
