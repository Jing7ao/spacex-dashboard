# backtest_q2.py — 预测层方法论 Q2 验证：E1 vs 虚标，买入信号后的收益分层
# 规则来自预测层方法论 §十一 第三步：
#   E1/E2 + 评分≥65 + 主力流入 → 高确信
#   虚标 + 评分≥65 + 主力流入 → 中确信（仓位减半）
#   评分≥65 + 资金流出 → 诱多
# 本次验证聚焦：同样的"买入信号"条件下，E1 标的是否跑赢虚标？

import akshare as ak
import pandas as pd
import numpy as np
import json, sys, io, os, re
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ═══ 1. 加载标的元数据（从 predict.html 的 ECO_STOCKS 提取） ═══
DIR = r'c:\Users\13639\spacex-dashboard'

def load_stocks():
    """从 predict.html 提取所有标的及其 rn 字段"""
    with open(os.path.join(DIR, 'predict.html'), 'r', encoding='utf-8') as f:
        html = f.read()

    # 提取 ECO_STOCKS 中的股票数据
    stocks = []
    # 匹配每条 {c:'...',n:'...',rn:'...'}
    pattern = r"\{c:'(\d+)',n:'([^']+)',rn:'([^']+)'\}"
    seen = set()
    for m in re.finditer(pattern, html):
        code = m.group(1)
        if code in seen:
            continue
        seen.add(code)
        name = m.group(2)
        rn = m.group(3)

        # 证据分级（与预测层方法论 §Q2 一致）
        if '[E1]' in rn or '(年报/E1)' in rn:
            evidence = 'E1'
        elif '年报未提' in rn or '年报未称' in rn or '年报无' in rn or '年报未披露' in rn:
            evidence = '虚标'
        elif '[E2]' in rn or '(互动易)' in rn or 'E2产业链' in rn:
            evidence = 'E2'
        else:
            evidence = 'E3'

        stocks.append({'code': code, 'name': name, 'rn': rn, 'evidence': evidence})

    return stocks

# ═══ 2. 拉 K 线数据 ═══
def fetch_kline(code, days=400):
    """用 AKShare 拉日 K 线"""
    try:
        market = 'sh' if code.startswith(('6', '5')) else 'sz'
        symbol = market + code

        # 确定日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days + 50)).strftime('%Y%m%d')

        df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date, adjust='qfq')

        if df is None or len(df) == 0:
            return None

        # 标准化列名
        df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        return df
    except Exception as e:
        return None

# ═══ 3. 计算简化评分信号（替代完整的七维评分） ═══
# 预测层方法论 Q2 用"评分≥65"作为买入门槛
# 回测中用 RSI + 均线 + 量价关系近似评分信号

def compute_signals(df):
    """为每行计算简化信号"""
    if df is None or len(df) < 60:
        return df

    df = df.copy()

    # RSI(14)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df['rsi'] = 100 - (100 / (1 + rs))

    # MA5 / MA20
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()

    # 量比（当日量 / 20日均量）
    df['vol_ma20'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_ma20'].replace(0, np.nan)

    # 简化评分（0-100）
    # RSI 分数：30-70 最优，<20 超卖给高分，>80 超买给低分
    df['rsi_score'] = np.where(df['rsi'] < 20, 80,
                     np.where(df['rsi'] < 30, 65,
                     np.where(df['rsi'] < 70, 55,
                     np.where(df['rsi'] < 80, 35, 15))))

    # 均线分数：价格 > MA5 > MA20 多头排列
    df['ma_score'] = np.where((df['close'] > df['ma5']) & (df['ma5'] > df['ma20']), 75,
                     np.where(df['close'] > df['ma20'], 55,
                     np.where(df['close'] > df['ma5'], 40, 25)))

    # 综合评分（近似七维评分中的技术部分）
    df['signal_score'] = df['rsi_score'] * 0.4 + df['ma_score'] * 0.35 + np.minimum(df['vol_ratio'].fillna(1) * 15, 25)

    # 买入信号：评分 >= 65（对应预测层方法论 §Q2 阈值）
    df['buy_signal'] = df['signal_score'] >= 65

    return df

# ═══ 4. 按 Q2 规则验证：E1 vs 虚标 ═══
def backtest_q2(stocks):
    """核心验证：买入信号后 E1 vs 虚标的收益差异"""

    results = {'E1': [], 'E2': [], 'E3': [], '虚标': []}

    total = len(stocks)
    for i, s in enumerate(stocks):
        code = s['code']
        name = s['name']
        ev = s['evidence']

        sys.stdout.write(f'\r  {i+1}/{total} {name}({code}) {ev}...')
        sys.stdout.flush()

        df = fetch_kline(code)
        if df is None or len(df) < 60:
            continue

        df = compute_signals(df)

        # 找到所有买入信号日（评分>=65 且 前一日评分<65 → 首次触发）
        buy_days = df[(df['buy_signal']) & (~df['buy_signal'].shift(1).fillna(False))]

        for idx, row in buy_days.iterrows():
            day_idx = df.index.get_loc(idx)

            # 计算前向收益（5日/10日/20日）
            for horizon in [5, 10, 20]:
                future_idx = day_idx + horizon
                if future_idx < len(df):
                    fwd_return = (df.iloc[future_idx]['close'] - row['close']) / row['close'] * 100
                    results[ev].append({
                        'code': code, 'name': name, 'date': row['date'].strftime('%Y-%m-%d'),
                        'score': round(row['signal_score'], 1),
                        'rsi': round(row['rsi'], 1) if not pd.isna(row['rsi']) else None,
                        'horizon': horizon,
                        'fwd_return': round(fwd_return, 2),
                        'price': round(row['close'], 2)
                    })

    print()
    return results

# ═══ 5. 统计与输出 ═══
def analyze(results):
    print('\n' + '='*70)
    print('预测层方法论 Q2 验证：E1 vs 虚标 买入信号后收益分层')
    print('='*70)
    print()

    for ev in ['E1', 'E2', 'E3', '虚标']:
        data = results.get(ev, [])
        if not data:
            print(f'{ev}: 无信号数据')
            continue

        df = pd.DataFrame(data)

        print(f'{"─"*60}')
        print(f'【{ev}】 {len(df)} 个买入信号 ({df["code"].nunique()} 只标的)')
        print(f'{"─"*60}')

        for h in [5, 10, 20]:
            subset = df[df['horizon'] == h]['fwd_return']
            if len(subset) < 3:
                continue

            avg = subset.mean()
            median = subset.median()
            win_rate = (subset > 0).sum() / len(subset) * 100
            best = subset.max()
            worst = subset.min()

            print(f'  D+{h:2d}  |  平均 {avg:+6.2f}%  |  中位 {median:+6.2f}%  |  胜率 {win_rate:5.1f}%  |  最好 {best:+7.2f}%  |  最差 {worst:+7.2f}%  |  n={len(subset)}')

        print()

    # ═══ 核心对比：E1 vs 虚标 ═══
    print('='*70)
    print('核心对比：E1 vs 虚标')
    print('='*70)

    e1_data = results.get('E1', [])
    fake_data = results.get('虚标', [])

    if e1_data and fake_data:
        df_e1 = pd.DataFrame(e1_data)
        df_fake = pd.DataFrame(fake_data)

        print(f'\n{"指标":<15} {"E1(n="+str(len(df_e1)//3)+")":<25} {"虚标(n="+str(len(df_fake)//3)+")":<25} {"差值":<15}')
        print('-'*80)

        for h in [5, 10, 20]:
            e1_ret = df_e1[df_e1['horizon'] == h]['fwd_return']
            fake_ret = df_fake[df_fake['horizon'] == h]['fwd_return']

            if len(e1_ret) < 3 or len(fake_ret) < 3:
                continue

            diff = e1_ret.mean() - fake_ret.mean()
            e1_win = (e1_ret > 0).sum() / len(e1_ret) * 100
            fake_win = (fake_ret > 0).sum() / len(fake_ret) * 100

            print(f'D+{h:<2d} 平均收益    {e1_ret.mean():+6.2f}%{"":<19} {fake_ret.mean():+6.2f}%{"":<19} {diff:+6.2f}%')
            print(f'D+{h:<2d} 胜率        {e1_win:5.1f}%{"":<19} {fake_win:5.1f}%{"":<19} {e1_win-fake_win:+5.1f}%')
            print()

        # 综合判定
        e1_d20 = df_e1[df_e1['horizon'] == 20]['fwd_return']
        fake_d20 = df_fake[df_fake['horizon'] == 20]['fwd_return']

        if len(e1_d20) >= 3 and len(fake_d20) >= 3:
            diff_d20 = e1_d20.mean() - fake_d20.mean()
            print('='*70)
            if diff_d20 > 0:
                print(f'✅ Q2 验证通过：E1 标的 D+20 平均跑赢虚标 {diff_d20:.1f}%')
                print('   预测层方法论 §Q2 "E1→高确信，虚标→低确信" 的区分逻辑成立')
            else:
                print(f'❌ Q2 验证未通过：E1 标的 D+20 未跑赢虚标 (差值 {diff_d20:.1f}%)')
                print('   证据等级在买入信号后的收益预测中无区分力')
                print('   预测层可能需要降低 E1 vs 虚标的权重差异')
            print('='*70)

    # ═══ 信号频率检查 ═══
    print(f'\n信号统计：')
    for ev in ['E1', 'E2', 'E3', '虚标']:
        data = results.get(ev, [])
        if data:
            df = pd.DataFrame(data)
            stocks_n = df['code'].nunique()
            signals_n = len(df[df['horizon'] == 5])  # 只算一个 horizon
            per_stock = signals_n / stocks_n if stocks_n > 0 else 0
            print(f'  {ev}: {stocks_n} 只标的, {signals_n} 个信号, 每只平均 {per_stock:.1f} 次')

if __name__ == '__main__':
    print('预测层方法论 Q2 回测')
    print('正在加载标的元数据...')
    stocks = load_stocks()
    print(f'共 {len(stocks)} 只标的')

    e1_count = sum(1 for s in stocks if s['evidence'] == 'E1')
    e2_count = sum(1 for s in stocks if s['evidence'] == 'E2')
    e3_count = sum(1 for s in stocks if s['evidence'] == 'E3')
    fake_count = sum(1 for s in stocks if s['evidence'] == '虚标')
    print(f'  E1: {e1_count} | E2: {e2_count} | E3: {e3_count} | 虚标: {fake_count}')
    print()

    print('正在拉取K线数据并计算信号...')
    results = backtest_q2(stocks)

    analyze(results)

    # 保存结果
    out = {}
    for ev, data in results.items():
        if data:
            out[ev] = {
                'count': len([d for d in data if d['horizon'] == 5]),
                'stocks': len(set(d['code'] for d in data)),
                'd5_avg': round(pd.DataFrame([d for d in data if d['horizon'] == 5])['fwd_return'].mean(), 2) if data else None,
                'd10_avg': round(pd.DataFrame([d for d in data if d['horizon'] == 10])['fwd_return'].mean(), 2) if data else None,
                'd20_avg': round(pd.DataFrame([d for d in data if d['horizon'] == 20])['fwd_return'].mean(), 2) if data else None,
            }

    with open(os.path.join(DIR, 'backtest_q2_results.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'\n结果已保存到 backtest_q2_results.json')
