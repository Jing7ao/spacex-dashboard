"""Audit batch 3: 马斯克生态 + 英伟达补充"""
import os, glob, time, json, urllib.request, fitz, re

BASE = "https://api.siliconflow.cn/v1"
MODEL = "deepseek-ai/DeepSeek-V3"
KEY = "REPLACE_WITH_YOUR_KEY"
PROMPT = "Analyze this annual report. Find ALL named customers and supply chain evidence. E1=names specific customer. E2=implies. E3=vague/unsupported. Check claims like '独家供应/唯一/全球唯' against actual report text. Return ONLY JSON array."

os.chdir(os.path.dirname(os.path.abspath(__file__)))

for cat in ["马斯克生态", "英伟达补充"]:
    print(f"\n{'='*60}")
    print(f"  {cat}")
    print(f"{'='*60}")
    pdfs = sorted(glob.glob(f"{cat}/*.pdf"))
    all_results = {}

    for pdf in pdfs:
        name = os.path.basename(pdf)[:45]
        doc = fitz.open(pdf)
        pages = [(i+1, doc[i].get_text()) for i in range(min(len(doc), 35)) if doc[i].get_text() and len(doc[i].get_text().strip()) > 50]
        doc.close()

        relevant = [(pg, t) for pg, t in pages if any(kw in t for kw in [
            "客户","供应","认证","独家","唯一","全球","NVIDIA","英伟达","SpaceX","Tesla","特斯拉",
            "Intel","AMD","Google","华为","苹果","Amazon","Meta","Microsoft","星链","Starlink",
            "Elon","Musk","星舰","火箭","Optimus","机器人","FSD","自动驾驶"
        ])]
        if len(relevant) > 25:
            relevant = relevant[:25]

        text = "\n".join([f"[p{pg}] {t}" for pg, t in relevant])[:24000]
        print(f"  {name}: {len(relevant)} pages, {len(text)} chars")

        if len(text) < 200:
            print("    SKIP")
            continue

        data = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": PROMPT + "\n\n" + text}], "temperature": 0.1, "max_tokens": 1500}).encode()
        req = urllib.request.Request(f"{BASE}/chat/completions", data=data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
            content = resp["choices"][0]["message"]["content"].strip()
            if content.startswith("```"): content = re.sub(r"^```\w*\n?", "", content); content = re.sub(r"\n?```$", "", content)
            findings = json.loads(content) if content else []
            if not isinstance(findings, list):
                findings = []
        except json.JSONDecodeError:
            print(f"    JSON parse failed, response was: {content[:200]}")
            findings = []
        except Exception as e:
            print(f"    API ERROR: {e}")
            findings = []

        e1 = [f for f in findings if f.get("grade") == "E1"]
        e2 = [f for f in findings if f.get("grade") == "E2"]
        print(f"    E1={len(e1)} E2={len(e2)}")
        for f in e1:
            print(f"    [E1] {f.get('customer','?')} | {f.get('product','?')} | {f.get('quote','')[:120]}")
        for f in e2[:2]:
            print(f"    [E2] {f.get('customer','?')} | {f.get('product','?')} | {f.get('quote','')[:100]}")

        all_results[name] = findings
        with open(f"{cat}/audit_results.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        time.sleep(10)

    print(f"  Saved: {cat}/audit_results.json")

print("\nALL DONE")
