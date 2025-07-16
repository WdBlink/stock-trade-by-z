#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试港股数据获取功能
"""

import logging
import sys
from pathlib import Path

import akshare as ak
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("test_hk")

def test_hk_stock():
    """测试港股数据获取"""
    code = "00700"  # 腾讯控股
    start_date = "20230101"
    end_date = "20230105"
    adjust = "qfq"
    
    logger.info("开始获取港股 %s 的历史数据，日期范围：%s 至 %s", code, start_date, end_date)
    
    try:
        logger.info("尝试调用 ak.stock_hk_hist 获取港股数据")
        df = ak.stock_hk_hist(
            symbol=code,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        
        logger.info("成功获取港股数据，数据形状：%s", df.shape)
        logger.info("数据列：%s", df.columns.tolist())
        logger.info("数据预览：\n%s", df.head())
        
        # 保存数据
        out_dir = Path("./data")
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = out_dir / f"HK_{code}.csv"
        
        # 处理数据列名
        column_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount"
        }
        
        # 确保所有需要的列都存在
        available_columns = [col for col in column_map.keys() if col in df.columns]
        
        df = (
            df[available_columns]
            .rename(columns={col: column_map[col] for col in available_columns})
            .assign(date=lambda x: pd.to_datetime(x["date"]))
        )
        
        # 确保必要的列存在
        required_columns = ["date", "open", "close", "high", "low", "volume"]
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"港股 {code} 数据缺少 {col} 列")
                return
        
        # 转换为数值类型
        df[[c for c in df.columns if c != "date"]] = df[[c for c in df.columns if c != "date"]].apply(
            pd.to_numeric, errors="coerce"
        )
        
        df = df[required_columns]
        df = df.sort_values("date").reset_index(drop=True)
        
        # 保存到CSV
        df.to_csv(csv_path, index=False)
        logger.info("数据已保存到 %s", csv_path)
        
    except Exception as e:
        logger.exception("获取港股数据失败：%s", e)

if __name__ == "__main__":
    test_hk_stock()