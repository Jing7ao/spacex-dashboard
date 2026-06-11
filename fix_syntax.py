# fix_syntax.py — 检查 monitor.html JS 语法并尝试自动修复
import re, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(DIR, "monitor.html")

with open(FILE, encoding='utf-8') as f:
    html = f.read()

# 提取内联JS
start = html.index('<script>', 200) + 8
end = html.index('</script>', start)
js = html[start:end]

lines = js.split('\n')
print(f"JS: {len(lines)} 行, {len(js)} 字符")
print(f"括号: {{{js.count('{')}}} vs {'}'}{js.count('}')} = {js.count('{')-js.count('}')}")
print(f"圆括号: ({js.count('(')} vs ){js.count(')')} = {js.count('(')-js.count(')')}")

# 逐行检查深度变化
depth = 0
issues = []
for i, line in enumerate(lines, 1):
    prev = depth
    for ch in line:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
    # 只在函数/块级别记录大幅跳跃
    line_opens = line.count('{') - line.count('}')

# 输出最后50行的深度变化
print(f"\n最后50行深度追踪:")
depth = 0
for i in range(max(0, len(lines)-50), len(lines)):
    line = lines[i]
    line_opens = line.count('{') - line.count('}')
    depth += line_opens
    if line.strip():
        print(f"  L{i+1}: d={depth} ({line_opens:+d}) {line.strip()[:100]}")

# 检查 try/catch 匹配
tries = len(re.findall(r'\btry\s*\{', js))
catches = len(re.findall(r'\bcatch\s*\(', js))
print(f"\ntry: {tries}, catch: {catches} (差值 {tries-catches}, Promise.catch不计在内)")

# 保存提取的JS供外部检查
with open(os.path.join(DIR, "_check.js"), 'w', encoding='utf-8') as f:
    f.write(js)
print(f"\n提取的JS已保存到 _check.js，可运行: node --check _check.js")
