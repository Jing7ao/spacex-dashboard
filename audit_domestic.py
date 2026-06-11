# audit_domestic.py — 新领域瓶颈 · 国产替代角度重审
import PyPDF2, os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = r'c:\Users\13639\spacex-dashboard\年报'

BATCH = [
    ('300308','中际旭创','光模块','中际旭创：2025年年度报告.pdf'),
    ('002837','英维克','液冷CDU','英维克：2025年年度报告.pdf'),
    ('600183','生益科技','CCL覆铜板','生益科技：生益科技2025年年度报告.pdf'),
    ('688300','联瑞新材','球形硅微粉','联瑞新材：联瑞新材2025年年度报告.pdf'),
]

# 国产替代关键词
KW_MAP = {
    '国产替代/自主可控': ['国产替代','自主可控','国产化','自主研制','自主研发','进口替代','打破垄断','填补空白'],
    '国内地位（首家/唯一/领先）': ['国内首家','国内唯一','国内领先','国内第一','国内独家','首家','唯一','独家','第一','领先'],
    '量产+产能': ['量产','产能','出货量','批量生产','批量供应','规模生产','产能扩张','扩产'],
    '市场份额': ['市占','市场份额','占有率','全球第','国内第','排名'],
    '客户认证': ['认证','通过.*认证','获得.*认证','送样','验证'],
}

def extract_text(pdf_path):
    try:
        with open(pdf_path,'rb') as f:
            return ' '.join([p.extract_text() or '' for p in PyPDF2.PdfReader(f).pages])
    except: return ''

def find_context(text, kw, window=100):
    results = []
    idx = 0
    while True:
        pos = text.find(kw, idx)
        if pos == -1: break
        start = max(0, pos - window)
        end = min(len(text), pos + len(kw) + window)
        results.append(text[start:end].replace('\n',' ').strip()[:250])
        idx = pos + 1
    return results

for code, name, biz, filename in BATCH:
    pdf_path = os.path.join(DIR, filename)
    print(f"\n{'='*70}")
    print(f"  {name}({code}) — {biz}")
    print(f"{'='*70}")
    if not os.path.exists(pdf_path):
        print(f"  ❌ 文件不存在"); continue
    text = extract_text(pdf_path)
    if not text:
        print(f"  ❌ PDF解析失败"); continue
    print(f"  {len(text):,} 字\n")

    score = 0
    for cat, kws in KW_MAP.items():
        hits = 0
        best_ctx = ''
        for kw in kws:
            if kw.startswith('通过.*'):
                matches = len(re.findall(kw, text))
            else:
                matches = text.count(kw)
            if matches > 0:
                hits += matches
                ctxs = find_context(text, kw, 80)
                # 找最相关的上下文（包含产品的）
                for c in ctxs:
                    if biz[:2] in c or '产品' in c or '公司' in c:
                        best_ctx = c; break
                if not best_ctx and ctxs:
                    best_ctx = ctxs[0]
        if hits > 0:
            icon = '✅' if hits >= 3 else '⚠️'
            score += 1
            print(f"  {icon} {cat}: {hits}次 ", end='')
            if best_ctx: print(f"→ {best_ctx[:150]}")
            else: print()

    print(f"\n  🎯 国产替代强度: {score}/{len(KW_MAP)}")
    if score >= 4:
        print(f"  >> 🌟 国产替代实锤——年报有充分的自证")
    elif score >= 3:
        print(f"  >> 🟡 有一定证据但不充分")
    else:
        print(f"  >> ⚪ 年报自证不足，市场声称存疑")
