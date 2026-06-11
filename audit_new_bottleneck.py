# audit_new_bottleneck.py — 新领域瓶颈 E1 审计（光通信CPO/液冷/半导体材料）
import PyPDF2, os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = r'c:\Users\13639\spacex-dashboard\年报'

BATCH = [
    ('300308','中际旭创','中际旭创：2025年年度报告.pdf', ['1.6T','800G','NVIDIA','英伟达','GB300','光模块','认证','独家','唯一','龙头','第一','市占']),
    ('300394','天孚通信','天孚通信：2025年年度报告.pdf', ['CPO','FAU','光引擎','NVIDIA','英伟达','GB300','独家','唯一','认证','订单','75亿']),
    ('002837','英维克','英维克：2025年年度报告.pdf', ['NVL','液冷','NVIDIA','英伟达','CDU','Tier1','认证','独家','唯一','订单']),
    ('601208','东材科技','东材科技：四川东材科技集团股份有限公司2025年年度报告.pdf', ['M9','碳氢树脂','NVIDIA','英伟达','GPU','认证','独家','唯一','路线图','PCB']),
    ('600183','生益科技','生益科技：生益科技2025年年度报告.pdf', ['M9','认证','NVIDIA','英伟达','GPU','独家','唯一','覆铜板','CCL','订单']),
]

def extract_text(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return ' '.join([p.extract_text() or '' for p in reader.pages])
    except: return ''

def find_context(text, kw, window=80):
    results = []
    idx = 0
    while True:
        pos = text.find(kw, idx)
        if pos == -1: break
        start = max(0, pos - window)
        end = min(len(text), pos + len(kw) + window)
        results.append(text[start:end].replace('\n', ' ').strip()[:200])
        idx = pos + 1
    return results

for code, name, filename, keywords in BATCH:
    pdf_path = os.path.join(DIR, filename)
    print(f"\n{'='*65}")
    print(f"  {name}({code})")
    print(f"{'='*65}")
    if not os.path.exists(pdf_path):
        print(f"  ❌ 文件不存在")
        continue
    text = extract_text(pdf_path)
    if not text:
        print(f"  ❌ PDF解析失败")
        continue
    print(f"  {len(text):,} 字")

    # Count all keywords
    for kw in keywords:
        count = text.count(kw)
        if count > 0:
            ctx = find_context(text, kw, 60)
            key_ctx = [c for c in ctx if any(w in c for w in ['独家','唯一','认证','通过','全球第','国内第','第一','龙头'])]
            if key_ctx:
                print(f"  [{kw}:{count}次] {key_ctx[0][:150]}")
            else:
                print(f"  [{kw}:{count}次] (无关键上下文)")

    # Critical checks
    checks = {
        '独家/唯一': bool(re.search(r'独家供应|唯一供应商|全球唯一|国内唯一', text)),
        'NVIDIA点名': bool(re.search(r'NVIDIA|英伟达', text)),
        'GPU点名': bool(re.search(r'GPU|GB300|Rubin|Blackwell', text)),
        '认证提及': bool(re.search(r'认证|通过.*认证|获得.*认证', text)),
        '批量/订单': bool(re.search(r'批量交付|批量供货|在手中|订单.*亿', text)),
    }
    print(f"\n  📋 关键声称验证:")
    for check, passed in checks.items():
        icon = '✅' if passed else '❌'
        print(f"    {icon} {check}")

    score = sum(1 for v in checks.values() if v)
    print(f"  🎯 E1强度: {score}/{len(checks)}")
