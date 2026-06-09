"""
PPO（概率过拟合指标）检测
核心逻辑：把历史收益标签随机打乱，看策略信号还能不能"预测"打乱后的收益。
如果打乱后策略表现不打折 → 信号没有预测能力，只是拟合噪声。

数据来源: history-prices.json (31只 × 100根K线)
用法: python ppo_test.py
"""
import json, random, math, os

DIR = os.path.dirname(os.path.abspath(__file__))


def load_signals_and_returns():
    """
    从K线数据构造:
    - signal: RSI近似（过去5日涨跌幅的z-score，越大越超买）
    - label: 未来5日实际收益
    """
    path = os.path.join(DIR, "history-prices.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for code, klines in data.items():
        closes = [k["close"] for k in klines if k.get("close")]
        if len(closes) < 30:
            continue
        for i in range(25, len(closes) - 5):
            # 信号：过去5日涨跌幅（负=超卖，正=超买）
            ret_5d_past = (closes[i] - closes[i - 5]) / closes[i - 5]
            # 过去10日波动率（用于归一化）
            past_rets = [(closes[j] - closes[j - 1]) / closes[j - 1] for j in range(i - 9, i + 1)]
            volatility = (sum((r - sum(past_rets) / 10) ** 2 for r in past_rets) / 9) ** 0.5
            signal = ret_5d_past / (volatility + 0.001)  # 归一化信号

            # 标签：未来5日实际收益
            label = (closes[i + 5] - closes[i]) / closes[i]

            records.append({
                "code": code,
                "idx": i,
                "signal": signal,
                "label": label,
            })
    return records


def backtest_with_signals(records, signals, labels):
    """
    用给定信号选前20%做多，计算夏普和胜率
    """
    paired = list(zip(signals, labels, [r["code"] for r in records]))
    threshold = sorted(signals)[int(len(signals) * 0.2)]  # 最低20% = 超卖
    selected = [p for p in paired if p[0] <= threshold]
    returns = [p[1] for p in selected]
    return calc_stats(returns)


def calc_stats(returns):
    n = len(returns)
    if n < 5:
        return {"sharpe": 0, "win_rate": 0.5, "mean_ret": 0, "n": n}
    mean_ret = sum(returns) / n
    std = (sum((r - mean_ret) ** 2 for r in returns) / (n - 1)) ** 0.5
    sharpe = (mean_ret / std) * math.sqrt(252 / 5) if std > 0 else 0
    win_rate = sum(1 for r in returns if r > 0) / n
    return {
        "sharpe": round(sharpe, 3),
        "win_rate": round(win_rate, 3),
        "mean_ret": round(mean_ret, 5),
        "n": n,
    }


def ppo_test(N=200):
    records = load_signals_and_returns()
    signals = [r["signal"] for r in records]
    labels = [r["label"] for r in records]

    print(f"=== PPO Overfitting Detection ===")
    print(f"Records: {len(records)} (31 stocks x ~100 K-lines)")

    # 原始表现
    orig = backtest_with_signals(records, signals, labels)
    print(f"\nOriginal strategy (buy oversold, lowest 20% signal):")
    print(f"  Win Rate: {orig['win_rate']:.1%}  Sharpe: {orig['sharpe']}  Mean ret: {orig['mean_ret']:.4%}  N: {orig['n']}")

    # 打乱标签测试
    random.seed(42)
    ppo_count = 0
    shuffled_stats = []

    for i in range(N):
        shuffled = labels[:]
        random.shuffle(shuffled)
        ss = backtest_with_signals(records, signals, shuffled)
        shuffled_stats.append(ss)
        if ss["sharpe"] > orig["sharpe"] and ss["win_rate"] > orig["win_rate"]:
            ppo_count += 1

    avg_sh = sum(s["sharpe"] for s in shuffled_stats) / N
    max_sh = max(s["sharpe"] for s in shuffled_stats)
    ppo = ppo_count / N
    sharpe_drop = (orig["sharpe"] - avg_sh) / abs(orig["sharpe"]) if orig["sharpe"] != 0 else 0

    print(f"\nShuffled test ({N} times):")
    print(f"  Average Sharpe: {avg_sh:.3f} (original: {orig['sharpe']})")
    print(f"  Max Sharpe: {max_sh:.3f}")
    print(f"  Sharpe drop: {sharpe_drop:.0%}")
    print(f"  PPO (beat original): {ppo:.1%}")

    # 判定
    max_beats = max(ppo, 1 - ppo)  # 看打乱后是更好还是更差，取极端
    if ppo > 0.9:
        verdict = "REVERSED - Signal predicts the OPPOSITE. Try flipping buy/sell."
    elif sharpe_drop > 0.5 and ppo < 0.1:
        verdict = "PASS - Signal has real predictive power. Shuffling destroys it."
    elif sharpe_drop > 0.3:
        verdict = "WARN - Some overfitting. Add cross-validation before going live."
    elif sharpe_drop > 0.1:
        verdict = "FAIL - Signal is barely better than noise."
    else:
        verdict = "NOISE - Signal has no predictive power above random."

    print(f"\nVerdict: {verdict}")
    print(f"\nHow to use PPO with YOUR strategy:")
    print(f"  1. Replace 'signal' in load_signals_and_returns() with YOUR panel's score")
    print(f"  2. Keep 'label' as future 5-day return")
    print(f"  3. PPO < 10% + big sharpe drop = your strategy found real alpha")
    return {"ppo": ppo, "orig": orig, "sharpe_drop": sharpe_drop}


if __name__ == "__main__":
    ppo_test(N=200)
