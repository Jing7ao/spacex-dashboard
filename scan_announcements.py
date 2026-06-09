# scan_announcements.py — 全自动公告扫描
# 每天跑一次: python scan_announcements.py
# 自动拉全市场A股公告 → 过滤53只标的 → 关键词匹配 → 追加到events.json

import akshare as ak
import pandas as pd
import json, sys, os, io
from datetime import datetime, timedelta

# 修复Windows GBK编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ═══ 53只跟踪标的 ═══
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

# ═══ 供应链关键词 ═══
KEYWORDS = [
    'NVIDIA','英伟达','SpaceX','星链','Starlink','Tesla','特斯拉','Optimus',
    '供货','独家供应','唯一供应商','批量交付','批量供货','量产','通过认证','Tier1',
    '一级供应商','核心供应商','海外大客户','国际客户','头部客户','获得订单','中标',
    '新建产线','扩产','宇航级','航天级','猛禽','FSD','GPU','PCB','封装','液冷',
    '光模块','CPO','覆铜板','铜箔','碳氢树脂','基板','载板','EMC',
    '33kW电源','送样','通过验证','通过客户','认证通过','首家','率先','突破',
    '供应商','供应链','HVLP','Q布','电子布','M9树脂','GB300','Rubin','Vera','H20',
    # --- 国内自主产业链 ---
    '华为','昇腾','鲲鹏','寒武纪','海光','国产替代','自主可控',
    '刻蚀','薄膜','离子注入','光刻','检测','清洗','CMP','PVD','CVD','ALD',
    '碳化硅','氮化镓','SiC','GaN','大硅片','光刻胶','电子特气','靶材',
    '商业航天','低轨卫星','卫星互联网','火箭','可回收','液氧甲烷',
    '算力','数据中心','服务器','AIDC','智算','超算',
    '虚拟电厂','储能','光伏','风电','特高压','柔直','换流阀',
    '机器人','人形','减速器','执行器','六维力','力矩',
]

# ═══ 配置 ═══
EVENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'events.json')
DAYS_BACK = int(sys.argv[1]) if len(sys.argv) > 1 else 7

def scan_day(date_str):
    """扫描某一天的公告"""
    try:
        df = ak.stock_notice_report(symbol="全部", date=date_str)
        if df is None or len(df) == 0:
            return []
        # 修复列名编码（AKShare可能返回Unicode转义列名）
        cols = {}
        for i, c in enumerate(df.columns):
            try:
                name = c.encode('raw_unicode_escape').decode('utf-8') if '\\u' in str(c) else str(c)
            except:
                name = str(c)
            cols[name] = i
        # 同时支持整数索引fallback: 0=代码 1=名称 2=公告标题 3=公告类型 4=公告日期 5=网址
        code_col = cols.get('代码', 0) if cols else 0
        title_col = cols.get('公告标题', 2) if cols else 2
        url_col = cols.get('网址', 5) if cols else 5
        type_col = cols.get('公告类型', 3) if cols else 3

        results = []
        for _, row in df.iterrows():
            code = str(row.iloc[code_col] if isinstance(code_col, int) else row.get('代码', '')).strip()
            title = str(row.iloc[title_col] if isinstance(title_col, int) else row.get('公告标题', '')).strip()
            url = str(row.iloc[url_col] if isinstance(url_col, int) else row.get('网址', '')).strip()
            notice_type = str(row.iloc[type_col] if isinstance(type_col, int) else row.get('公告类型', '')).strip()

            # 必须是跟踪标的
            if code not in TRACKED:
                continue

            # 必须包含关键词
            matched_kw = []
            for kw in KEYWORDS:
                if kw.lower() in title.lower():
                    matched_kw.append(kw)
            if not matched_kw:
                continue

            # ═══ 噪声过滤（v3.1 新增，基于 214 条 LLM 分类经验） ═══
            # 1. 内部治理公告（全市场通用）
            INTERNAL = ['股东会','股东大会','董事会决议','监事会决议','独立董事','董事/高级管理人员',
                '权益分派','利润分配','公积金转增','章程','管理制度','议事规则','工作制度',
                '审计报告','内部控制','募集资金','验资报告','限售股','回购公司股份',
                '减持','增持','质押','解质押','担保','关联交易管理制度',
                '2025年年度报告','半年报','季度报告','业绩预告','业绩快报',
                '法律意见书','核查意见','核查报告','督导报告','跟踪报告','保荐书',
                '上市公告书','发行结果','发行情况','认购对象','发行过程',
                '信息披露','投资者关系','内幕信息','知情人','重组报告书',
                '独立财务顾问','审阅报告','评估报告','评估说明','审核问询函',
                '募集说明书','自查报告','摊薄即期','填补措施','产业政策',
                '股票交易风险','股票交易异常','做市交易',
                '会计师事务所','选聘制度','履职情况','述职报告',
                '可持续发展报告','ESG','提质增效重回报','分红派息',
                '更正','补充公告','说明公告']
            is_internal = False
            for kw in INTERNAL:
                if kw in title:
                    is_internal = True
                    break
            if is_internal:
                continue

            # 2. 建筑施工中标（结构/路桥/市政工程，非供应链）
            if code in ['601789','002135','600477','600496']:  # 宁波建工/东南网架/杭萧钢构/精工钢构
                CONSTRUCTION = ['施工','公路','快速路','地块','建设工程','EPC总承包',
                    '改建工程','道路','停车场','市政','桥梁','隧道','轨道交通',
                    '产业园','安置房','保障房','住宅','商业地产']
                is_construction = False
                for kw in CONSTRUCTION:
                    if kw in title:
                        is_construction = True
                        break
                if is_construction:
                    continue

            results.append({
                'code': code,
                'name': TRACKED[code],
                'title': title,
                'date': f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                'url': url,
                'type': notice_type,
                'keywords': matched_kw,
            })
        return results
    except Exception as e:
        print(f"  Error on {date_str}: {e}")
        return []

def classify_event(title):
    """根据标题分类事件类型"""
    if any(kw in title for kw in ['订单', '合同', '中标']):
        return 'order_disclose'
    if any(kw in title for kw in ['认证', '通过', '送样', '验证通过']):
        return 'cert_progress'
    if any(kw in title for kw in ['新建', '扩产', '项目']):
        return 'expand'
    if any(kw in title for kw in ['终止', '减持', '退市', 'ST']):
        return 'refute'
    if any(kw in title for kw in ['财务报告', '年报', '半年报', '季报']):
        return 'supply_confirm'  # 年报可能含供应链信息
    return 'supply_confirm'

def main():
    today = datetime.today()
    start = today - timedelta(days=DAYS_BACK)

    print(f"[scan] {start.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')} ({DAYS_BACK} days)")
    print(f"       tracking {len(TRACKED)} stocks")
    print()

    all_results = []
    current = start
    day_count = 0

    while current <= today:
        date_str = current.strftime('%Y%m%d')
        # 跳过周末（AKShare周末无数据，减少无效请求）
        if current.weekday() < 5:
            day_count += 1
            results = scan_day(date_str)
            if results:
                print(f"  {current.strftime('%m-%d')} → {len(results)} 条")
                all_results.extend(results)
        current += timedelta(days=1)

    print(f"\n---")
    print(f"Scanned {day_count} trading days，发现 {len(all_results)} candidates")

    if not all_results:
        print("No candidates.。")
        return

    # 去重
    seen = set()
    unique = []
    for r in all_results:
        key = f"{r['code']}|{r['title'][:60]}"
        if key not in seen:
            seen.add(key)
            unique.append(r)

    unique.sort(key=lambda x: x['date'], reverse=True)

    print(f"Deduplicated {len(unique)} 条:\n")
    for i, r in enumerate(unique):
        print(f"[{i+1}] {r['date']} | {r['name']}({r['code']}) | {r['type']}")
        print(f"    {r['title']}")
        kw_str = ', '.join(r['keywords'][:5])
        print(f"    Hits: {kw_str}")
        if r['url']:
            print(f"    Link: {r['url']}")
        print()

    # 生成候选 events
    candidates = []
    for r in unique:
        candidates.append({
            "id": f"evt_scan_{datetime.now().strftime('%Y%m%d')}_{r['code']}",
            "stock_code": r['code'],
            "stock_name": r['name'],
            "event_date": r['date'],
            "event_type": classify_event(r['title']),
            "event_desc": r['title'][:100],
            "source_ref": f"{r['type']} | {r['url']}" if r['url'] else r['type'],
            "source_type": "东方财富公告",
            "evidence_level": "E2",
            "d0_return": None, "d5_excess": None, "d20_excess": None, "d60_excess": None,
            "notes": f"自动扫描 | 关键词: {', '.join(r['keywords'][:3])}"
        })

    # 写入 events-pending.json
    pending_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'events-pending.json')
    with open(pending_file, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"Generated {pending_file} ({len(candidates)} 条)")
    print()
    print("Next steps:")
    print("  1. 审核 events-pending.json（删除误判条目）")
    print("  2. 确认的条目 → 追加到 events.json")
    print("  3. node fill-returns.js（自动填充收益）")

if __name__ == '__main__':
    main()
