#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版测试港股数据获取功能
"""

import os
import sys
from pathlib import Path

import akshare as ak
import pandas as pd

def main():
    """测试港股数据获取"""
    # 创建数据目录
    data_dir = Path("./data_hk")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取港股数据
    code = "00700"  # 腾讯控股
    start_date = "20230101"
    end_date = "20230105"
    adjust = "qfq"
    
    print(f"开始获取港股 {code} 的历史数据，日期范围：{start_date} 至 {end_date}")
    
    try:
        print(f"尝试调用 ak.stock_hk_hist 获取港股数据")
        df = ak.stock_hk_hist(
            symbol=code,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        
        print(f"成功获取港股数据，数据形状：{df.shape}")
        print(f"数据列：{df.columns.tolist()}")
        print(f"数据预览：\n{df.head()}")
        
        # 保存数据
        csv_path = data_dir / f"HK_{code}.csv"
        
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
                print(f"港股 {code} 数据缺少 {col} 列")
                return
        
        # 转换为数值类型
        df[[c for c in df.columns if c != "date"]] = df[[c for c in df.columns if c != "date"]].apply(
            pd.to_numeric, errors="coerce"
        )
        
        df = df[required_columns]
        df = df.sort_values("date").reset_index(drop=True)
        
        # 保存到CSV
        df.to_csv(csv_path, index=False)
        print(f"数据已保存到 {csv_path}")
        
        # 显示文件内容
        print(f"\n文件内容预览：")
        with open(csv_path, "r") as f:
            print(f.read())
        
    except Exception as e:
        print(f"获取港股数据失败：{e}")

if __name__ == "__main__":
    main()