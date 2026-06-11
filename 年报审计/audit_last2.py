import os, time, json, urllib.request, fitz, re

BASE = "https://api.siliconflow.cn/v1"
MODEL = "deepseek-ai/DeepSeek-V3"
KEY = "REPLACE_WITH_YOUR_KEY"
PROMPT = "Analyze this annual report. Find all customer/supply chain evidence. E1=names specific customer. E2=implies. E3=vague. Check if claims like '独家供应/全球唯一' are supported. Return ONLY JSON array."

import glob as gb
os.chdir(os.path.dirname(os.path.abspath(__file__)))
targets = {"联瑞新材": "联瑞", "隆扬电子": "隆扬"}
for name, keyword in targets.items():
    matches = gb.glob(f"半导体材料/*{keyword}*.pdf")
    if not matches:
        print(f"\n=== {name}: NOT FOUND ===")
        continue
    pdf = matches[0]
    print(f"\n=== {name} ({os.path.basename(pdf)[:40]}) ===")
    doc = fitz.open(pdf)
    pages = [(i+1, doc[i].get_text()) for i in range(min(len(doc), 35)) if doc[i].get_text() and len(doc[i].get_text().strip()) > 50]
    doc.close()
    relevant = [(pg, t) for pg, t in pages if any(kw in t for kw in ["客户","供应","认证","独家","全球唯","NVIDIA","英伟达","Intel","AMD","台积","华为","苹果"])]
    text = "\n".join([f"[p{pg}] {t}" for pg, t in relevant])[:22000]
    print(f"  {len(relevant)} relevant pages, {len(text)} chars")
    if len(text) < 200:
        print("  SKIP: too little content")
        continue
    data = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": PROMPT + "\n\n" + text}], "temperature": 0.1, "max_tokens": 1500}).encode()
    req = urllib.request.Request(f"{BASE}/chat/completions", data=data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
        content = resp["choices"][0]["message"]["content"].strip()
        if content.startswith("```"): content = re.sub(r"^```\w*\n?", "", content); content = re.sub(r"\n?```$", "", content)
        findings = json.loads(content) if content else []
        for f in findings:
            gr = f.get("grade", "?")
            if gr in ("E1", "E2"):
                print(f"  [{gr}] {f.get('customer','?')} | {f.get('product','?')}")
                print(f"    {f.get('quote','')[:180]}")
        print(f"  E1={len([f for f in findings if f.get('grade')=='E1'])} E2={len([f for f in findings if f.get('grade')=='E2'])}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(10)
print("\nDONE")
