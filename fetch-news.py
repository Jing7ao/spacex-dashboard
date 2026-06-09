# fetch-news.py — 为52只标的拉取东方财富个股新闻，过滤供应链关键词
# 输出 stock-news.js → 面板加载
# 用法: python fetch-news.py

import akshare as ak, json, sys, os, io, re, time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = os.path.dirname(os.path.abspath(__file__))

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

# 供应链关键词（用于过滤新闻）
SC_KW = re.compile(
    'NVIDIA|英伟达|SpaceX|星链|Starlink|Tesla|特斯拉|Optimus|'
    '供货|独家|唯一|批量|量产|认证|Tier|核心供应商|一级供应商|'
    '订单|合同|海外客户|国际客户|头部客户|大客户|'
    '新建产线|扩产|通过验证|送样|取得突破|首家|率先|'
    'GPU|AI算力|HBM|封装|液冷|光模块|CPO|PCB|载板|基板|铜箔|树脂|电源|'
    '宇航级|航天级|卫星|火箭|发动机|猛禽|FSD|自动驾驶|人形机器人', re.IGNORECASE)

def main():
    print(f'=== Stock News Fetch ({datetime.now().strftime("%H:%M")}) ===')
    print(f'Fetching news for {len(TRACKED)} stocks...\n')

    result = {}
    total_news = 0
    sc_news = 0

    codes = list(TRACKED.keys())
    for i, code in enumerate(codes):
        name = TRACKED[code]
        try:
            df = ak.stock_news_em(symbol=code)
            if df is None or len(df) == 0:
                result[code] = {'name': name, 'news': [], 'sc_count': 0}
                continue

            news_list = []
            sc_count = 0
            for _, row in df.head(10).iterrows():
                title = str(row.get('新闻标题', ''))
                pub_time = str(row.get('发布时间', ''))[:16]
                source = str(row.get('文章来源', ''))
                url = str(row.get('新闻链接', ''))
                content = str(row.get('新闻内容', ''))[:150]

                is_sc = bool(SC_KW.search(title + content))
                if is_sc:
                    sc_count += 1

                news_list.append({
                    't': title[:80], 'pt': pub_time, 's': source, 'u': url,
                    'c': content, 'sc': is_sc
                })

            result[code] = {'name': name, 'news': news_list[:10], 'sc_count': sc_count}
            total_news += len(news_list)
            sc_news += sc_count

        except Exception as e:
            result[code] = {'name': name, 'news': [], 'sc_count': 0}

        if (i+1) % 10 == 0:
            print(f'  {i+1}/{len(codes)} ...')
        time.sleep(0.2)

    # 汇总
    sc_stocks = {code: data for code, data in result.items() if data['sc_count'] > 0}
    print(f'\nDone: {total_news} news items, {sc_news} supply-chain related across {len(sc_stocks)} stocks')

    # 显示有供应链新闻的标的
    if sc_stocks:
        print('\nSupply-chain news today:')
        for code, data in sorted(sc_stocks.items(), key=lambda x: -x[1]['sc_count'])[:10]:
            sc_items = [n for n in data['news'] if n['sc']]
            print(f'  {data["name"]}({code}): {len(sc_items)} items')
            for n in sc_items[:3]:
                print(f'    [{n["pt"]}] {n["t"][:70]}')

    # 写入 JS 文件
    js_path = os.path.join(DIR, 'stock-news.js')
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(f'// Auto-generated {datetime.now().isoformat()}\n')
        f.write(f'var STOCK_NEWS = {json.dumps(result, ensure_ascii=False)};\n')
    print(f'\nWritten: {js_path}')

if __name__ == '__main__':
    main()
