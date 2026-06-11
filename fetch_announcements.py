# fetch_announcements.py — 公告监控（使用东方财富个股公告页链接——手动查看）
# API已失效，改为生成公告页链接列表，配合面板快速跳转
import sys, io, json, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

CODES = ["300136","002149","601689","002050","603305","688017","300476","601138","300308",
         "300394","002463","300502","002837","002851","600584","688102","300395","300346",
         "688268","300750","300476","002281","688012","600487","600522","002916"]

links = [{"code":c, "url":f"https://data.eastmoney.com/notices/stock/{c}.html"} for c in CODES]
output = {"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "links": links, "note": "公告API已失效，请手动点击链接查看。每个面板卡片也有📋公告按钮。"}

with open(os.path.join(DIR, "announcement_alerts.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ 已生成 {len(links)} 只标的公告页链接 (announcement_alerts.json)")
print("提示: 面板卡片上已有📋公告按钮，点击即可跳转。")
