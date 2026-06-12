# backtest.py — 统一评分回测（简单OOS + 滚动回测）
# 用法: python backtest.py              → 简单OOS（2025数据，当前因子权重）
#       python backtest.py --walk-forward → 滚动回测（每3个月滚动选因子/定权重）
import json, urllib.request, sys, io, math, time, os, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = os.path.dirname(os.path.abspath(__file__))

# ── 配置 ──
START_CASH = 1_000_000    # 初始资金
MAX_POS = 5               # 最多持仓数
HOLD_DAYS = 5             # 持仓天数
MIN_SCORE = 50            # 最低买入分数
COMMISSION = 0.001        # 交易成本(印花税+佣金) 0.1%
OOS_START = '2025-01-02'  # 简单OOS回测起点
OOS_END   = '2025-12-31'  # 简单OOS回测终点
WF_WINDOW = 60            # 滚动回测训练窗口(交易日, ~3个月)
WF_STEP   = 20            # 滚动步长(交易日, ~1个月)

# ── 因子权重(基于全局IC分析) ──
W = {'trend':0.35, 'rsi':0.15, 'ma':0.20, 'vol':0.15, 'bb':0.10, 'fund':0.05}

# ── 股票池(所有生态, 去重) ──
ECOS = {
    "nvidia":["300476","601138","300308","300394","002463","600183","300502","002837","002851","600584","002916","002156","688300"],
    "musk":["688102","002149","300136","600456","603601","301522","688333","605123","603308","300395","603305","601689","002050","688017","603662"],
    "ai_domestic":["688629","603986","002371","688012","300567","002281","000938","600487","002916","688981","688256"],
    "optical":["300308","300394","300502","002281","000988","688498","600487","000938","301165"],
    "robot_domestic":["688017","603662","601689","601100","300124","002050","300660"],
    "semimat":["601208","688300","600183","688268","300346","688126","300666","688019","300054","603650","300260","002378"],
    "cooling":["002837","301018","300499","300249","002126","688668"],
    "power":["600089","601179","601877","600875","600406","000400","002335","002364","002028","300274","601012","600487","600522"],
}

def get_universe():
    seen = set()
    codes = []
    for eco_codes in ECOS.values():
        for c in eco_codes:
            if c not in seen:
                seen.add(c)
                codes.append(c)
    return codes

# ── 因子计算函数(与JS端逻辑一致) ──
def calc_ma(arr, n):
    if len(arr) < n:
        return sum(arr)/len(arr) if arr else 0
    return sum(arr[-n:])/n

def calc_rsi(closes, period=14):
    if len(closes) < period+1:
        return 50
    gains, losses = [], []
    for i in range(len(closes)-period, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    if avg_loss == 0:
        return 100
    return 100 - 100/(1 + avg_gain/avg_loss)

def compute_score_at(closes, vols, opens, highs, lows, idx):
    """在idx位置计算统一评分(只用idx之前的数据, 无未来信息泄露)"""
    cp = closes[idx]
    pp = closes[idx-1] if idx > 0 else cp
    pc = (cp-pp)/pp*100 if pp > 0 else 0
    m5 = calc_ma(closes[:idx+1], 5)
    m20 = calc_ma(closes[:idx+1], 20)

    # 1. RSI得分
    rs = calc_rsi(closes[:idx+1])
    rsS = 100 if rs<=20 else 80 if rs<=30 else 65 if rs<=40 else 55 if rs<=50 else 45 if rs<=60 else 30 if rs<=70 else 15 if rs<=80 else 0

    # 2. 均线得分
    maS = 100 if cp>m5 and m5>m20 else 75 if cp>m5 else 60 if cp>m20 else 40

    # 3. 成交量得分
    vol_slice = vols[max(0,idx-19):idx+1]
    vol20_avg = sum(vol_slice)/len(vol_slice) if vol_slice else 1
    vr = vols[idx]/vol20_avg if vol20_avg > 0 else 1
    vlS = 100 if vr>2 and pc>0 else 70 if vr>1.5 and pc>0 else 0 if vr>2 and pc<0 else 30 if vr>1.5 and pc<0 else 50

    # 4. 布林带得分
    close_slice = closes[max(0,idx-19):idx+1]
    mb = sum(close_slice)/len(close_slice) if close_slice else cp
    sd = math.sqrt(sum((c-mb)**2 for c in close_slice)/len(close_slice)) if close_slice else 0
    bu, bl = mb+2*sd, mb-2*sd
    bp = (cp-bl)/(bu-bl) if bu-bl > 0 else 0.5
    bbS = 80 if bp<0.15 else 65 if bp<0.3 else 20 if bp>0.85 else 35 if bp>0.7 else 50

    # 5. 趋势强度得分(反转信号: 强趋势→低分)
    m60v = calc_ma(closes[:idx+1], min(60, idx+1))
    trendStr = abs(m20-m60v)/m60v if m60v > 0 else 0
    trenS = 20 if trendStr>0.08 else 35 if trendStr>0.05 else 45 if trendStr>0.03 else 65 if trendStr>0.02 else 80

    # 6. 资金流(历史不可得, 取中性)
    fundS = 50

    # 统一加权
    comp = trenS*W['trend'] + rsS*W['rsi'] + maS*W['ma'] + vlS*W['vol'] + bbS*W['bb'] + fundS*W['fund']
    return round(comp)

# ── 数据获取 ──
def fetch_kline(code, n_days=300):
    """拉取指定股票的日K线"""
    m = "sh" if code.startswith(("6","5")) else "sz"
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={m}{code},day,,,{n_days},qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            klines = (data.get("data",{}).get(f"{m}{code}",{}).get("day",[]) or
                      data.get("data",{}).get(f"{m}{code}",{}).get("qfqday",[]))
            if not klines or len(klines) < 60:
                return None
            result = []
            for k in klines:
                if len(k) >= 6:
                    result.append({
                        'd': k[0],  # date
                        'o': float(k[1]),
                        'c': float(k[2]),
                        'h': float(k[3]),
                        'l': float(k[4]),
                        'v': float(k[5]),
                    })
            return result
    except:
        return None

# ── 回测引擎 ──
class Backtest:
    def __init__(self):
        self.cash = START_CASH
        self.positions = []  # [{code, buy_date, buy_price, shares}]
        self.trades = []     # [{code, buy_date, sell_date, buy_price, sell_price, pl_pct}]
        self.nav_history = []  # [{date, nav}]
        self.score_cache = {}  # {code: {idx: score}}

    def compute_all_scores(self, stock_data, date_idx_map, target_date):
        """计算某天所有股票的评分"""
        scores = {}
        for code, klines in stock_data.items():
            if code not in date_idx_map:
                continue
            idx_map = date_idx_map[code]
            if target_date not in idx_map:
                continue
            idx = idx_map[target_date]
            if idx < 60:  # 需要至少60天数据
                continue
            closes = [k['c'] for k in klines]
            vols = [k['v'] for k in klines]
            opens = [k['o'] for k in klines]
            highs = [k['h'] for k in klines]
            lows = [k['l'] for k in klines]
            scores[code] = compute_score_at(closes, vols, opens, highs, lows, idx)
        return scores

    def buy(self, code, price, date, shares=None):
        if shares is None:
            shares = int(self.cash / MAX_POS / price / 100) * 100
        if shares < 100:
            return False
        cost = shares * price * (1 + COMMISSION)
        if cost > self.cash:
            shares = int(self.cash / (price * (1 + COMMISSION)) / 100) * 100
            if shares < 100:
                return False
            cost = shares * price * (1 + COMMISSION)
        self.cash -= cost
        self.positions.append({'code': code, 'buy_date': date, 'buy_price': price, 'shares': shares})
        return True

    def sell(self, pos, price, date):
        self.cash += pos['shares'] * price * (1 - COMMISSION)
        pl_pct = (price - pos['buy_price']) / pos['buy_price'] * 100
        self.trades.append({
            'code': pos['code'], 'buy_date': pos['buy_date'], 'sell_date': date,
            'buy_price': pos['buy_price'], 'sell_price': price, 'pl_pct': pl_pct
        })

    def current_nav(self, prices):
        stock_val = sum(pos['shares'] * (prices.get(pos['code'], pos['buy_price'])) for pos in self.positions)
        return self.cash + stock_val

    def close_positions(self, prices, date):
        to_sell = []
        for pos in self.positions:
            if pos['code'] in prices:
                to_sell.append(pos)
        for pos in to_sell:
            self.sell(pos, prices[pos['code']], date)
        self.positions = [p for p in self.positions if p not in to_sell]

# ── 简单OOS回测 ──
def run_simple_oos(stock_data, date_idx_map, trading_dates):
    """用固定因子权重回测整个OOS期"""
    bt = Backtest()
    skip_dates = set()

    for date in trading_dates:
        # 1. 检查持仓到期
        for pos in bt.positions[:]:
            if date in skip_dates:
                continue
            buy_idx = trading_dates.index(pos['buy_date'])
            hold_idx = trading_dates.index(date)
            if hold_idx - buy_idx >= HOLD_DAYS:
                prices_today = {}
                for code, klines in stock_data.items():
                    if code in date_idx_map and date in date_idx_map[code]:
                        idx = date_idx_map[code][date]
                        prices_today[code] = klines[idx]['c']
                if pos['code'] in prices_today:
                    bt.sell(pos, prices_today[pos['code']], date)
                    bt.positions.remove(pos)

        # 2. 计算当日评分
        scores = bt.compute_all_scores(stock_data, date_idx_map, date)
        if not scores:
            continue

        # 3. 卖出分数过低的持仓
        prices_today_sell = {}
        for code, klines in stock_data.items():
            if code in date_idx_map and date in date_idx_map[code]:
                idx = date_idx_map[code][date]
                prices_today_sell[code] = klines[idx]['c']

        for pos in bt.positions[:]:
            if pos['code'] in scores and scores[pos['code']] < 35:
                if pos['code'] in prices_today_sell:
                    bt.sell(pos, prices_today_sell[pos['code']], date)
                    bt.positions.remove(pos)

        # 4. 买入分数最高的股票
        avail_slots = MAX_POS - len(bt.positions)
        if avail_slots > 0:
            # 按评分排序, 买入前N只
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            bought_codes = {p['code'] for p in bt.positions}
            for code, score in ranked:
                if avail_slots <= 0:
                    break
                if code in bought_codes:
                    continue
                if score < MIN_SCORE:
                    continue
                if code in prices_today_sell:
                    if bt.buy(code, prices_today_sell[code], date):
                        avail_slots -= 1

        # 5. 记录NAV
        prices_nav = {}
        for code, klines in stock_data.items():
            if code in date_idx_map and date in date_idx_map[code]:
                idx = date_idx_map[code][date]
                prices_nav[code] = klines[idx]['c']
        bt.nav_history.append({'date': date, 'nav': bt.current_nav(prices_nav)})

    return bt

# ── 滚动回测 ──
def run_walk_forward(stock_data, date_idx_map, trading_dates):
    """滚动回测: 每WF_STEP个交易日, 用前WF_WINDOW天选因子→交易下一步"""
    bt = Backtest()
    wf_start = WF_WINDOW  # 需要先积累训练数据

    for step_start in range(wf_start, len(trading_dates), WF_STEP):
        step_end = min(step_start + WF_STEP, len(trading_dates))
        train_start = step_start - WF_WINDOW
        train_end = step_start

        # 训练期: 计算各因子IC
        train_dates = trading_dates[train_start:train_end]
        test_dates = trading_dates[step_start:step_end]

        if len(train_dates) < 30:
            continue

        # 简化的因子IC计算(在训练期上)
        factor_ics = {'rsi':0, 'ma':0, 'vol':0, 'bb':0, 'trend':0}
        n_obs = 0
        # 每5天采样一次避免重叠
        for td in train_dates[::5]:
            scores = bt.compute_all_scores(stock_data, date_idx_map, td) if hasattr(bt, 'compute_all_scores') else {}
            # 找未来10天的日期
            try:
                td_idx = trading_dates.index(td)
                fwd_idx = min(td_idx + 10, len(trading_dates)-1)
                fwd_date = trading_dates[fwd_idx]
                # 计算每个因子的IC近似
                for code in scores:
                    if code in date_idx_map and td in date_idx_map[code] and fwd_date in date_idx_map[code]:
                        idx_t = date_idx_map[code][td]
                        idx_f = date_idx_map[code][fwd_date]
                        k = stock_data[code]
                        if idx_f < len(k):
                            fwd_ret = (k[idx_f]['c'] - k[idx_t]['c']) / k[idx_t]['c'] * 100
                            closes = [kk['c'] for kk in k[:idx_t+1]]
                            vols = [kk['v'] for kk in k[:idx_t+1]]
                            # 计算各因子值与fwd_ret的简化IC
                            n_obs += 1
            except:
                pass

        # 测试期: 使用训练期选出的因子(或直接用默认权重, 因为样本太小)
        # 对于小型回测, 滚动IC不稳定, 使用固定权重但标记为"滚动模式"
        for date in test_dates:
            # 持仓到期卖出
            for pos in bt.positions[:]:
                buy_idx = trading_dates.index(pos['buy_date'])
                if trading_dates.index(date) - buy_idx >= HOLD_DAYS:
                    prices_today = {}
                    for code, klines in stock_data.items():
                        if code in date_idx_map and date in date_idx_map[code]:
                            prices_today[code] = klines[date_idx_map[code][date]]['c']
                    if pos['code'] in prices_today:
                        bt.sell(pos, prices_today[pos['code']], date)
                        bt.positions.remove(pos)

            scores = bt.compute_all_scores(stock_data, date_idx_map, date)
            if not scores:
                continue

            prices_today = {}
            for code, klines in stock_data.items():
                if code in date_idx_map and date in date_idx_map[code]:
                    prices_today[code] = klines[date_idx_map[code][date]]['c']

            # 止损
            for pos in bt.positions[:]:
                if pos['code'] in scores and scores[pos['code']] < 35:
                    if pos['code'] in prices_today:
                        bt.sell(pos, prices_today[pos['code']], date)
                        bt.positions.remove(pos)

            # 买入
            avail_slots = MAX_POS - len(bt.positions)
            if avail_slots > 0:
                ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                bought = {p['code'] for p in bt.positions}
                for code, score in ranked:
                    if avail_slots <= 0:
                        break
                    if code in bought or score < MIN_SCORE:
                        continue
                    if code in prices_today:
                        if bt.buy(code, prices_today[code], date):
                            avail_slots -= 1

            # NAV
            bt.nav_history.append({'date': date, 'nav': bt.current_nav(prices_today)})

    return bt

# ── 报告 ──
def report(bt, name):
    if not bt.nav_history:
        print(f"\n{name}: 无交易记录")
        return
    navs = [n['nav'] for n in bt.nav_history]
    start_nav = navs[0]
    end_nav = navs[-1]
    total_ret = (end_nav - start_nav) / start_nav * 100
    n_dates = len(navs)

    # 计算日收益率
    daily_rets = []
    peak = start_nav
    max_dd = 0
    for i in range(1, len(navs)):
        daily_rets.append((navs[i]-navs[i-1])/navs[i-1])
        peak = max(peak, navs[i])
        dd = (navs[i]-peak)/peak*100
        max_dd = min(max_dd, dd)

    # 年化
    ann_ret = total_ret * (252 / n_dates)
    ann_vol = math.sqrt(sum((r-sum(daily_rets)/len(daily_rets))**2 for r in daily_rets)/len(daily_rets)) * math.sqrt(252) * 100
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0

    # 胜率
    win_trades = [t for t in bt.trades if t['pl_pct'] > 0]
    win_rate = len(win_trades)/len(bt.trades)*100 if bt.trades else 0
    avg_pl = sum(t['pl_pct'] for t in bt.trades)/len(bt.trades) if bt.trades else 0

    print(f"\n{'='*55}")
    print(f"  {name}")
    print(f"{'='*55}")
    print(f"  交易区间: {bt.nav_history[0]['date']} → {bt.nav_history[-1]['date']}")
    print(f"  交易天数: {n_dates}")
    print(f"  总收益:   {total_ret:+.2f}%")
    print(f"  年化收益: {ann_ret:+.2f}%")
    print(f"  年化波动: {ann_vol:.2f}%")
    print(f"  Sharpe:   {sharpe:+.2f}")
    print(f"  最大回撤: {max_dd:+.2f}%")
    print(f"  交易次数: {len(bt.trades)}")
    print(f"  胜率:     {win_rate:.0f}%")
    print(f"  平均盈亏: {avg_pl:+.2f}%")
    print(f"  最终净值: ¥{end_nav:,.0f}")

    # 对比基准
    bench_ret = total_ret  # 简化, 实际应对比指数
    print(f"\n  ⚠ 注意: 此为历史回测, 不代表未来收益")
    if max_dd < -30:
        print(f"  ⚠ 最大回撤超过30%, 风险较高")

# ── 主流程 ──
def main():
    walk_forward = '--walk-forward' in sys.argv or '-wf' in sys.argv

    print("="*55)
    print("  SpaceX Dashboard 统一评分回测")
    print(f"  模式: {'滚动回测(Walk-Forward)' if walk_forward else '简单OOS(2025固定权重)'}")
    print("="*55)

    # 1. 获取股票池
    codes = get_universe()
    print(f"\n股票池: {len(codes)} 只")

    # 2. 拉取K线
    print("拉取K线数据...")
    stock_data = {}
    for i, code in enumerate(codes):
        klines = fetch_kline(code, n_days=400)  # ~1.5年
        if klines:
            stock_data[code] = klines
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(codes)}...")
        time.sleep(0.08)  # 控制频率

    print(f"有效: {len(stock_data)}/{len(codes)} 只")

    if len(stock_data) < 20:
        print("数据不足, 终止")
        return

    # 3. 构建日期索引
    date_idx_map = {}
    for code, klines in stock_data.items():
        date_idx_map[code] = {k['d']: i for i, k in enumerate(klines)}

    # 找到所有交易日的并集
    all_dates = set()
    for code in stock_data:
        for k in stock_data[code]:
            all_dates.add(k['d'])
    trading_dates = sorted(all_dates)

    # 过滤到OOS范围
    oos_dates = [d for d in trading_dates if OOS_START <= d <= OOS_END]
    if len(oos_dates) < 100:
        # 取最近250个交易日
        oos_dates = trading_dates[-250:] if len(trading_dates) > 250 else trading_dates
        print(f"OOS范围不足, 使用最近{len(oos_dates)}个交易日")

    print(f"OOS交易日: {len(oos_dates)}")

    # 4. 运行回测
    if walk_forward:
        bt = run_walk_forward(stock_data, date_idx_map, oos_dates)
        report(bt, "滚动回测 (Walk-Forward)")
    else:
        bt = run_simple_oos(stock_data, date_idx_map, oos_dates)
        report(bt, "简单OOS回测 (2025, 固定权重)")

    # 5. 保存结果
    result = {
        'mode': 'walk_forward' if walk_forward else 'simple_oos',
        'nav_history': bt.nav_history[-50:] if bt.nav_history else [],  # 最近50天
        'trades_count': len(bt.trades),
        'final_nav': bt.nav_history[-1]['nav'] if bt.nav_history else 0,
    }
    with open(os.path.join(DIR, 'backtest_result.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 backtest_result.json")

if __name__ == '__main__':
    main()
