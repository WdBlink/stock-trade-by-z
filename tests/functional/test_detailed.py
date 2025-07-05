#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
详细测试选股器功能的脚本，显示中间计算过程
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 使用相对导入路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from Selector import BBIKDJSelector, BBIShortLongSelector, BreakoutVolumeKDJSelector, PeakKDJSelector

# 确保输出不被缓冲
def print_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()


def load_data(data_dir: Path):
    """
    加载测试数据
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        包含股票数据的字典，键为股票代码，值为DataFrame
    """
    print_flush(f"正在从 {data_dir} 加载数据...")
    frames = {}
    for fp in data_dir.glob("*.csv"):
        print_flush(f"加载文件: {fp.name}")
        df = pd.read_csv(fp, parse_dates=["date"]).sort_values("date")
        frames[fp.stem] = df
        print_flush(f"股票 {fp.stem} 数据范围: {df['date'].min()} 至 {df['date'].max()}, 共 {len(df)} 条记录")
    
    print_flush(f"共加载了 {len(frames)} 只股票的数据")
    return frames


def analyze_stock_data(stock_code, df):
    """
    分析单只股票的数据
    
    Args:
        stock_code: 股票代码
        df: 股票数据DataFrame
    """
    print_flush(f"\n分析股票 {stock_code} 的数据:")
    print_flush(f"数据范围: {df['date'].min()} 至 {df['date'].max()}, 共 {len(df)} 条记录")
    
    # 计算基本技术指标
    print_flush("\n计算基本技术指标...")
    
    # 计算KDJ指标
    low_list = df['low'].rolling(window=9, min_periods=9).min()
    high_list = df['high'].rolling(window=9, min_periods=9).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    k = pd.Series(0.0, index=df.index)
    d = pd.Series(0.0, index=df.index)
    j = pd.Series(0.0, index=df.index)
    
    for i in range(len(df)):
        if i == 0:
            k[i] = 50
            d[i] = 50
            j[i] = 50
        else:
            k[i] = 2/3 * k[i-1] + 1/3 * rsv[i]
            d[i] = 2/3 * d[i-1] + 1/3 * k[i]
            j[i] = 3 * k[i] - 2 * d[i]
    
    # 计算BBI指标
    ma3 = df['close'].rolling(window=3).mean()
    ma6 = df['close'].rolling(window=6).mean()
    ma12 = df['close'].rolling(window=12).mean()
    ma24 = df['close'].rolling(window=24).mean()
    bbi = (ma3 + ma6 + ma12 + ma24) / 4
    
    # 显示最近5天的指标
    recent_days = 5
    print_flush(f"\n最近{recent_days}天的技术指标:")
    for i in range(len(df) - recent_days, len(df)):
        date = df['date'].iloc[i].strftime('%Y-%m-%d')
        print_flush(f"日期: {date}, 收盘价: {df['close'].iloc[i]:.2f}, K: {k.iloc[i]:.2f}, D: {d.iloc[i]:.2f}, J: {j.iloc[i]:.2f}, BBI: {bbi.iloc[i]:.2f}")
    
    return {
        'k': k,
        'd': d,
        'j': j,
        'bbi': bbi,
        'close': df['close'],
        'volume': df['volume'],
        'high': df['high'],
        'low': df['low']
    }


def test_bbikdj_selector(trade_date, data, indicators):
    """
    测试少妇战法
    
    Args:
        trade_date: 交易日期
        data: 股票数据字典
        indicators: 技术指标字典
    """
    print_flush("\n============== 测试少妇战法 ==============")
    selector = BBIKDJSelector(
        j_threshold=1,
        bbi_min_window=20,
        max_window=60,
        price_range_pct=0.5,
        bbi_q_threshold=0.1,
        j_q_threshold=0.10
    )
    
    print_flush("少妇战法参数:")
    print_flush(f"  j_threshold: {selector.j_threshold}")
    print_flush(f"  bbi_min_window: {selector.bbi_min_window}")
    print_flush(f"  max_window: {selector.max_window}")
    print_flush(f"  price_range_pct: {selector.price_range_pct}")
    print_flush(f"  bbi_q_threshold: {selector.bbi_q_threshold}")
    print_flush(f"  j_q_threshold: {selector.j_q_threshold}")
    
    picks = []
    for stock_code, df in data.items():
        print_flush(f"\n分析股票 {stock_code}:")
        
        # 获取该股票的指标
        ind = indicators[stock_code]
        j = ind['j']
        bbi = ind['bbi']
        close = ind['close']
        
        # 获取最新日期的索引
        latest_idx = df[df['date'] <= pd.to_datetime(trade_date)].index[-1]
        
        # 检查J值条件
        j_value = j.iloc[latest_idx]
        j_window = j.iloc[max(0, latest_idx - selector.max_window):latest_idx+1]
        j_quantile = np.nanquantile(j_window, selector.j_q_threshold)
        j_condition = j_value > j_quantile
        print_flush(f"  J值条件: 当前J值 {j_value:.2f} > {j_quantile:.2f} 分位数? {j_condition}")
        
        # 检查BBI条件
        bbi_value = bbi.iloc[latest_idx]
        bbi_min_idx = max(0, latest_idx - selector.bbi_min_window)
        bbi_window = bbi.iloc[bbi_min_idx:latest_idx+1]
        bbi_quantile = np.nanquantile(bbi_window, selector.bbi_q_threshold)
        bbi_condition = bbi_value < bbi_quantile
        print_flush(f"  BBI条件: 当前BBI值 {bbi_value:.2f} < {bbi_quantile:.2f} 分位数? {bbi_condition}")
        
        # 检查价格范围条件
        price_window = close.iloc[max(0, latest_idx - selector.max_window):latest_idx+1]
        price_range = (price_window.max() - price_window.min()) / price_window.min()
        price_condition = price_range <= selector.price_range_pct
        print_flush(f"  价格范围条件: 价格波动 {price_range:.2%} <= {selector.price_range_pct:.2%}? {price_condition}")
        
        # 检查J值阈值条件
        j_threshold_condition = j_value > selector.j_threshold
        print_flush(f"  J值阈值条件: 当前J值 {j_value:.2f} > {selector.j_threshold}? {j_threshold_condition}")
        
        # 综合判断
        all_conditions = j_condition and bbi_condition and price_condition and j_threshold_condition
        print_flush(f"  综合判断: {all_conditions}")
        
        if all_conditions:
            picks.append(stock_code)
    
    print_flush(f"\n少妇战法选出股票: {picks}")
    return picks


def test_bbishorlong_selector(trade_date, data, indicators):
    """
    测试补票战法
    
    Args:
        trade_date: 交易日期
        data: 股票数据字典
        indicators: 技术指标字典
    """
    print_flush("\n============== 测试补票战法 ==============")
    selector = BBIShortLongSelector(
        n_short=3,
        n_long=21,
        m=3,
        bbi_min_window=2,
        max_window=60,
        bbi_q_threshold=0.2
    )
    
    print_flush("补票战法参数:")
    print_flush(f"  n_short: {selector.n_short}")
    print_flush(f"  n_long: {selector.n_long}")
    print_flush(f"  m: {selector.m}")
    print_flush(f"  bbi_min_window: {selector.bbi_min_window}")
    print_flush(f"  max_window: {selector.max_window}")
    print_flush(f"  bbi_q_threshold: {selector.bbi_q_threshold}")
    
    picks = []
    for stock_code, df in data.items():
        print_flush(f"\n分析股票 {stock_code}:")
        
        # 获取该股票的指标
        ind = indicators[stock_code]
        bbi = ind['bbi']
        close = ind['close']
        
        # 获取最新日期的索引
        latest_idx = df[df['date'] <= pd.to_datetime(trade_date)].index[-1]
        
        # 计算短期和长期均线
        ma_short = close.rolling(window=selector.n_short).mean()
        ma_long = close.rolling(window=selector.n_long).mean()
        
        # 检查均线金叉条件
        cross_condition = False
        for i in range(max(0, latest_idx - selector.m), latest_idx + 1):
            if i > 0 and ma_short.iloc[i-1] <= ma_long.iloc[i-1] and ma_short.iloc[i] > ma_long.iloc[i]:
                cross_condition = True
                break
        print_flush(f"  均线金叉条件: 最近{selector.m}天内短期均线上穿长期均线? {cross_condition}")
        
        # 检查BBI条件
        bbi_value = bbi.iloc[latest_idx]
        bbi_min_idx = max(0, latest_idx - selector.bbi_min_window)
        bbi_window = bbi.iloc[bbi_min_idx:latest_idx+1]
        bbi_quantile = np.nanquantile(bbi_window, selector.bbi_q_threshold)
        bbi_condition = bbi_value < bbi_quantile
        print_flush(f"  BBI条件: 当前BBI值 {bbi_value:.2f} < {bbi_quantile:.2f} 分位数? {bbi_condition}")
        
        # 综合判断
        all_conditions = cross_condition and bbi_condition
        print_flush(f"  综合判断: {all_conditions}")
        
        if all_conditions:
            picks.append(stock_code)
    
    print_flush(f"\n补票战法选出股票: {picks}")
    return picks


def test_breakoutvolumekdj_selector(trade_date, data, indicators):
    """
    测试TePu战法
    
    Args:
        trade_date: 交易日期
        data: 股票数据字典
        indicators: 技术指标字典
    """
    print_flush("\n============== 测试TePu战法 ==============")
    selector = BreakoutVolumeKDJSelector(
        j_threshold=1,
        j_q_threshold=0.10,
        up_threshold=3.0,
        volume_threshold=0.6667,
        offset=15,
        max_window=60,
        price_range_pct=0.5
    )
    
    print_flush("TePu战法参数:")
    print_flush(f"  j_threshold: {selector.j_threshold}")
    print_flush(f"  j_q_threshold: {selector.j_q_threshold}")
    print_flush(f"  up_threshold: {selector.up_threshold}")
    print_flush(f"  volume_threshold: {selector.volume_threshold}")
    print_flush(f"  offset: {selector.offset}")
    print_flush(f"  max_window: {selector.max_window}")
    print_flush(f"  price_range_pct: {selector.price_range_pct}")
    
    picks = []
    for stock_code, df in data.items():
        print_flush(f"\n分析股票 {stock_code}:")
        
        # 获取该股票的指标
        ind = indicators[stock_code]
        j = ind['j']
        close = ind['close']
        volume = ind['volume']
        
        # 获取最新日期的索引
        latest_idx = df[df['date'] <= pd.to_datetime(trade_date)].index[-1]
        
        # 检查J值条件
        j_value = j.iloc[latest_idx]
        j_window = j.iloc[max(0, latest_idx - selector.max_window):latest_idx+1]
        j_quantile = np.nanquantile(j_window, selector.j_q_threshold)
        j_condition = j_value > j_quantile
        print_flush(f"  J值条件: 当前J值 {j_value:.2f} > {j_quantile:.2f} 分位数? {j_condition}")
        
        # 检查价格突破条件
        price_offset_idx = max(0, latest_idx - selector.offset)
        price_change = (close.iloc[latest_idx] - close.iloc[price_offset_idx]) / close.iloc[price_offset_idx] * 100
        price_condition = price_change > selector.up_threshold
        print_flush(f"  价格突破条件: 价格变化 {price_change:.2f}% > {selector.up_threshold:.2f}%? {price_condition}")
        
        # 检查成交量条件
        volume_offset_idx = max(0, latest_idx - selector.offset)
        volume_change = volume.iloc[latest_idx] / volume.iloc[volume_offset_idx]
        volume_condition = volume_change > selector.volume_threshold
        print_flush(f"  成交量条件: 成交量变化 {volume_change:.2f} > {selector.volume_threshold:.2f}? {volume_condition}")
        
        # 检查价格范围条件
        price_window = close.iloc[max(0, latest_idx - selector.max_window):latest_idx+1]
        price_range = (price_window.max() - price_window.min()) / price_window.min()
        price_range_condition = price_range <= selector.price_range_pct
        print_flush(f"  价格范围条件: 价格波动 {price_range:.2%} <= {selector.price_range_pct:.2%}? {price_range_condition}")
        
        # 检查J值阈值条件
        j_threshold_condition = j_value > selector.j_threshold
        print_flush(f"  J值阈值条件: 当前J值 {j_value:.2f} > {selector.j_threshold}? {j_threshold_condition}")
        
        # 综合判断
        all_conditions = j_condition and price_condition and volume_condition and price_range_condition and j_threshold_condition
        print_flush(f"  综合判断: {all_conditions}")
        
        if all_conditions:
            picks.append(stock_code)
    
    print_flush(f"\nTePu战法选出股票: {picks}")
    return picks


def test_peakkdj_selector(trade_date, data, indicators):
    """
    测试填坑战法
    
    Args:
        trade_date: 交易日期
        data: 股票数据字典
        indicators: 技术指标字典
    """
    print_flush("\n============== 测试填坑战法 ==============")
    selector = PeakKDJSelector(
        j_threshold=10,
        max_window=100,
        fluc_threshold=0.03,
        j_q_threshold=0.10,
        gap_threshold=0.2
    )
    
    print_flush("填坑战法参数:")
    print_flush(f"  j_threshold: {selector.j_threshold}")
    print_flush(f"  max_window: {selector.max_window}")
    print_flush(f"  fluc_threshold: {selector.fluc_threshold}")
    print_flush(f"  j_q_threshold: {selector.j_q_threshold}")
    print_flush(f"  gap_threshold: {selector.gap_threshold}")
    
    picks = []
    for stock_code, df in data.items():
        print_flush(f"\n分析股票 {stock_code}:")
        
        # 获取该股票的指标
        ind = indicators[stock_code]
        j = ind['j']
        high = ind['high']
        low = ind['low']
        
        # 获取最新日期的索引
        latest_idx = df[df['date'] <= pd.to_datetime(trade_date)].index[-1]
        
        # 检查J值条件
        j_value = j.iloc[latest_idx]
        j_window = j.iloc[max(0, latest_idx - selector.max_window):latest_idx+1]
        j_quantile = np.nanquantile(j_window, selector.j_q_threshold)
        j_condition = j_value > j_quantile
        print_flush(f"  J值条件: 当前J值 {j_value:.2f} > {j_quantile:.2f} 分位数? {j_condition}")
        
        # 检查价格波动条件
        price_fluc = (high.iloc[latest_idx] - low.iloc[latest_idx]) / low.iloc[latest_idx]
        price_fluc_condition = price_fluc > selector.fluc_threshold
        print_flush(f"  价格波动条件: 当日价格波动 {price_fluc:.2%} > {selector.fluc_threshold:.2%}? {price_fluc_condition}")
        
        # 检查缺口条件
        if latest_idx > 0:
            gap = (low.iloc[latest_idx] - high.iloc[latest_idx-1]) / high.iloc[latest_idx-1]
            gap_condition = gap > selector.gap_threshold
            print_flush(f"  缺口条件: 缺口大小 {gap:.2%} > {selector.gap_threshold:.2%}? {gap_condition}")
        else:
            gap_condition = False
            print_flush(f"  缺口条件: 无法计算 (没有前一天数据)")
        
        # 检查J值阈值条件
        j_threshold_condition = j_value > selector.j_threshold
        print_flush(f"  J值阈值条件: 当前J值 {j_value:.2f} > {selector.j_threshold}? {j_threshold_condition}")
        
        # 综合判断
        all_conditions = j_condition and price_fluc_condition and gap_condition and j_threshold_condition
        print_flush(f"  综合判断: {all_conditions}")
        
        if all_conditions:
            picks.append(stock_code)
    
    print_flush(f"\n填坑战法选出股票: {picks}")
    return picks


def main():
    """
    主函数
    """
    print_flush("开始详细测试选股器...")
    
    # 加载数据
    data_dir = Path("/Users/echooo/Documents/Code/github_star/StockTradebyZ/data")
    data = load_data(data_dir)
    
    if not data:
        print_flush("未能加载任何数据，退出测试")
        return
    
    # 使用最新日期作为交易日
    trade_date = pd.to_datetime("2023-06-30")
    print_flush(f"使用交易日: {trade_date.date()}")
    
    # 计算技术指标
    indicators = {}
    for stock_code, df in data.items():
        indicators[stock_code] = analyze_stock_data(stock_code, df)
    
    # 测试各种选股策略
    test_bbikdj_selector(trade_date, data, indicators)
    test_bbishorlong_selector(trade_date, data, indicators)
    test_breakoutvolumekdj_selector(trade_date, data, indicators)
    test_peakkdj_selector(trade_date, data, indicators)
    
    print_flush("\n详细测试完成")


if __name__ == "__main__":
    main()