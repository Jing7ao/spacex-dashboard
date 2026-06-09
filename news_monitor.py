# news_monitor.py — 供应链新闻监控 + 标的匹配 + 影响预测
# 用法: python news_monitor.py           # 拉取最新新闻
#       python news_monitor.py --serve    # 启动HTTP服务,面板可调用
import json, urllib.request, sys, io, os, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = os.path.dirname(os.path.abspath(__file__))

# ── 供应链关键词 → 标的映射 ──────────────────────
KEYWORD_MAP = {
    "OpenAI|openai|ChatGPT|GPT-5": ["AI算力","光模块","液冷"],
    "NVIDIA|英伟达|黄仁勋|GB300|Rubin|Blackwell|GPU": ["300476","601138","300308","300394","002463","002851","002837","600584","300502"],
    "SpaceX|星舰|Starship|星链|Starlink|猛禽|Raptor": ["688102","002149","300136","600456","603601","301522","605123","603308"],
    "特斯拉|Tesla|Optimus|FSD|Cybertruck|4680": ["601689","002050","603305","688017","603662","002036"],
    "光模块|CPO|800G|1.6T|3.2T|LPO": ["300308","300394","300502","002281","000988"],
    "PCB|电路板|封装基板|IC载板|CCL": ["300476","002463","600183","002916"],
    "液冷|散热|数据中心电源": ["002837","002851","301018","300499"],
    "华为|昇腾|910C|鲲鹏|鸿蒙": ["688629","002916","603986","002371"],
    "机器人|人形机器人|减速器|丝杠|执行器": ["688017","601100","603662","601689","002050"],
    "低空经济|eVTOL|无人机|空管": ["688631","688070","000099"],
    "半导体设备|光刻|刻蚀|薄膜|检测|量测": ["688012","002371","300567","300604"],
    "光刻胶|电子特气|硅片|靶材|CMP|抛光": ["300346","688268","688126","300666","688019","300054"],
    "海缆|海底光缆|跨洋|光纤": ["600487","600522","603606","601869"],
    "特高压|电网|储能|光伏|电力": ["600089","601179","601877","300274","601012"],
    "封测|先进封装|Chiplet|CoWoS|HBM": ["600584","002156","688981"],
    "军工|航天|卫星|火箭|蓝箭|星网": ["600118","688102","002179","001270"],
}

# Stock name lookup
STOCK_NAMES = {}
try:
    with open(os.path.join(DIR, "stock-data.json"), encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            for s in data: STOCK_NAMES[s.get("c","")] = s.get("n","")
        else:
            for c, s in data.items(): STOCK_NAMES[c] = s.get("n","") if isinstance(s,dict) else str(s)
except: pass

# Manual fallback for key stocks
NAME_FALLBACK = {"300476":"胜宏科技","002463":"沪电股份","601138":"工业富联","300308":"中际旭创",
    "300394":"天孚通信","002851":"麦格米特","002837":"英维克","600584":"长电科技","300502":"新易盛",
    "688102":"斯瑞新材","002149":"西部材料","300136":"信维通信","600456":"宝钛股份","603601":"再升科技",
    "601689":"拓普集团","002050":"三花智控","603305":"旭升集团","688017":"绿的谐波","603662":"柯力传感",
    "600487":"亨通光电","600522":"中天科技","603606":"东方电缆","600183":"生益科技","002916":"深南电路",
    "300346":"南大光电","688268":"华特气体","688012":"中微公司","002371":"北方华创","301522":"上大股份",
    "300408":"三环集团","688300":"联瑞新材","605589":"圣泉集团","603308":"应流股份","301005":"超捷股份",
    "688629":"华丰科技","002281":"光迅科技","000988":"华工科技","600089":"特变电工","600118":"中国卫星",
    "688631":"莱斯信息","688070":"纵横股份","000099":"中信海直","002156":"通富微电","002036":"联创电子",
    "002792":"通宇通讯","300855":"图南股份","688333":"铂力特","300395":"菲利华","002179":"中航光电",
    "600869":"远东股份","002466":"天齐锂业"
}

def get_name(code):
    return STOCK_NAMES.get(code) or NAME_FALLBACK.get(code) or code

# ── 新闻拉取 ─────────────────────────────────
def fetch_sina_news(keyword, count=10):
    """新浪财经新闻搜索"""
    results = []
    try:
        url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k={urllib.request.quote(keyword)}&num={count}&page=1"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            for item in data.get("result",{}).get("data",[]):
                results.append({
                    "title": item.get("title",""),
                    "url": item.get("url",""),
                    "time": item.get("ctime",""),
                    "source": "sina"
                })
    except Exception as e:
        pass
    return results

def fetch_eastmoney_news(keyword, count=10):
    """东方财富新闻搜索"""
    results = []
    try:
        url = f"https://searchapi.eastmoney.com/bussiness/Web/GetCMSSearchResult?type=8196&pageindex=1&pagesize={count}&keyword={urllib.request.quote(keyword)}&name=zixun"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.eastmoney.com/"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            for item in data.get("Data",[]):
                results.append({
                    "title": item.get("Title",""),
                    "url": item.get("Url",""),
                    "time": item.get("ShowTime",""),
                    "source": "eastmoney"
                })
    except: pass
    return results

# ── 新闻→标的匹配 ────────────────────────────
def match_stocks(news_title):
    """根据新闻标题匹配受影响的股票代码"""
    matched = set()
    affected_ecos = set()
    for pattern, targets in KEYWORD_MAP.items():
        if re.search(pattern, news_title, re.IGNORECASE):
            for t in targets:
                if t.startswith("0") or t.startswith("3") or t.startswith("6") or t.startswith("5"):
                    matched.add(t)
                else:
                    affected_ecos.add(t)
    return list(matched), list(affected_ecos)

# ── 影响预测（简化版：基于关键词+供应链层级） ──
def predict_impact(news_title):
    """简单情感判断 + 影响方向"""
    positive_patterns = ["突破","量产","认证","订单","增长","利好","合作","签署","通过","中标","第一","领先","唯一"]
    negative_patterns = ["制裁","限制","禁令","脱钩","调查","处罚","亏损","暴跌","退市","造假","暴雷","封锁","断供"]
    pos = sum(1 for p in positive_patterns if p in news_title)
    neg = sum(1 for p in negative_patterns if p in news_title)
    if pos > neg: return "positive"
    elif neg > pos: return "negative"
    return "neutral"

# ── 主逻辑 ──────────────────────────────────
def run():
    print(f"🔍 供应链新闻监控 · {time.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    all_news = []
    # 搜索关键主题（用更精准的关键词）
    topics = ["英伟达 GB300","SpaceX 星舰 发射","OpenAI 芯片 半导体","特斯拉 Optimus 机器人",
              "光模块 800G 1.6T","PCB 电路板 AI服务器","华为 昇腾 910C","人形机器人 减速器",
              "低空经济 eVTOL 无人机","半导体光刻 设备"]
    seen_titles = set()
    for topic in topics:
        print(f"  搜索: {topic}")
        news_items = fetch_eastmoney_news(topic, 8)
        # Eastmoney returns more targeted results; fallback to Sina
        if len(news_items) < 3:
            news_items += fetch_sina_news(topic, 3)
        for item in news_items:
            if item["title"] in seen_titles: continue
            if len(item["title"]) < 10: continue
            seen_titles.add(item["title"])
            matched_stocks, matched_ecos = match_stocks(item["title"])
            if not matched_stocks and not matched_ecos: continue  # 跳过无关新闻
            impact = predict_impact(item["title"])
            all_news.append({**item, "stocks": matched_stocks, "ecos": matched_ecos, "impact": impact})
        time.sleep(0.3)

    # 按影响排序：利空在前
    all_news.sort(key=lambda n: (n["impact"]!="negative", n["impact"]!="positive", -len(n["stocks"])))

    # 输出
    print(f"\n📰 共 {len(all_news)} 条相关新闻\n")
    for item in all_news[:30]:
        impact_icon = {"positive":"🟢","negative":"🔴","neutral":"⚪"}[item["impact"]]
        stock_names = [f"{get_name(c)}({c})" for c in item["stocks"][:5]]
        stock_str = " → " + ", ".join(stock_names) if stock_names else ""
        print(f"  {impact_icon} [{item['time'][:10]}] {item['title'][:80]}")
        if stock_str: print(f"     {stock_str}")
    print()

    # 保存结果
    output = {
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(all_news),
        "news": [{**n, "stocks": n["stocks"], "ecos": n["ecos"]} for n in all_news[:50]]
    }
    with open(os.path.join(DIR, "supply_chain_news.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存 supply_chain_news.json ({len(all_news)} 条)")

if __name__ == "__main__":
    run()
