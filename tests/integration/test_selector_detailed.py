#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
详细测试选股器功能的脚本，包含中间计算过程的输出
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
# 使用相对导入路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from Selector import (
    BBIKDJSelector, BBIShortLongSelector, 
    BreakoutVolumeKDJSelector, PeakKDJSelector,
    compute_kdj, compute_bbi, compute_rsv, compute_dif, bbi_deriv_uptrend
)

# 配置日志输出到控制台和文件
logging.basicConfig(
    level=logging.DEBUG,  # 使用DEBUG级别以显示更多信息
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(Path(__file__).parent.parent / "outputs" / "test_selector_detailed.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("test_selector_detailed")


def load_data(data_dir: Path):
    """
    加载测试数据
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        包含股票数据的字典，键为股票代码，值为DataFrame
    """
    logger.info(f"正在从 {data_dir} 加载数据...")
    frames = {}
    for fp in data_dir.glob("*.csv"):
        logger.info(f"加载文件: {fp.name}")
        df = pd.read_csv(fp, parse_dates=["date"]).sort_values("date")
        frames[fp.stem] = df
        logger.debug(f"股票 {fp.stem} 数据范围: {df['date'].min()} 至 {df['date'].max()}, 共 {len(df)} 条记录")
    
    logger.info(f"共加载了 {len(frames)} 只股票的数据")
    return frames


def analyze_stock_data(code, df, trade_date):
    """
    分析单只股票的技术指标
    
    Args:
        code: 股票代码
        df: 股票数据DataFrame
        trade_date: 交易日期
    """
    logger.info(f"\n分析股票 {code} 的技术指标...")
    
    # 计算KDJ指标
    k, d, j = compute_kdj(df)
    logger.debug(f"KDJ指标最后5个值:\nK: {k[-5:]}\nD: {d[-5:]}\nJ: {j[-5:]}")
    
    # 计算BBI指标
    bbi = compute_bbi(df)
    logger.debug(f"BBI指标最后5个值: {bbi[-5:]}")
    
    # 计算BBI趋势
    uptrend = bbi_deriv_uptrend(bbi, min_window=20)
    logger.debug(f"BBI上升趋势最后5个值: {uptrend[-5:]}")
    
    # 计算短期和长期RSV
    rsv_short = compute_rsv(df, n=3)
    rsv_long = compute_rsv(df, n=21)
    logger.debug(f"短期RSV最后5个值: {rsv_short[-5:]}")
    logger.debug(f"长期RSV最后5个值: {rsv_long[-5:]}")
    
    # 计算DIF
    dif = compute_dif(df)
    logger.debug(f"DIF最后5个值: {dif[-5:]}")
    
    # 获取最后交易日的指标值
    idx = df[df['date'] <= pd.to_datetime(trade_date)].index[-1]
    logger.info(f"交易日 {trade_date.date()} 的指标值:")
    logger.info(f"  收盘价: {df.loc[idx, 'close']:.2f}")
    logger.info(f"  KDJ: K={k[idx]:.2f}, D={d[idx]:.2f}, J={j[idx]:.2f}")
    logger.info(f"  BBI: {bbi[idx]:.2f}, 上升趋势: {uptrend[idx]}")
    logger.info(f"  RSV短期: {rsv_short[idx]:.2f}, RSV长期: {rsv_long[idx]:.2f}")
    logger.info(f"  DIF: {dif[idx]:.2f}")
    
    return {
        'k': k, 'd': d, 'j': j, 'bbi': bbi, 'uptrend': uptrend,
        'rsv_short': rsv_short, 'rsv_long': rsv_long, 'dif': dif,
        'idx': idx
    }


def test_bbi_kdj_selector(data, trade_date, indicators):
    """
    详细测试少妇战法选股器
    
    Args:
        data: 股票数据字典
        trade_date: 交易日期
        indicators: 预计算的指标字典
    """
    logger.info("\n============== 详细测试少妇战法 ==============")
    selector = BBIKDJSelector(
        j_threshold=1,
        bbi_min_window=20,
        max_window=60,
        price_range_pct=0.5,
        bbi_q_threshold=0.1,
        j_q_threshold=0.10
    )
    
    # 记录选股器参数
    logger.info(f"选股器参数: j_threshold={selector.j_threshold}, "
                f"bbi_min_window={selector.bbi_min_window}, "
                f"max_window={selector.max_window}, "
                f"price_range_pct={selector.price_range_pct}, "
                f"bbi_q_threshold={selector.bbi_q_threshold}, "
                f"j_q_threshold={selector.j_q_threshold}")
    
    # 逐个股票分析选股条件
    for code, df in data.items():
        ind = indicators[code]
        idx = ind['idx']
        
        # 检查BBI上升趋势条件
        bbi_uptrend = ind['uptrend'][idx]
        logger.info(f"\n股票 {code} 少妇战法条件检查:")
        logger.info(f"1. BBI上升趋势: {bbi_uptrend} {'✓' if bbi_uptrend else '✗'}")
        
        if not bbi_uptrend:
            logger.info(f"  股票 {code} 不满足BBI上升趋势条件，跳过后续检查")
            continue
        
        # 检查J值条件
        j_value = ind['j'][idx]
        j_condition = j_value > selector.j_threshold
        logger.info(f"2. J值 {j_value:.2f} > {selector.j_threshold}: {'✓' if j_condition else '✗'}")
        
        if not j_condition:
            logger.info(f"  股票 {code} 不满足J值条件，跳过后续检查")
            continue
        
        # 检查DIF条件
        dif_value = ind['dif'][idx]
        dif_condition = dif_value > 0
        logger.info(f"3. DIF {dif_value:.2f} > 0: {'✓' if dif_condition else '✗'}")
        
        if not dif_condition:
            logger.info(f"  股票 {code} 不满足DIF条件，跳过后续检查")
            continue
        
        # 检查价格波动范围条件
        price_range = selector._check_price_range(df, idx, selector.max_window)
        price_condition = price_range <= selector.price_range_pct
        logger.info(f"4. 价格波动范围 {price_range:.2f} <= {selector.price_range_pct}: {'✓' if price_condition else '✗'}")
        
        if not price_condition:
            logger.info(f"  股票 {code} 不满足价格波动范围条件，跳过后续检查")
            continue
        
        logger.info(f"  股票 {code} 满足所有少妇战法条件 ✓")
    
    # 运行选股器获取结果
    picks = selector.select(trade_date, data)
    logger.info(f"少妇战法最终选出股票: {picks}")
    return picks


def test_bbi_short_long_selector(data, trade_date, indicators):
    """
    详细测试补票战法选股器
    
    Args:
        data: 股票数据字典
        trade_date: 交易日期
        indicators: 预计算的指标字典
    """
    logger.info("\n============== 详细测试补票战法 ==============")
    selector = BBIShortLongSelector(
        n_short=3,
        n_long=21,
        m=3,
        bbi_min_window=2,
        max_window=60,
        bbi_q_threshold=0.2
    )
    
    # 记录选股器参数
    logger.info(f"选股器参数: n_short={selector.n_short}, "
                f"n_long={selector.n_long}, "
                f"m={selector.m}, "
                f"bbi_min_window={selector.bbi_min_window}, "
                f"max_window={selector.max_window}, "
                f"bbi_q_threshold={selector.bbi_q_threshold}")
    
    # 逐个股票分析选股条件
    for code, df in data.items():
        ind = indicators[code]
        idx = ind['idx']
        
        # 检查BBI上升趋势条件
        bbi_uptrend = ind['uptrend'][idx]
        logger.info(f"\n股票 {code} 补票战法条件检查:")
        logger.info(f"1. BBI上升趋势: {bbi_uptrend} {'✓' if bbi_uptrend else '✗'}")
        
        if not bbi_uptrend:
            logger.info(f"  股票 {code} 不满足BBI上升趋势条件，跳过后续检查")
            continue
        
        # 检查短期RSV条件
        rsv_short = ind['rsv_short'][idx]
        rsv_short_condition = rsv_short < 0.2
        logger.info(f"2. 短期RSV {rsv_short:.2f} < 0.2: {'✓' if rsv_short_condition else '✗'}")
        
        if not rsv_short_condition:
            logger.info(f"  股票 {code} 不满足短期RSV条件，跳过后续检查")
            continue
        
        # 检查长期RSV条件
        rsv_long = ind['rsv_long'][idx]
        rsv_long_condition = rsv_long > 0.8
        logger.info(f"3. 长期RSV {rsv_long:.2f} > 0.8: {'✓' if rsv_long_condition else '✗'}")
        
        if not rsv_long_condition:
            logger.info(f"  股票 {code} 不满足长期RSV条件，跳过后续检查")
            continue
        
        # 检查DIF条件
        dif_value = ind['dif'][idx]
        dif_condition = dif_value > 0
        logger.info(f"4. DIF {dif_value:.2f} > 0: {'✓' if dif_condition else '✗'}")
        
        if not dif_condition:
            logger.info(f"  股票 {code} 不满足DIF条件，跳过后续检查")
            continue
        
        logger.info(f"  股票 {code} 满足所有补票战法条件 ✓")
    
    # 运行选股器获取结果
    picks = selector.select(trade_date, data)
    logger.info(f"补票战法最终选出股票: {picks}")
    return picks


def main():
    """
    主函数
    """
    logger.info("开始详细测试选股器...")
    
    # 加载数据
    data_dir = Path("/Users/echooo/Documents/Code/github_star/StockTradebyZ/data")
    data = load_data(data_dir)
    
    if not data:
        logger.error("未能加载任何数据，退出测试")
        return
    
    # 使用最新日期作为交易日
    trade_date = pd.to_datetime("2023-06-30")
    logger.info(f"使用交易日: {trade_date.date()}")
    
    # 预计算所有股票的指标
    indicators = {}
    for code, df in data.items():
        indicators[code] = analyze_stock_data(code, df, trade_date)
    
    # 详细测试各选股器
    test_bbi_kdj_selector(data, trade_date, indicators)
    test_bbi_short_long_selector(data, trade_date, indicators)
    
    logger.info("\n详细测试完成")


if __name__ == "__main__":
    main()