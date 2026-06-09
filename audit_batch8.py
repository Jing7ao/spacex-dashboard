# audit_batch8.py — 第8批年报审计（10只）
import PyPDF2, os, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'c:\Users\13639\spacex-dashboard\年报'

BATCH8 = [
    ('002028', '思源电气', '思源电气：2025年年度报告.pdf'),
    ('688676', '金盘科技', '金盘科技：2025年年度报告.pdf'),
    ('300153', '科泰电源', '科泰电源：2025年年度报告.pdf'),
    ('301086', '鸿富瀚', '鸿富瀚：2025年年度报告.pdf'),
    ('301162', '国能日新', '国能日新：2025年年度报告.pdf'),
    ('000682', '东方电子', '东方电子：2025年年度报告.pdf'),
    ('300738', '奥飞数据', '奥飞数据：2025年年度报告.pdf'),
    ('603606', '东方电缆', '东方电缆：东方电缆2025年年度报告.pdf'),
    ('300570', '太辰光', '太辰光：2025年年度报告.pdf'),
    ('300383', '光环新网', '光环新网：2025年年度报告.pdf'),
]

EXCLUSIVITY = re.compile(r'独家|唯一|垄断|仅有')
RANKING = re.compile(r'第一|第二|第三|领先|龙头|最大|前茅|排名|位居|名列')
SHARE = re.compile(r'市[场占]率|份额|占有率|全球第|国内第|国际第')
SUPPLY_CHAIN = re.compile(r'供应商|供应链|供货|交付|通过认证|Tier|核心客户|大客户')
NVIDIA_TERMS = re.compile(r'英伟达|NVIDIA|GB300|GB200|H100|H200|B100|B200|Rubin|Vera|Blackwell')
SPACEX_TESLA = re.compile(r'SpaceX|特斯拉|Tesla|Optimus|Starlink|星链')
DOMESTIC = re.compile(r'华为|昇腾|字节|阿里|腾讯|百度|Meta|Amazon|AWS|出海|海外')

def extract_text_safe(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages:
                try:
                    t = page.extract_text()
                    if t: text += t + '\n'
                except: pass
            return text
    except Exception as e:
        print(f'  ERROR: {e}')
        return ''

def find_context(text, keyword, window=80):
    results = []
    idx = 0
    while True:
        pos = text.find(keyword, idx)
        if pos == -1: break
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)
        ctx = text[start:end].replace('\n', ' ').strip()
        results.append((pos, ctx))
        idx = pos + 1
    return results

def main():
    print('='*70)
    print('BATCH 8 ANNUAL REPORT AUDIT')
    print('='*70)

    all_findings = {}

    for code, name, filename in BATCH8:
        pdf_path = os.path.join(DIR, filename)
        if not os.path.exists(pdf_path):
            print(f'\n## {name}({code}) — FILE NOT FOUND')
            continue

        print(f'\n{"="*70}')
        print(f'## {name}({code})')
        print(f'{"="*70}')

        text = extract_text_safe(pdf_path)
        if not text:
            print('  [EMPTY]')
            continue

        print(f'  ~{len(text):,} chars')

        findings = {'exclusivity':[],'ranking':[],'share':[],'supply_chain':[],'nvidia':[],'spacex_tesla':[],'domestic':[]}

        for kw in ['独家', '唯一', '垄断']:
            for pos, ctx in find_context(text, kw, 100):
                findings['exclusivity'].append({'keyword': kw, 'context': ctx[:200]})

        for kw in ['第一', '领先', '龙头', '最大', '位居', '名列前茅']:
            for pos, ctx in find_context(text, kw, 80):
                findings['ranking'].append({'keyword': kw, 'context': ctx[:180]})

        for kw in ['市占率', '市场份额', '占有率']:
            for pos, ctx in find_context(text, kw, 80):
                findings['share'].append({'keyword': kw, 'context': ctx[:180]})

        for kw in ['供应商', '供应链', '供货', 'Tier', '核心客户', '批量交付', '中标']:
            for pos, ctx in find_context(text, kw, 80):
                findings['supply_chain'].append({'keyword': kw, 'context': ctx[:180]})

        for m in NVIDIA_TERMS.finditer(text):
            ctx = text[max(0,m.start()-80):min(len(text),m.end()+80)].replace('\n',' ').strip()
            findings['nvidia'].append({'keyword': m.group(), 'context': ctx[:180]})

        for m in SPACEX_TESLA.finditer(text):
            ctx = text[max(0,m.start()-80):min(len(text),m.end()+80)].replace('\n',' ').strip()
            findings['spacex_tesla'].append({'keyword': m.group(), 'context': ctx[:180]})

        for kw in ['华为', '字节', '阿里', '腾讯', 'Meta', 'Amazon', 'AWS']:
            for pos, ctx in find_context(text, kw, 80):
                findings['domestic'].append({'keyword': kw, 'context': ctx[:180]})

        total_hits = sum(len(v) for v in findings.values())
        if total_hits == 0:
            print('  [NO HITS]')
        else:
            for cat, items in findings.items():
                if items:
                    cat_name = {
                        'exclusivity':'🔴 独家/唯一','ranking':'🟡 排名/地位','share':'🟢 市占/份额',
                        'supply_chain':'🔵 供应链','nvidia':'🟣 英伟达','spacex_tesla':'🟠 SpaceX/Tesla',
                        'domestic':'⚪ 大客户/出海'
                    }[cat]
                    print(f'\n  {cat_name} ({len(items)} hits):')
                    for item in items[:5]:
                        print(f'    [{item["keyword"]}] ...{item["context"][:160]}...')
                    if len(items) > 5:
                        print(f'    ... and {len(items)-5} more')

        all_findings[f'{name}({code})'] = {
            'total_hits': sum(len(v) for v in findings.values()),
            'categories': {k: len(v) for k, v in findings.items() if v}
        }

    print('\n\n' + '='*70)
    print('BATCH 8 SUMMARY')
    print('='*70)
    for stock, info in all_findings.items():
        cats = ', '.join(f'{k}({v})' for k, v in info['categories'].items())
        print(f'  {stock}: {info["total_hits"]} hits — {cats if cats else "无"}')

if __name__ == '__main__':
    main()
