# 瓶颈股年报E1审计脚本
import os,re,glob

DIR=r'C:\Users\13639\spacex-dashboard\年报'
TARGETS={
    '600456':'宝钛股份','002149':'西部材料','301522':'上大股份',
    '605123':'派克新材','603308':'应流股份','300136':'信维通信',
    '300395':'菲利华','600584':'长电科技'
}
KEYS={
    '独家/唯一':r'独家|唯一|全球唯一',
    '批量供货':r'批量供货|批量交付|批量生产',
    '客户确认':r'SpaceX|Starlink|星链|NVIDIA|英伟达|Tesla|特斯拉',
    '认证':r'认证|通过.*认证|NADCAP|NASA|AS9100',
    '龙头/第一':r'龙头|全球第|国内第|行业第|市占率',
    '供货措辞':r'供货|供应|交付.*客户|终端.*客户',
}

def audit(pdf_path,code,name):
    try:
        from PyPDF2 import PdfReader
        reader=PdfReader(pdf_path)
        text=' '.join([p.extract_text() or '' for p in reader.pages])
    except:
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text=' '.join([p.extract_text() or '' for p in pdf.pages])
        except:
            return {'code':code,'name':name,'error':'PDF解析失败','findings':{},'pages':0}
    pages=len(reader.pages) if 'reader' in dir() else 0
    findings={}
    for k,pat in KEYS.items():
        matches=re.findall(pat,text)
        findings[k]=len(matches)
        if matches:
            # 提取第一条匹配的上下文(前后30字)
            first=matches[0]
            idx=text.find(first)
            ctx=text[max(0,idx-30):idx+len(first)+30].replace('\n',' ')
            findings[k+'_ctx']=ctx[:100]
    return {'code':code,'name':name,'pages':pages,'findings':findings}

print('瓶颈股年报E1审计')
print('='*60)
results=[]
for code,name in TARGETS.items():
    pdfs=glob.glob(os.path.join(DIR,f'*{name}*.pdf'))
    if not pdfs:pdfs=glob.glob(os.path.join(DIR,f'*{code}*.pdf'))
    if not pdfs:
        print(f'FAIL {code} {name}: PDF not found')
        results.append({'code':code,'name':name,'error':'PDF not found'})
        continue
    r=audit(pdfs[0],code,name)
    results.append(r)
    f=r['findings']
    ok='OK' if not r.get('error') else 'FAIL'
    print(f"\n[{ok}] {code} {name} ({r.get('pages',0)} pages)")
    if r.get('error'):continue
    for k in KEYS:
        cnt=f.get(k,0)
        bar='#'*min(cnt,20) if cnt else '--'
        ctx=f.get(k+'_ctx','')
        print(f'  {k}: {cnt} hits {bar}')
        if ctx:print(f'    -> {ctx[:100]}')

# 汇总
print('\n'+'='*60)
print('汇总')
for r in results:
    f=r.get('findings',{})
    score=sum([1 for k in KEYS if f.get(k,0)>0])
    print(f"{r['code']} {r['name']}: {score}/{len(KEYS)}项命中")
