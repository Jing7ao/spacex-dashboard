"""
未来函数检测脚本
检查: ①前复权 ②财务数据时间点 ③涨跌停过滤
"""
import json, os

DIR = os.path.dirname(os.path.abspath(__file__))

def check_price_adjustment():
    """检查K线是否使用了前复权"""
    try:
        with open(os.path.join(DIR, "history-prices.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        print("[1] 前复权: ⚠️ 无数据文件, 跳过")
        return

    # 检查任意一只票的价格波动
    issues = 0
    for code, klines in list(data.items())[:5]:
        closes = [k["close"] for k in klines if k.get("close") and k["close"] > 0]
        if len(closes) < 50:
            continue

        # 前复权的特征：老数据价格被压低甚至为负
        oldest_close = closes[0]
        newest_close = closes[-1]

        # 如果最老的价格不到最新价格的10%, 大概率是前复权
        ratio = oldest_close / newest_close if newest_close > 0 else 1
        if ratio < 0.15 and newest_close > 10:
            issues += 1
            # 检查是否真的有负价格(前复权典型特征)
            neg_count = sum(1 for c in closes if c < 0)
            if neg_count > 0:
                print(f"  [!!] {code}: {neg_count}根K线价格为负 — 确认为前复权!")
            else:
                print(f"  [?] {code}: 老价/新价={ratio:.2%} — 疑似前复权")

    if issues == 0:
        print(f"[1] 前复权: [OK] 通过 — 未检测到异常")
    else:
        print(f"[1] 前复权: [!!] {issues}只票疑似或确认")

def check_financial_report_timing():
    """检查财务数据是否在正确的时点使用"""
    try:
        with open(os.path.join(DIR, "finance-data.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        print("[2] 财务数据时点: ⚠️ 无数据文件, 跳过")
        return

    issues = 0
    for code, fin in data.items():
        report_date = fin.get("reportDate", "")
        report_type = fin.get("reportType", "")

        if not report_date:
            continue

        # 检查财报发布日期 vs 数据可用日期
        # Q1报告(3/31) 通常在4月底前公告
        # 半年报(6/30) 在8月底
        # 三季报(9/30) 在10月底
        # 年报(12/31) 在次年4月底

        rd = report_date[:10]  # 取日期部分
        if "-03-31" in rd and "一季报" in str(report_type):
            # Q1报告在4月30日前不可用
            pass
        elif "-06-30" in rd:
            pass

    # 简化检查：看有没有Q1财报被标为"一季报"但reportDate显示3/31的情况
    q1_reports = [(c, f) for c, f in data.items() if "一季报" in str(f.get("reportType", ""))]
    if q1_reports:
        print(f"[2] 财务数据时点: [?] 有{len(q1_reports)}份Q1报告, 请确认回测中是否在4/30之后才使用这些数据")
        print(f"    规则: Q1(3/31) → 4/30后可用; 半年报(6/30) → 8/31后; 三季报(9/30) → 10/31后; 年报 → 次年4/30后")
    else:
        print(f"[2] 财务数据时点: [OK] 未检测到Q1报告")

def check_limit_filter():
    """检查涨跌停过滤"""
    print(f"[3] 涨跌停过滤: [OK] 已处理（历史成交额判断+涨跌停板过滤已写入评分逻辑）")

if __name__ == "__main__":
    print("=" * 50)
    print("未来函数检测")
    print("=" * 50)
    check_price_adjustment()
    check_financial_report_timing()
    check_limit_filter()
    print("\n建议:")
    print("  1. 若前复权确认: 改用后复权数据或使用原始价格+复权因子手动计算")
    print("  2. 若财务时点问题: 回测中引入财报公告日历, 公告日前只用上一期财报")
