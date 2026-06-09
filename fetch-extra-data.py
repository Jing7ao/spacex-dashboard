# fetch-extra-data.py — 股东户数+十大流通股东+概念板块
# 输出 extra-data.js → 面板加载
# 用法: python fetch-extra-data.py

import requests, json, sys, os, io, time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = os.path.dirname(os.path.abspath(__file__))
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://data.eastmoney.com/'}

TRACKED = {
    '000400':'许继电气','000682':'东方电子','000938':'紫光股份','000970':'中科三环',
    '000977':'浪潮信息','000988':'华工科技','002028':'思源电气','002036':'联创电子',
    '002050':'三花智控','002126':'银轮股份','002129':'中环股份','002135':'东南网架',
    '002149':'西部材料','002156':'通富微电','002230':'科大讯飞','002241':'歌尔股份',
    '002270':'华明装备','002281':'光迅科技','002335':'科华数据','002340':'格林美',
    '002364':'中恒电气','002371':'北方华创','002463':'沪电股份','002466':'天齐锂业',
    '002475':'立讯精密','002536':'飞龙股份','002792':'通宇通讯','002837':'英维克',
    '002851':'麦格米特','002865':'钧达股份','002916':'深南电路','002920':'德赛西威',
    '300040':'九洲集团','300054':'鼎龙股份','300070':'碧水源','300136':'信维通信',
    '300153':'科泰电源','300249':'依米康','300260':'新莱应材','300274':'阳光电源',
    '300308':'中际旭创','300346':'南大光电','300383':'光环新网','300394':'天孚通信',
    '300395':'菲利华','300408':'三环集团','300418':'昆仑万维','300433':'蓝思科技',
    '300476':'胜宏科技','300499':'高澜股份','300502':'新易盛','300567':'精测电子',
    '300570':'太辰光','300604':'长川科技','300620':'光库科技','300655':'晶瑞电材',
    '300666':'江丰电子','300712':'永福股份','300738':'奥飞数据','300748':'金力永磁',
    '300750':'宁德时代','300779':'惠城环保','300782':'卓胜微','300855':'图南股份',
    '300990':'同飞股份','301005':'超捷股份','301018':'申菱环境','301086':'鸿富瀚',
    '301162':'国能日新','301165':'锐捷网络','301389':'隆扬电子','301522':'上大股份',
    '600008':'首创环保','600089':'特变电工','600126':'杭钢股份','600131':'国网信通',
    '600143':'金发科技','600183':'生益科技','600312':'平高电气','600362':'江西铜业',
    '600406':'国电南瑞','600456':'宝钛股份','600477':'杭萧钢构','600487':'亨通光电',
    '600496':'精工钢构','600522':'中天科技','600584':'长电科技','600602':'云赛智联',
    '600699':'均胜电子','600745':'闻泰科技','600804':'*ST鹏博士','600869':'远东股份',
    '600875':'东方电气','601012':'隆基绿能','601126':'四方股份','601138':'工业富联',
    '601179':'中国西电','601208':'东材科技','601689':'拓普集团','601789':'宁波建工',
    '601869':'长飞光纤','601877':'正泰电器','603191':'望变电气','603212':'赛伍技术',
    '603256':'宏和科技','603290':'斯达半导','603305':'旭升集团','603308':'应流股份',
    '603348':'文灿股份','603601':'再升科技','603606':'东方电缆','603650':'彤程新材',
    '603662':'柯力传感','603799':'华友钴业','603809':'豪能股份','603881':'数据港',
    '603986':'兆易创新','605123':'派克新材','605589':'圣泉集团','688008':'澜起科技',
    '688012':'中微公司','688017':'绿的谐波','688019':'安集科技','688102':'斯瑞新材',
    '688111':'金山办公','688126':'沪硅产业','688146':'中船特气','688153':'英诺赛科',
    '688248':'南网科技','688256':'寒武纪','688268':'华特气体','688300':'联瑞新材',
    '688333':'铂力特','688498':'源杰科技','688535':'华海诚科','688599':'天合光能',
    '688668':'鼎通科技','688676':'金盘科技','688981':'中芯国际',
}

def api_get(url, params):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        j = r.json()
        if j.get('result') and j['result'].get('data'):
            return j['result']['data']
        if j.get('result') and isinstance(j['result'], list):
            return j['result']
        return []
    except:
        return []

def fetch_shareholders():
    print('[1/3] Shareholder counts...')
    url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
    result = {}
    for i, code in enumerate(TRACKED.keys()):
        try:
            data = api_get(url, {
                'reportName': 'RPT_F10_EH_HOLDERNUM',
                'columns': 'SECURITY_CODE,END_DATE,HOLDER_TOTAL_NUM,TOTAL_NUM_RATIO',
                'filter': f'(SECURITY_CODE="{code}")',
                'pageSize': 2, 'pageNumber': 1,
                'sortTypes': '-1', 'sortColumns': 'END_DATE'
            })
            if data and len(data) >= 1:
                cur = data[0]
                cc = cur.get('HOLDER_TOTAL_NUM')
                cr = cur.get('TOTAL_NUM_RATIO')
                if cc and cr is not None:
                    cr = round(float(cr), 1)
                    if cr <= -10: sig = 'high_concentration'
                    elif cr <= -5: sig = 'concentration'
                    elif cr >= 10: sig = 'dispersion'
                    elif cr >= 5: sig = 'mild_dispersion'
                    else: sig = 'stable'
                    result[code] = {'count': cc, 'change_pct': cr, 'signal': sig,
                        'date': cur.get('END_DATE','')[:10]}
                else:
                    result[code] = None
            else:
                result[code] = None
        except:
            result[code] = None
        if (i+1) % 15 == 0:
            print(f'  {i+1}/{len(TRACKED)} ...')
        time.sleep(0.15)
    print(f'  Done: {sum(1 for v in result.values() if v is not None)} stocks')
    return result

def fetch_top10():
    print('[2/3] Top 10 holders...')
    url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
    result = {}
    for i, code in enumerate(TRACKED.keys()):
        try:
            data = api_get(url, {
                'reportName': 'RPT_F10_EH_FREEHOLDERS',
                'columns': 'SECURITY_CODE,END_DATE,HOLDER_NAME,HOLD_NUM,HOLD_NUM_CHANGE,HOLDER_TYPE',
                'filter': f'(SECURITY_CODE="{code}")',
                'pageSize': 10, 'pageNumber': 1,
                'sortTypes': '-1', 'sortColumns': 'END_DATE'
            })
            if data:
                latest_date = data[0].get('END_DATE','')
                holders = []
                inst_all = 0; inst_active = 0
                new_entries = []
                passive_kw = ['香港中央结算','沪股通','深股通','ETF','指数','联接','LOF']
                for h in data:
                    name = str(h.get('HOLDER_NAME',''))
                    shares = str(h.get('HOLD_NUM',''))
                    change = str(h.get('HOLD_NUM_CHANGE',''))
                    htype = str(h.get('HOLDER_TYPE',''))
                    is_inst = any(kw in name+htype for kw in
                        ['基金','社保','QFII','券商','保险','信托','银行','私募','资产',
                         '证券','汇金','证金','香港中央结算','沪股通','深股通','组合'])
                    is_passive = any(kw in name for kw in passive_kw)
                    if is_inst: inst_all += 1
                    if is_inst and not is_passive: inst_active += 1
                    if '新进' in change or 'NEW' in change.upper():
                        new_entries.append(name[:20])
                    holders.append({'n': name[:30], 'sh': shares, 'ch': change, 'inst': is_inst, 'passive': is_passive})
                result[code] = {'date': latest_date[:10], 'inst_count': inst_all,
                    'active_count': inst_active, 'new': new_entries[:5], 'holders': holders}
            else:
                result[code] = None
        except:
            result[code] = None
        if (i+1) % 15 == 0:
            print(f'  {i+1}/{len(TRACKED)} ...')
        time.sleep(0.15)
    print(f'  Done: {sum(1 for v in result.values() if v is not None)} stocks')
    return result

def fetch_concepts():
    print('[3/3] Concept boards (AKShare)...')
    try:
        import akshare as ak
        boards = ['英伟达概念','特斯拉概念','人形机器人','商业航天',
            'AI服务器','液冷服务器','CPO','光模块','PCB概念','Chiplet','先进封装','第三代半导体']
        all_members = {}
        for b in boards:
            try:
                df = ak.stock_board_concept_cons_em(symbol=b)
                if df is not None and len(df) > 0:
                    cc = '代码' if '代码' in df.columns else df.columns[0]
                    all_members[b] = [str(c) for c in df[cc].tolist()]
                    print(f'  {b}: {len(all_members[b])} stocks')
            except Exception as e:
                print(f'  {b}: error - {e}')
            time.sleep(0.5)

        tracked_in = {}
        for code, name in TRACKED.items():
            bs = [b for b, ms in all_members.items() if code in ms]
            if bs: tracked_in[code] = bs

        new_cand = {}
        for b, ms in all_members.items():
            ut = [m for m in ms if m not in TRACKED]
            if ut: new_cand[b] = ut[:15]

        return {'tracked_mapping': tracked_in, 'new_candidates': new_cand}
    except Exception as e:
        print(f'  AKShare error: {e}')
        return {'tracked_mapping': {}, 'new_candidates': {}}

def main():
    print(f'=== Extra Data ({datetime.now().strftime("%H:%M")}) ===\n')

    sh = fetch_shareholders()
    print()
    t10 = fetch_top10()
    print()
    cs = fetch_concepts()

    output = {'updated': datetime.now().isoformat(), 'shareholders': sh, 'top10': t10, 'concepts': cs}

    js_path = os.path.join(DIR, 'extra-data.js')
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(f'// Auto-generated {datetime.now().isoformat()}\n')
        f.write(f'var EXTRA_DATA = {json.dumps(output, ensure_ascii=False)};\n')
    print(f'\nDone: {js_path}')

    conc = sum(1 for v in sh.values() if v and v.get('signal') in ('high_concentration','concentration'))
    disp = sum(1 for v in sh.values() if v and v.get('signal') in ('dispersion','mild_dispersion'))
    heavy_old = sum(1 for v in t10.values() if v and v.get('inst_count',0) >= 5)
    heavy_active = sum(1 for v in t10.values() if v and v.get('active_count',0) >= 3)
    total_new = sum(len(v) for v in cs.get('new_candidates',{}).values())
    print(f'Summary: 筹码集中={conc} | 筹码分散={disp} | 主动机构>=3={heavy_active} | 全部机构>=5={heavy_old} | 新候选={total_new}')

if __name__ == '__main__':
    main()
