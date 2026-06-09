"""合并 monitor.html 导航分类: 22 -> 8"""
import re, json

with open("monitor.html", "r", encoding="utf-8") as f:
    content = f.read()

# 找 WATCH 对象的位置
start = content.find("var WATCH={")
end = content.find("};\n\n//", start)  # find end of WATCH
if end == -1:
    end = content.find("};\n\nvar PARAMS", start)
if end == -1:
    print("Cannot find WATCH object end")
    exit(1)

# 提取WATCH内容
watch_block = content[start:end+2]
print(f"WATCH block: {len(watch_block)} chars")

# 合并方案
MERGE = {
    "英伟达全链": ["nvidia", "optical", "semimat", "cooling"],  # 英伟达供应链
    "马斯克生态": ["musk"],  # 不变
    "算力基础设施": ["power", "datacenter", "idc", "subcable"],
    "半导体与光通信": ["chip", "optical"],  # optical独立副本
    "机器人": ["robot_domestic"],
    "商业航天": ["space", "space_domestic"],
    "新能源与储能": ["newenergy", "storage"],
    "自选与更多": ["custom", "consumer", "env", "ai", "ai_domestic", "cxmt", "lowalt_domestic"],
}

# 提取每个类别的watchlist
import ast
# Parse the watch block as JavaScript-like dictionary
# Simple regex approach
def extract_watchlist(name_key):
    """Extract watchlist array for a given category key"""
    pattern = rf'{name_key}:\{{name:\'[^\']+\',watchlist:\[(.*?)\],etfs:\[(.*?)\]\}}'
    match = re.search(pattern, watch_block, re.DOTALL)
    if match:
        stocks_str = "[" + match.group(1) + "]"
        etfs_str = "[" + match.group(2) + "]"
        # Count stocks
        stock_count = len(re.findall(r"\{c:", stocks_str))
        return stock_count
    return 0

# Count stocks per merged category
total = 0
for cat_name, sources in MERGE.items():
    count = 0
    for src in sources:
        c = extract_watchlist(src)
        count += c
    total += count
    print(f"  {cat_name}: {count} stocks (from {sources})")
print(f"  Total: {total}")

# Build new WATCH object
new_watch = "var WATCH={\n"
keys = {
    "英伟达全链": "nvidia_full",
    "马斯克生态": "musk",
    "算力基础设施": "compute",
    "半导体与光通信": "chip_optical",
    "机器人": "robot",
    "商业航天": "space_all",
    "新能源与储能": "energy_all",
    "自选与更多": "custom_all",
}
icons = {
    "英伟达全链": "🔷", "马斯克生态": "⚡", "算力基础设施": "🏗️",
    "半导体与光通信": "🔗", "机器人": "🤖", "商业航天": "🚀",
    "新能源与储能": "🔋", "自选与更多": "⭐",
}

for cat_name, sources in MERGE.items():
    key = keys[cat_name]
    icon = icons[cat_name]
    new_watch += f'  {key}:{{name:\'{icon} {cat_name}\',watchlist:[\n'

    # Collect stocks from all source categories
    all_stocks = []
    all_etfs = []
    seen_codes = set()

    for src in sources:
        # Extract watchlist
        pattern = rf'{src}:\{{name:\'[^\']+\',watchlist:\[(.*?)\],etfs:\[(.*?)\]\}}'
        match = re.search(pattern, watch_block, re.DOTALL)
        if match:
            stocks_str = match.group(1).strip()
            etfs_str = match.group(2).strip()

            # Extract individual stock entries
            stock_entries = re.findall(r'\{[^}]+\}', stocks_str)
            for se in stock_entries:
                # Extract code to deduplicate
                code_match = re.search(r"c:'(\d+)'", se)
                s_match = re.search(r"s:'([^']+)'", se)
                if code_match:
                    code = code_match.group(1)
                    if code not in seen_codes:
                        seen_codes.add(code)
                        all_stocks.append(se)
                elif s_match:
                    sym = s_match.group(1)
                    if sym not in seen_codes:
                        seen_codes.add(sym)
                        all_stocks.append(se)
                else:
                    all_stocks.append(se)

            # Extract ETF entries
            etf_entries = re.findall(r'\{[^}]+\}', etfs_str)
            for ee in etf_entries:
                if ee not in all_etfs:
                    all_etfs.append(ee)

    # Write stocks
    for i, s in enumerate(all_stocks):
        comma = "," if i < len(all_stocks)-1 else ""
        new_watch += f"    {s}{comma}\n"

    new_watch += "  ],etfs:["
    for i, e in enumerate(all_etfs):
        comma = "," if i < len(all_etfs)-1 else ""
        new_watch += f"{e}{comma}"
    new_watch += "]},\n"

new_watch += "};\n"

print(f"\nNew WATCH: {len(new_watch)} chars")
print("Write to monitor_merged.html for review...")
with open("monitor_merged.html", "w", encoding="utf-8") as f:
    f.write(new_watch)
print("Done. Review monitor_merged.html before applying.")
