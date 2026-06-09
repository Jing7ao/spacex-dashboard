# check_volume.py — 量价健康度检查工具
# 用法: python check_volume.py [股票代码 ...]
#       python check_volume.py 603305 002466 300136        # 指定标的
#       python check_volume.py                             # 默认检查全部自选池
# 逻辑: 42号因子简化版 — 缩量涨=筹码稳定(看多) / 放量拉=游资出货(看空)

import json, urllib.request, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── 数据获取 ──────────────────────────────────────────────
def fetch_realtime(code):
    """腾讯实时行情"""
    m = "sh" if code.startswith(("6","5")) else "sz"
    url = f"http://qt.gtimg.cn/q={m}{code}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("gbk", errors="replace")
            # 解析: v_CODE="market~name~code~price~prev_close~..."
            parts = raw.split("~")
            if len(parts) < 10:
                return None
            return {
                "name": parts[1],
                "price": float(parts[3]),
                "prev": float(parts[4]),
                "vol": float(parts[6]),
            }
    except:
        return None

def fetch_avg_vol(code, days=20):
    """腾讯K线 → 近N日均量"""
    m = "sh" if code.startswith(("6","5")) else "sz"
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,{days+1},qfq"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data", {}).get(f"{m}{code}", {}).get("day", []) or
                      data.get("data", {}).get(f"{m}{code}", {}).get("qfqday", []))
            if klines and len(klines) > 1:
                vols = [float(k[5]) for k in klines[-(days+1):-1] if len(k) > 5]
                if vols:
                    return sum(vols) / len(vols)
    except:
        pass
    return None

# ── 量价分类 ──────────────────────────────────────────────
def classify(chg_pct, vol_ratio):
    """返回 (信号标签, 风险等级)"""
    if chg_pct > 2 and vol_ratio < 0.8:
        return "缩量涨·筹码稳定", "LOW"
    elif chg_pct > 2 and vol_ratio > 1.5:
        return "放量拉·游资出货", "HIGH"
    elif chg_pct < -2 and vol_ratio > 1.5:
        return "放量跌·恐慌出清", "MID"
    elif chg_pct < -2 and vol_ratio < 0.8:
        return "缩量跌·无人接盘", "HIGH"
    elif vol_ratio > 1.5:
        return "放量异动·偏空", "MID"
    elif vol_ratio < 0.5:
        return "极度缩量·关注", "MID"
    else:
        return "正常", "LOW"

# ── 主逻辑 ────────────────────────────────────────────────
def main(codes):
    results = []
    for code in codes:
        rt = fetch_realtime(code)
        if not rt:
            print(f"  {code}: 行情获取失败")
            continue
        avg = fetch_avg_vol(code) or rt["vol"]
        vr = rt["vol"] / avg if avg > 0 else 1.0
        chg = (rt["price"] - rt["prev"]) / rt["prev"] * 100
        sig, risk = classify(chg, vr)
        results.append({**rt, "code": code, "chg": chg, "vr": vr, "sig": sig, "risk": risk})

    if not results:
        print("无有效数据")
        return

    # 输出
    print()
    print("═" * 80)
    print("  量价健康度检查  |  缩量涨=筹码稳定  |  放量拉=游资出货  |  量比=今日量/20日均量")
    print("═" * 80)
    print(f"  {'标的':<8} {'价格':>8} {'涨跌':>7} {'量比':>6}  {'信号':<22} 风险")
    print("─" * 80)

    for d in sorted(results, key=lambda x: x["vr"], reverse=True):
        risk_icon = {"HIGH":"🔴","MID":"🟡","LOW":"🟢"}.get(d["risk"],"⚪")
        print(f"  {d['name']:<8} {d['price']:>8.2f} {d['chg']:>+6.2f}% {d['vr']:>5.1f}x  {d['sig']:<22} {risk_icon}")

    print("─" * 80)

    # 异常汇总
    alerts = [d for d in results if d["risk"] in ("HIGH","MID")]
    if alerts:
        print(f"\n  ⚠ {len(alerts)} 只异常:")
        for d in alerts:
            icon = {"HIGH":"🔴","MID":"🟡"}[d["risk"]]
            print(f"  {icon} {d['name']}({d['code']}): {d['sig']} | 涨跌{d['chg']:+.1f}% | 量比{d['vr']:.1f}x")
    else:
        print(f"\n  ✓ {len(results)} 只标的全数量价正常")
    print()

# ── 默认自选池 ────────────────────────────────────────────
DEFAULT = [
    "603305","002466","300136","002281","600522","600089",
    "688333","300346","600869","300408","688268","300395"
]

if __name__ == "__main__":
    codes = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT
    # 去重去空格
    codes = [c.strip() for c in codes if c.strip()]
    main(codes)
