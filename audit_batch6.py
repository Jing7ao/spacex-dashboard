# audit_batch6.py — 第6批年报审计（10只）
# 搜索: 独家/唯一/垄断/第一/市占/份额/领先/龙头/最大/前茅
import PyPDF2, os, re, sys, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'c:\Users\13639\spacex-dashboard\年报'

BATCH6 = [
    ('002837', '英维克', '英维克：2025年年度报告.pdf'),
    ('002364', '中恒电气', '中恒电气：2025年年度报告.pdf'),
    ('600089', '特变电工', '特变电工：特变电工股份有限公司2025年年度报告.pdf'),
    ('002335', '科华数据', '科华数据：2025年年度报告.pdf'),
    ('300054', '鼎龙股份', '鼎龙股份：2025年年度报告.pdf'),
    ('300655', '晶瑞电材', '晶瑞电材：2025年年度报告.pdf'),
    ('601179', '中国西电', '中国西电：中国西电2025年年度报告.pdf'),
    ('688019', '安集科技', '安集科技：2025年年度报告.pdf'),
    ('301165', '锐捷网络', '锐捷网络：2025年年度报告.pdf'),
    ('603290', '斯达半导', '斯达半导：斯达半导体股份有限公司2025年年度报告.pdf'),
]

# 关键词分组
EXCLUSIVITY = re.compile(r'独家|唯一|垄断|仅有|仅有')
RANKING = re.compile(r'第一|第二|第三|领先|龙头|最大|前茅|排名|位居|名列')
SHARE = re.compile(r'市[场占]率|份额|占有率|全球第|国内第|国际第')
SUPPLY_CHAIN = re.compile(r'供应商|供应链|供货|交付|通过认证|Tier|核心客户|大客户')
NVIDIA_TERMS = re.compile(r'英伟达|NVIDIA|GB300|GB200|H100|H200|B100|B200|Rubin|Vera|Blackwell')
SPACEX_TESLA = re.compile(r'SpaceX|特斯拉|Tesla|Optimus|Starlink|星链')
DOMESTIC = re.compile(r'华为|昇腾|鲲鹏|寒武纪|海光|刻蚀|CMP|PVD|CVD|碳化硅|氮化镓|SiC|GaN|光刻胶')

def extract_text_safe(pdf_path):
    """安全提取PDF文本"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages:
                try:
                    t = page.extract_text()
                    if t:
                        text += t + '\n'
                except:
                    pass
            return text
    except Exception as e:
        print(f'  ERROR: {e}')
        return ''

def find_context(text, keyword, window=80):
    """查找关键词前后上下文"""
    results = []
    idx = 0
    while True:
        pos = text.find(keyword, idx)
        if pos == -1:
            break
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)
        ctx = text[start:end].replace('\n', ' ').strip()
        results.append((pos, ctx))
        idx = pos + 1
    return results

def main():
    print('='*70)
    print('BATCH 6 ANNUAL REPORT AUDIT')
    print(f'Target: 10 stocks | Keywords: 4 groups')
    print('='*70)

    total_pages = 0
    all_findings = {}

    for code, name, filename in BATCH6:
        pdf_path = os.path.join(DIR, filename)
        if not os.path.exists(pdf_path):
            print(f'\n## {name}({code}) — FILE NOT FOUND: {filename}')
            continue

        print(f'\n{"="*70}')
        print(f'## {name}({code}) — {filename}')
        print(f'{"="*70}')

        text = extract_text_safe(pdf_path)
        if not text:
            print('  [EMPTY TEXT]')
            continue

        pages = text.count('\f') + 1  # rough estimate
        total_pages += pages
        print(f'  Extracted ~{len(text):,} chars (~{pages} pages)')

        findings = {
            'exclusivity': [], 'ranking': [], 'share': [], 'supply_chain': [],
            'nvidia': [], 'spacex_tesla': [], 'domestic': []
        }

        # 搜索"独家/唯一/垄断"
        for kw in ['独家', '唯一', '垄断']:
            for pos, ctx in find_context(text, kw, 100):
                findings['exclusivity'].append({'keyword': kw, 'context': ctx[:200]})

        # 搜索排名声明
        for kw in ['第一', '领先', '龙头', '最大', '位居', '名列前茅']:
            for pos, ctx in find_context(text, kw, 80):
                findings['ranking'].append({'keyword': kw, 'context': ctx[:180]})

        # 搜索市场份额
        for kw in ['市占率', '市场份额', '占有率']:
            for pos, ctx in find_context(text, kw, 80):
                findings['share'].append({'keyword': kw, 'context': ctx[:180]})

        # 搜索供应链相关
        for kw in ['供应商', '供应链', '供货', 'Tier', '核心客户']:
            for pos, ctx in find_context(text, kw, 80):
                findings['supply_chain'].append({'keyword': kw, 'context': ctx[:180]})

        # 搜索英伟达相关
        for m in NVIDIA_TERMS.finditer(text):
            ctx = text[max(0,m.start()-80):min(len(text),m.end()+80)].replace('\n',' ').strip()
            findings['nvidia'].append({'keyword': m.group(), 'context': ctx[:180]})

        # 搜索SpaceX/Tesla相关
        for m in SPACEX_TESLA.finditer(text):
            ctx = text[max(0,m.start()-80):min(len(text),m.end()+80)].replace('\n',' ').strip()
            findings['spacex_tesla'].append({'keyword': m.group(), 'context': ctx[:180]})

        # 搜索国内产业链
        for kw in ['华为', '昇腾', '刻蚀', 'CMP', '碳化硅', '氮化镓', '光刻胶']:
            for pos, ctx in find_context(text, kw, 80):
                findings['domestic'].append({'keyword': kw, 'context': ctx[:180]})

        # 打印结果
        total_hits = sum(len(v) for v in findings.values())
        if total_hits == 0:
            print('  [NO HITS — 无供应链相关声明]')
        else:
            for cat, items in findings.items():
                if items:
                    cat_name = {
                        'exclusivity': '🔴 独家/唯一',
                        'ranking': '🟡 排名/地位',
                        'share': '🟢 市占/份额',
                        'supply_chain': '🔵 供应链',
                        'nvidia': '🟣 英伟达',
                        'spacex_tesla': '🟠 SpaceX/Tesla',
                        'domestic': '⚪ 国内产业链',
                    }[cat]
                    print(f'\n  {cat_name} ({len(items)} hits):')
                    for item in items[:5]:  # max 5 per category
                        print(f'    [{item["keyword"]}] ...{item["context"][:160]}...')
                    if len(items) > 5:
                        print(f'    ... and {len(items)-5} more')

        all_findings[f'{name}({code})'] = {
            'total_hits': sum(len(v) for v in findings.values()),
            'categories': {k: len(v) for k, v in findings.items() if v}
        }

    # 汇总
    print('\n\n' + '='*70)
    print('BATCH 6 SUMMARY')
    print(f'Total pages processed: ~{total_pages}')
    print('='*70)
    for stock, info in all_findings.items():
        cats = ', '.join(f'{k}({v})' for k, v in info['categories'].items())
        print(f'  {stock}: {info["total_hits"]} hits — {cats if cats else "无"}')

if __name__ == '__main__':
    main()
