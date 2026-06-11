# policy_monitor.py — 政策文件自动抓取+DeepSeek解读+供应链关联
import sys, io, json, os, time, urllib.request, urllib.parse, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

# DeepSeek API配置
DS_KEY = "sk-c488cb49d95d4ec4b9da62bbd708a74b"
DS_URL = "https://api.deepseek.com/v1/chat/completions"

# 政策源
SOURCES = [
    {"name":"国务院","url":"http://www.gov.cn/zhengce/","type":"gov"},
    {"name":"工信部","url":"https://www.miit.gov.cn/","type":"miit"},
    {"name":"发改委","url":"https://www.ndrc.gov.cn/","type":"ndrc"},
    {"name":"科技部","url":"https://www.most.gov.cn/","type":"most"},
]

# 供应链关键词→受益方向映射
ECO_MAP = {
    "人工智能|AI|算力|芯片|半导体|大模型|数据": ("国产AI算力","AI算力产业链"),
    "机器人|人形|智能装备|自动化|智能制造": ("国产机器人","机器人产业链"),
    "航天|卫星|火箭|北斗|空间|星网": ("商业航天","商业航天产业链"),
    "低空|无人机|eVTOL|通用航空|空域": ("低空经济","低空经济产业链"),
    "新能源|光伏|风电|储能|氢能|锂电|电力|电网|特高压": ("电力能源","新能源产业链"),
    "光纤|光缆|通信|5G|6G|网络|宽带": ("光通信","光通信产业链"),
    "液冷|数据中心|算力中心|IDC": ("液冷散热","数据中心散热产业链"),
    "新材料|碳纤维|树脂|硅微粉|铜箔|CCL|PCB|覆铜板": ("半导体材料","半导体材料产业链"),
    "新能源车|电动车|充电桩|智能驾驶|自动驾驶": ("马斯克生态","电动车产业链"),
    "光刻|封装|封测|晶圆|EDA": ("半导体材料","半导体制造产业链"),
}

def call_deepseek(prompt):
    data = json.dumps({"model":"deepseek-chat","messages":[{"role":"user","content":prompt}],"max_tokens":500,"temperature":0}).encode()
    req = urllib.request.Request(DS_URL, data=data, headers={"Content-Type":"application/json","Authorization":"Bearer "+DS_KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[API错误: {e}]"

def match_ecosystems(text):
    """匹配政策文本到生态"""
    matched = set()
    details = []
    for pattern, (eco_name, description) in ECO_MAP.items():
        if re.search(pattern, text, re.IGNORECASE):
            matched.add(eco_name)
            details.append(f"{eco_name}({description})")
    return list(matched), details

# 从国务院政策文件库抓取
print(f"🔍 政策监控 · {time.strftime('%Y-%m-%d')}")
print("=" * 60)

# 用新浪新闻API搜政策关键词
policies = []
topics = ["国务院政策","工信部政策","发改委政策","科技部政策","新质生产力","人工智能产业政策","机器人产业政策","低空经济政策"]

for topic in topics[:5]:
    encoded = urllib.parse.quote(topic)
    url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k={encoded}&num=3&page=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            for item in data.get("result",{}).get("data",[])[:2]:
                title = item.get("title","")
                if len(title) > 10 and title not in [p["title"] for p in policies]:
                    policies.append({"title":title,"url":item.get("url",""),"time":item.get("ctime",""),"source":"sina"})
    except: pass
    time.sleep(0.3)

print(f"抓取 {len(policies)} 条政策相关新闻\n")

# DeepSeek批量解读
if policies:
    titles_text = "\n".join(f"{i+1}. {p['title']}" for i,p in enumerate(policies[:8]))
    prompt = f"""你是政策分析师。分析以下政策新闻标题，判断每一条对中国A股哪些产业链有影响。

返回格式（只返回JSON，不要其他文字）:
[{{"id":序号,"impact":"利好/利空/中性","sector":"受影响的产业链","reason":"一句话解释"}}]

政策标题:
{titles_text}"""

    print("⏳ DeepSeek 解读中...")
    analysis = call_deepseek(prompt)
    print(analysis[:500])

    # Parse and match
    try:
        results = json.loads(re.findall(r'\[.*\]', analysis, re.DOTALL)[0])
        print(f"\n📋 政策解读结果:")
        for r in results:
            title = policies[r["id"]-1]["title"] if r["id"] <= len(policies) else ""
            matched, details = match_ecosystems(title + " " + r.get("sector",""))
            icon = {"利好":"🟢","利空":"🔴","中性":"⚪"}.get(r["impact"],"⚪")
            print(f"  {icon} {r['impact']} → {', '.join(details) if details else r.get('sector','?')}")
            if matched:
                print(f"     关联: {', '.join(matched)}")
            print(f"     {title[:80]}")
    except Exception as e:
        print(f"  解析失败: {e}")

    # Save
    output = {"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "policies": policies, "analysis": analysis}
    with open(os.path.join(DIR, "policy_alerts.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("\n✅ 已保存 policy_alerts.json")
else:
    print("未抓取到政策新闻")
