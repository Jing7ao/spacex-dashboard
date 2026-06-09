"""
AI 年报审计 — 用 DeepSeek 提取供应链证据
输入: PDF文件
输出: E1/E2/E3 标注结果
"""
import os, json, glob, re, urllib.request
import fitz  # PyMuPDF — much better CJK support

# ====== SiliconFlow API (supports DeepSeek models) ======
BASE = "https://api.siliconflow.cn/v1"
MODEL = "deepseek-ai/DeepSeek-V3"
KEY = os.environ.get("SILICONFLOW_API_KEY", "")
if not KEY:
    # Try reading from claude.json MCP config
    import json as _json
    try:
        with open(os.path.expanduser("~/.claude.json")) as f:
            d = _json.load(f)
        for s in d.get("mcpServers", {}).values():
            k = s.get("env", {}).get("SILICONFLOW_API_KEY", "")
            if k:
                KEY = k
                break
    except: pass

PROMPT = """Analyze this section of a Chinese A-share annual report (年报). Extract ALL evidence related to supply chain relationships (供应链关系).

For each finding, classify:
- E1 (可查证): Company explicitly names a major customer (e.g. NVIDIA, 英伟达, SpaceX, Tesla, Google, Meta, Amazon, Microsoft, 华为, 字节 etc.) and describes the supply relationship (product, order amount, certification status)
- E2 (可推断): Company mentions "international leading GPU/AI company" or "North American major client" or "海外头部客户" without naming them, but context strongly implies the customer
- E3 (待验证): Only vague mentions like "industry-leading customers" or market speculation

For EACH finding, return:
1. Evidence grade (E1/E2/E3)
2. Product mentioned (光模块/CPO/PCB/液冷 etc.)
3. Customer implied (which company)
4. Verbatim Chinese quote from the text (原文字句)
5. Page number approximation

Return ONLY valid JSON array. No markdown, no explanation.
Format: [{"grade":"E1","product":"1.6T光模块","customer":"NVIDIA","quote":"本公司系国际头部GPU企业核心供应商","source":"年报正文"}]
If nothing found, return []."""


def call_deepseek(text_chunk):
    """Send text to DeepSeek for supply chain analysis"""
    data = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a financial analyst extracting supply chain evidence from Chinese annual reports. Return ONLY valid JSON arrays."},
            {"role": "user", "content": PROMPT + "\n\nTEXT:\n" + text_chunk[:30000]}
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode()

    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY}",
        }
    )

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        # Try to extract JSON from response
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r'^```\w*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        return json.loads(content) if content else []
    except Exception as e:
        print(f"  API error: {e}")
        return []


def extract_text(pdf_path, max_pages=None):
    """Extract text from PDF using PyMuPDF (excellent CJK support)"""
    doc = fitz.open(pdf_path)
    all_text = []
    for i in range(len(doc)):
        try:
            text = doc[i].get_text()
            if text and len(text.strip()) > 50:
                if any(kw in text for kw in ['客户','供应','采购','订单','认证','合作','销售','主要','核心']):
                    all_text.append((i+1, text))
        except: pass
    doc.close()
    return all_text


def audit_pdf(pdf_path, name):
    """Full audit pipeline for one PDF"""
    print(f"\n{'='*60}")
    print(f"  AI Audit: {name}")
    print(f"{'='*60}")

    pages = extract_text(pdf_path)
    if not pages:
        print("  No relevant pages found.")
        return []

    # Chunk pages into ~25000 char batches
    chunks = []
    current_chunk = ""
    current_pages = []
    for pg, text in pages:
        if len(current_chunk) + len(text) > 25000:
            chunks.append((current_pages, current_chunk))
            current_chunk = text
            current_pages = [pg]
        else:
            current_chunk += "\n" + text
            current_pages.append(pg)
    if current_chunk:
        chunks.append((current_pages, current_chunk))

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()
    print(f"  Pages with relevant content: {len(pages)}/{total_pages}")
    print(f"  Chunks to analyze: {len(chunks)}")

    all_findings = []
    for i, (pgs, chunk) in enumerate(chunks):
        print(f"  [{i+1}/{len(chunks)}] Analyzing pages {pgs[0]}-{pgs[-1]} ({len(chunk)} chars)...")
        findings = call_deepseek(chunk)
        for f in findings:
            f["company"] = name
            # Try to find which page
            for pg_num in pgs:
                if any(w in chunk[chunk.find(str(pg_num)):chunk.find(str(pg_num))+500]
                       for w in f.get("quote","")[:20].split()):
                    f["page"] = pg_num
                    break
            else:
                f["page"] = pgs[0]
        all_findings.extend(findings)
        print(f"    Found {len(findings)} findings")

    return all_findings


if __name__ == "__main__":
    if not KEY:
        print("ERROR: API key not found.")
        exit(1)

    import time
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 扫描所有子目录
    all_pdfs = []
    for subdir in sorted(glob.glob("*/")):
        pdfs = sorted(glob.glob(f"{subdir}*.pdf"))
        for p in pdfs:
            all_pdfs.append((subdir.rstrip("/"), p))

    if not all_pdfs:
        print("No PDFs found in subdirectories")
        exit(1)

    print(f"Found {len(all_pdfs)} PDFs across {len(set(d for d,_ in all_pdfs))} categories")
    print(f"Using API: {BASE}")

    all_results = {}
    for i, (category, pdf) in enumerate(all_pdfs):
        time.sleep(8)  # 限流保护 429
        name = os.path.basename(pdf).replace("：2025年年度报告.pdf","").replace(".pdf","")
        name = name.replace("四川东材科技集团股份有限公司","东材科技").replace("圣泉集团：","").replace("圣泉集团2025年年度报告摘要","圣泉集团(摘要)")
        findings = audit_pdf(pdf, f"[{category}] {name}")
        all_results[f"{category}/{name}"] = findings

        e1s = [f for f in findings if f.get("grade") == "E1"]
        e2s = [f for f in findings if f.get("grade") == "E2"]
        print(f"  E1={len(e1s)} E2={len(e2s)} Total={len(findings)}")

    # 按目录分组保存
    for category in sorted(set(d for d,_ in all_pdfs)):
        cat_results = {k: v for k, v in all_results.items() if k.startswith(category)}
        output = f"{category}/audit_results.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(cat_results, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {output}")

    print("\nDONE. Summary:")
    for k, v in all_results.items():
        e1 = len([f for f in v if f.get("grade")=="E1"])
        e2 = len([f for f in v if f.get("grade")=="E2"])
        if e1 or e2:
            print(f"  {k}: E1={e1} E2={e2}")
