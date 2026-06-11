# fetch_irm.py — 互动易/上证e互动 监控（散户看不到的独家信息源）
# 用法: python fetch_irm.py
# 输出: irm_data.json → 面板加载
import sys, io, json, os, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

# 核心标的
CODES = ["688017","688102","300476","300136","300308","300394","300502","002281",
         "002149","601689","002050","603305","300395","688333","600456","603601",
         "002036","300346","688268","688012","002371","002463","600487","600522",
         "002916","002837","002851","600584","688629","688981","300750","601138"]

# 半导体材料标的（文档 §四重点关注）
SEMI_CODES = ["300346","688268","688126","300666","688019","300054","603650","300260",
              "688146","300655","688120"]

ALL = list(set(CODES + SEMI_CODES))

def fetch_irm(code):
    """东方财富互动易：拉最新问答"""
    items = []
    try:
        # 互动易API: 分页拉取
        for page in [1, 2]:
            url = f"https://irm.eastmoney.com/PC_IRM/Search/Question?code=SZ{code}&page={page}&size=10"
            if code.startswith(("6","5")): url = url.replace("SZ","SH")
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Referer":"https://irm.eastmoney.com/"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                rows = data.get("Data",{}).get("list",[]) if isinstance(data.get("Data"),dict) else []
                if not rows: break
                for row in rows:
                    q = row.get("QuestionTitle","") or row.get("Question","")
                    a = row.get("AnswerContent","") or row.get("Answer","")
                    dt = row.get("QuestionDate","") or row.get("CreateTime","")
                    if q and dt:
                        items.append({"question":q[:200],"answer":a[:300],"date":dt[:10]})
        # Filter: only keep supply-chain relevant Q&As
        keywords = ["SpaceX","星链","星舰","英伟达","NVIDIA","GPU","GB300","华为","昇腾",
                    "特斯拉","Tesla","Optimus","机器人","减速器","丝杠","光模块","CPO",
                    "PCB","封装","液冷","散热","认证","量产","独家","唯一","供应","客户"]
        relevant = []
        for item in items:
            qa = item["question"] + item["answer"]
            if any(kw in qa for kw in keywords):
                relevant.append(item)
        return relevant
    except Exception as e:
        return []

print(f"🔍 互动易监控 · {time.strftime('%Y-%m-%d')}")
print("=" * 60)

results = {}
found = 0
for code in ALL:
    items = fetch_irm(code)
    if items:
        results[code] = items
        found += 1
        print(f"  {code}: {len(items)} 条相关问答")
        for item in items[:2]:
            print(f"    Q: {item['question'][:100]}")
            a_preview = item['answer'][:120].replace('\n',' ')
            print(f"    A: {a_preview}...")
    time.sleep(0.3)

print(f"\n📊 {found}/{len(ALL)} 只有供应链相关互动问答")

output = {"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "data": results}
with open(os.path.join(DIR, "irm_data.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("✅ 已保存 irm_data.json")
