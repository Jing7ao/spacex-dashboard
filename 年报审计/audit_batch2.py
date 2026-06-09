"""Audit batch 2: 半导体材料 + 机器人"""
import os, glob, time, json, urllib.request, fitz, re

BASE = "https://api.siliconflow.cn/v1"
MODEL = "deepseek-ai/DeepSeek-V3"
KEY = "sk-gmqqbzhpqashlbxxrspnbzhelfysasnsvzkfkutjjszxykrd"

PROMPT = (
    "Analyze this Chinese annual report section. Extract ALL supply chain relationship evidence.\n"
    "E1 = company names a specific customer (e.g. NVIDIA, Google, Intel, 华为, 字节).\n"
    "E2 = implies customer (e.g. 'international leading GPU company').\n"
    "E3 = vague mention only.\n"
    "For each finding: grade, product, customer, verbatim Chinese quote, source section.\n"
    "Return ONLY a JSON array. No markdown. If nothing found, return []."
)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

for cat in ["半导体材料", "机器人"]:
    pdfs = sorted(glob.glob(f"{cat}/*.pdf"))
    if not pdfs:
        continue
    print(f"\n=== {cat} ({len(pdfs)} PDFs) ===")
    all_results = {}

    for pdf in pdfs:
        name = os.path.basename(pdf)[:40].replace(".pdf","")
        doc = fitz.open(pdf)
        pages = []
        for i in range(min(len(doc), 40)):
            text = doc[i].get_text()
            if text and len(text.strip()) > 50:
                pages.append((i+1, text))
        doc.close()

        # 只取含关键业务词的前35页
        relevant = [(pg, t) for pg, t in pages if any(
            kw in t for kw in ["客户","供应","采购","认证","合作","销售","核心","独家","NVIDIA","英伟达","Intel","Google"]
        )]
        if len(relevant) > 20:
            # 太多页就只取含最强关键词的
            strong = [(pg, t) for pg, t in relevant if any(
                kw in t for kw in ["客户","供应","认证","NVIDIA","英伟达","独家"]
            )]
            if strong:
                relevant = strong[:25]

        text = "\n".join([f"[p{pg}] {t}" for pg, t in relevant])[:28000]

        print(f"  {name}: {len(relevant)} relevant pages, {len(text)} chars")

        if len(text) < 200:
            print("    SKIP: too little content")
            continue

        # Call API
        data = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": PROMPT + "\n\nTEXT:\n" + text}],
            "temperature": 0.1,
            "max_tokens": 2000,
        }).encode()

        req = urllib.request.Request(
            f"{BASE}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"},
        )

        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
            content = resp["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            findings = json.loads(content) if content else []
        except Exception as e:
            print(f"    API ERROR: {e}")
            findings = []

        e1 = [f for f in findings if f.get("grade") == "E1"]
        e2 = [f for f in findings if f.get("grade") == "E2"]
        print(f"    E1={len(e1)} E2={len(e2)}")

        for f in e1:
            print(f'    [E1] {f.get("customer","?")} | {f.get("product","?")} | {f.get("quote","")[:120]}')
        for f in e2[:3]:
            print(f'    [E2] {f.get("customer","?")} | {f.get("product","?")} | {f.get("quote","")[:100]}')

        all_results[name] = findings
        time.sleep(10)  # 限流

    # Save per category
    with open(f"{cat}/audit_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {cat}/audit_results.json")

print("\nALL DONE")
