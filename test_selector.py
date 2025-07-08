import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
from typing import Dict, List

# 导入选股器
from Selector import BBIKDJSelector, BBIShortLongSelector, BreakoutVolumeKDJSelector, PeakKDJSelector

# 配置日志
log_file = "test_selector_results.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("test_selector")

# 确保其他日志不会干扰
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        logging.root.removeHandler(handler)

# 重新添加我们的处理器
for name in logging.root.manager.loggerDict:
    if name != "test_selector":
        logging.getLogger(name).setLevel(logging.ERROR)


def create_test_data() -> Dict[str, pd.DataFrame]:
    """
    创建测试数据，包含符合各种选股策略的股票数据
    """
    # 创建基础数据框架
    date_range = pd.date_range(start="2023-01-01", end="2023-06-30")
    data: Dict[str, pd.DataFrame] = {}
    
    # 创建符合 BBIKDJSelector 策略的数据
    df_bbikdj = pd.DataFrame({
        "date": date_range,
        "open": np.linspace(10, 15, len(date_range)) + np.random.normal(0, 0.1, len(date_range)),
        "high": np.linspace(10.5, 15.5, len(date_range)) + np.random.normal(0, 0.1, len(date_range)),
        "low": np.linspace(9.5, 14.5, len(date_range)) + np.random.normal(0, 0.1, len(date_range)),
        "close": np.linspace(10, 15, len(date_range)) + np.random.normal(0, 0.1, len(date_range)),
        "volume": np.random.randint(1000, 5000, len(date_range)),
    })
    
    # 确保 BBI 上升趋势
    for i in range(len(df_bbikdj) - 30, len(df_bbikdj)):
        df_bbikdj.loc[i, "close"] = df_bbikdj.loc[i-1, "close"] * (1 + 0.01 + 0.005 * np.random.random())
    
    # 确保 KDJ 指标符合条件
    for i in range(len(df_bbikdj) - 10, len(df_bbikdj)):
        df_bbikdj.loc[i, "close"] = df_bbikdj.loc[i-1, "close"] * (1 - 0.005 * np.random.random())
    
    data["TEST001"] = df_bbikdj
    
    # 创建符合 BBIShortLongSelector 策略的数据
    df_bbislong = pd.DataFrame({
        "date": date_range,
        "open": np.linspace(20, 30, len(date_range)) + np.random.normal(0, 0.2, len(date_range)),
        "high": np.linspace(21, 31, len(date_range)) + np.random.normal(0, 0.2, len(date_range)),
        "low": np.linspace(19, 29, len(date_range)) + np.random.normal(0, 0.2, len(date_range)),
        "close": np.linspace(20, 30, len(date_range)) + np.random.normal(0, 0.2, len(date_range)),
        "volume": np.random.randint(2000, 8000, len(date_range)),
    })
    
    # 确保 BBI 上升趋势
    for i in range(len(df_bbislong) - 40, len(df_bbislong)):
        df_bbislong.loc[i, "close"] = df_bbislong.loc[i-1, "close"] * (1 + 0.01 + 0.005 * np.random.random())
    
    # 确保短期 RSV 和长期 RSV 符合条件
    for i in range(len(df_bbislong) - 5, len(df_bbislong)):
        if i % 2 == 0:
            df_bbislong.loc[i, "close"] = df_bbislong.loc[i-1, "close"] * 1.03
            df_bbislong.loc[i, "high"] = df_bbislong.loc[i, "close"] * 1.01
        else:
            df_bbislong.loc[i, "close"] = df_bbislong.loc[i-1, "close"] * 0.97
            df_bbislong.loc[i, "low"] = df_bbislong.loc[i, "close"] * 0.99
    
    data["TEST002"] = df_bbislong
    
    # 创建符合 BreakoutVolumeKDJSelector 策略的数据
    df_breakout = pd.DataFrame({
        "date": date_range,
        "open": np.linspace(30, 40, len(date_range)) + np.random.normal(0, 0.3, len(date_range)),
        "high": np.linspace(31, 41, len(date_range)) + np.random.normal(0, 0.3, len(date_range)),
        "low": np.linspace(29, 39, len(date_range)) + np.random.normal(0, 0.3, len(date_range)),
        "close": np.linspace(30, 40, len(date_range)) + np.random.normal(0, 0.3, len(date_range)),
        "volume": np.random.randint(3000, 10000, len(date_range)),
    })
    
    # 创建放量突破
    breakout_idx = len(df_breakout) - 20
    df_breakout.loc[breakout_idx, "close"] = df_breakout.loc[breakout_idx-1, "close"] * 1.05
    df_breakout.loc[breakout_idx, "volume"] = df_breakout.loc[breakout_idx-1:breakout_idx+10, "volume"].mean() * 3
    
    # 确保 KDJ 指标符合条件
    for i in range(breakout_idx + 1, len(df_breakout)):
        df_breakout.loc[i, "close"] = df_breakout.loc[i-1, "close"] * (1 - 0.002 * np.random.random())
    
    data["TEST003"] = df_breakout
    
    # 创建符合 PeakKDJSelector 策略的数据
    df_peak = pd.DataFrame({
        "date": date_range,
        "open": np.linspace(50, 60, len(date_range)) + np.random.normal(0, 0.5, len(date_range)),
        "high": np.linspace(51, 61, len(date_range)) + np.random.normal(0, 0.5, len(date_range)),
        "low": np.linspace(49, 59, len(date_range)) + np.random.normal(0, 0.5, len(date_range)),
        "close": np.linspace(50, 60, len(date_range)) + np.random.normal(0, 0.5, len(date_range)),
        "volume": np.random.randint(5000, 15000, len(date_range)),
    })
    
    # 创建峰值
    peak1_idx = len(df_peak) - 40
    peak2_idx = len(df_peak) - 20
    
    df_peak.loc[peak1_idx-5:peak1_idx, "close"] = np.linspace(
        df_peak.loc[peak1_idx-6, "close"], 
        df_peak.loc[peak1_idx-6, "close"] * 1.1, 
        6
    )
    df_peak.loc[peak1_idx+1:peak1_idx+5, "close"] = np.linspace(
        df_peak.loc[peak1_idx, "close"], 
        df_peak.loc[peak1_idx, "close"] * 0.9, 
        5
    )
    
    df_peak.loc[peak2_idx-5:peak2_idx, "close"] = np.linspace(
        df_peak.loc[peak2_idx-6, "close"], 
        df_peak.loc[peak2_idx-6, "close"] * 1.15, 
        6
    )
    df_peak.loc[peak2_idx+1:peak2_idx+5, "close"] = np.linspace(
        df_peak.loc[peak2_idx, "close"], 
        df_peak.loc[peak2_idx, "close"] * 0.92, 
        5
    )
    
    # 确保 KDJ 指标符合条件
    for i in range(len(df_peak) - 10, len(df_peak)):
        df_peak.loc[i, "close"] = df_peak.loc[i-1, "close"] * (1 - 0.003 * np.random.random())
    
    data["TEST004"] = df_peak
    
    return data


def test_selectors(data: Dict[str, pd.DataFrame], date: pd.Timestamp):
    """
    测试所有选股策略
    """
    # 测试 BBIKDJSelector
    bbikdj_selector = BBIKDJSelector(
        j_threshold=1,
        bbi_min_window=20,
        max_window=60,
        price_range_pct=0.5,
        bbi_q_threshold=0.1,
        j_q_threshold=0.10
    )
    
    # 调试 BBIKDJSelector
    logger.info("\n============== 调试 [等待B1战法] ==============")
    for code, df in data.items():
        logger.info("分析股票: %s", code)
        # 检查数据是否足够
        if len(df) < 60:
            logger.info("  数据不足，跳过")
            continue
            
        # 计算指标
        from Selector import BBI, KDJ, DIF
        bbi = BBI(df)
        k, d, j = KDJ(df)
        dif = DIF(df)
        
        # 获取最近日期的索引
        idx = df[df['date'] <= date].index[-1]
        
        # 检查 BBI 上升趋势
        bbi_rising = bbi[idx] > bbi[idx-1] > bbi[idx-2]
        logger.info("  BBI上升趋势: %s (BBI值: %.2f, %.2f, %.2f)", 
                   bbi_rising, bbi[idx], bbi[idx-1], bbi[idx-2])
        
        # 检查 J 值条件
        j_condition = j[idx] < bbikdj_selector.j_threshold
        logger.info("  J值条件: %s (J值: %.2f, 阈值: %.2f)", 
                   j_condition, j[idx], bbikdj_selector.j_threshold)
        
        # 检查 DIF > 0
        dif_condition = dif[idx] > 0
        logger.info("  DIF > 0: %s (DIF值: %.2f)", dif_condition, dif[idx])
        
        # 检查价格波动
        price_range = (df['close'].max() - df['close'].min()) / df['close'].min() * 100
        price_condition = price_range <= bbikdj_selector.price_range_pct
        logger.info("  价格波动条件: %s (波动: %.2f%%, 阈值: %.2f%%)", 
                   price_condition, price_range, bbikdj_selector.price_range_pct)
        
        # 综合判断
        passes = bbi_rising and j_condition and dif_condition and price_condition
        logger.info("  综合判断: %s\n", passes)
    
    bbikdj_picks = bbikdj_selector.select(date, data)
    logger.info("\n============== 选股结果 [等待B1战法] ==============")
    logger.info("交易日: %s", date.date())
    logger.info("符合条件股票数: %d", len(bbikdj_picks))
    logger.info("%s", ", ".join(bbikdj_picks) if bbikdj_picks else "无符合条件股票")
    
    # 测试 BBIShortLongSelector
    bbisl_selector = BBIShortLongSelector(
        n_short=3,
        n_long=21,
        m=3,
        bbi_min_window=2,
        max_window=60,
        bbi_q_threshold=0.2
    )
    bbisl_picks = bbisl_selector.select(date, data)
    logger.info("\n============== 选股结果 [补票战法] ==============")
    logger.info("交易日: %s", date.date())
    logger.info("符合条件股票数: %d", len(bbisl_picks))
    logger.info("%s", ", ".join(bbisl_picks) if bbisl_picks else "无符合条件股票")
    
    # 测试 BreakoutVolumeKDJSelector
    breakout_selector = BreakoutVolumeKDJSelector(
        j_threshold=1,
        j_q_threshold=0.10,
        up_threshold=3.0,
        volume_threshold=0.6667,
        offset=15,
        max_window=60,
        price_range_pct=0.5
    )
    breakout_picks = breakout_selector.select(date, data)
    logger.info("\n============== 选股结果 [TePu战法] ==============")
    logger.info("交易日: %s", date.date())
    logger.info("符合条件股票数: %d", len(breakout_picks))
    logger.info("%s", ", ".join(breakout_picks) if breakout_picks else "无符合条件股票")
    
    # 测试 PeakKDJSelector
    peak_selector = PeakKDJSelector(
        j_threshold=10,
        max_window=100,
        fluc_threshold=0.03,
        j_q_threshold=0.10,
        gap_threshold=0.2
    )
    peak_picks = peak_selector.select(date, data)
    logger.info("\n============== 选股结果 [填坑战法] ==============")
    logger.info("交易日: %s", date.date())
    logger.info("符合条件股票数: %d", len(peak_picks))
    logger.info("%s", ", ".join(peak_picks) if peak_picks else "无符合条件股票")


def main():
    # 创建测试数据
    data = create_test_data()
    
    # 测试日期
    test_date = pd.Timestamp("2023-06-30")
    
    # 运行测试
    test_selectors(data, test_date)


if __name__ == "__main__":
    main()