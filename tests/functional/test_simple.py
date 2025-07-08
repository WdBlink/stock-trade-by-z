#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单测试选股器功能的脚本，直接输出到控制台
"""

import sys
import pandas as pd
from pathlib import Path

# 使用相对导入路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from Selector import BBIKDJSelector, BBIShortLongSelector, BreakoutVolumeKDJSelector, PeakKDJSelector


def load_data(data_dir: Path):
    """
    加载测试数据
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        包含股票数据的字典，键为股票代码，值为DataFrame
    """
    print(f"正在从 {data_dir} 加载数据...")
    frames = {}
    for fp in data_dir.glob("*.csv"):
        print(f"加载文件: {fp.name}")
        df = pd.read_csv(fp, parse_dates=["date"]).sort_values("date")
        frames[fp.stem] = df
        print(f"股票 {fp.stem} 数据范围: {df['date'].min()} 至 {df['date'].max()}, 共 {len(df)} 条记录")
    
    print(f"共加载了 {len(frames)} 只股票的数据")
    return frames


def main():
    """
    主函数
    """
    print("开始测试选股器...")
    
    # 加载数据
    data_dir = Path("/Users/echooo/Documents/Code/github_star/StockTradebyZ/data")
    data = load_data(data_dir)
    
    if not data:
        print("未能加载任何数据，退出测试")
        return
    
    # 使用最新日期作为交易日
    trade_date = pd.to_datetime("2023-06-30")
    print(f"使用交易日: {trade_date.date()}")
    
    # 测试等待B1战法
    print("\n============== 测试等待B1战法 ==============")
    selector1 = BBIKDJSelector(
        j_threshold=1,
        bbi_min_window=20,
        max_window=60,
        price_range_pct=0.5,
        bbi_q_threshold=0.1,
        j_q_threshold=0.10
    )
    picks1 = selector1.select(trade_date, data)
    print(f"等待B1战法选出股票: {picks1}")
    
    # 测试补票战法
    print("\n============== 测试补票战法 ==============")
    selector2 = BBIShortLongSelector(
        n_short=3,
        n_long=21,
        m=3,
        bbi_min_window=2,
        max_window=60,
        bbi_q_threshold=0.2
    )
    picks2 = selector2.select(trade_date, data)
    print(f"补票战法选出股票: {picks2}")
    
    # 测试TePu战法
    print("\n============== 测试TePu战法 ==============")
    selector3 = BreakoutVolumeKDJSelector(
        j_threshold=1,
        j_q_threshold=0.10,
        up_threshold=3.0,
        volume_threshold=0.6667,
        offset=15,
        max_window=60,
        price_range_pct=0.5
    )
    picks3 = selector3.select(trade_date, data)
    print(f"TePu战法选出股票: {picks3}")
    
    # 测试填坑战法
    print("\n============== 测试填坑战法 ==============")
    selector4 = PeakKDJSelector(
        j_threshold=10,
        max_window=100,
        fluc_threshold=0.03,
        j_q_threshold=0.10,
        gap_threshold=0.2
    )
    picks4 = selector4.select(trade_date, data)
    print(f"填坑战法选出股票: {picks4}")
    
    print("\n测试完成")


if __name__ == "__main__":
    main()