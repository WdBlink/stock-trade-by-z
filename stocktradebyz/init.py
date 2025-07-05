#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""初始化项目"""

import os
import sys
from pathlib import Path

from stocktradebyz.config.utils import copy_default_configs


def init_project(data_dir: str = "./data") -> None:
    """初始化项目
    
    Args:
        data_dir: 数据目录
    """
    # 创建数据目录
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    print(f"数据目录已创建: {data_path.resolve()}")
    
    # 复制默认配置文件到当前目录
    copy_default_configs(os.getcwd())
    print(f"默认配置文件已复制到: {os.getcwd()}")
    
    print("\n初始化完成！您现在可以：")
    print("1. 修改 configs.json 配置选股策略")
    print("2. 修改 appendix.json 添加自定义股票池")
    print("3. 运行 'fetch-kline' 下载历史K线数据")
    print("4. 运行 'select-stock' 执行选股策略")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="初始化 StockTradebyZ 项目")
    parser.add_argument("--data-dir", default="./data", help="数据目录")
    
    args = parser.parse_args()
    init_project(args.data_dir)


if __name__ == "__main__":
    main()