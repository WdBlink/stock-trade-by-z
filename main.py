#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""StockTradebyZ 主入口"""

import argparse
import sys

from stocktradebyz import fetch, select, init


def main():
    parser = argparse.ArgumentParser(
        description="StockTradebyZ - 一个基于Python的A股量化选股工具",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 初始化子命令
    init_parser = subparsers.add_parser("init", help="初始化项目")
    init_parser.add_argument("--data-dir", default="./data", help="数据目录")
    
    # 抓取K线数据子命令
    fetch_parser = subparsers.add_parser("fetch", help="抓取历史K线数据")
    fetch_parser.add_argument("--datasource", choices=["tushare", "akshare", "mootdx"], default="tushare", help="历史 K 线数据源")
    fetch_parser.add_argument("--frequency", type=int, choices=list(fetch._FREQ_MAP.keys()), default=4, help="K线频率编码，参见说明")
    fetch_parser.add_argument("--exclude-gem", default=True, help="True则排除创业板/科创板/北交所")
    fetch_parser.add_argument("--min-mktcap", type=float, default=5e9, help="最小总市值（含），单位：元")
    fetch_parser.add_argument("--max-mktcap", type=float, default=float("+inf"), help="最大总市值（含），单位：元，默认无限制")
    fetch_parser.add_argument("--start", default="20190101", help="起始日期 YYYYMMDD 或 'today'")
    fetch_parser.add_argument("--end", default="today", help="结束日期 YYYYMMDD 或 'today'")
    fetch_parser.add_argument("--out", default="./data", help="输出目录")
    fetch_parser.add_argument("--workers", type=int, default=3, help="并发线程数")
    
    # 选股子命令
    select_parser = subparsers.add_parser("select", help="运行选股策略")
    select_parser.add_argument("--data-dir", default="./data", help="CSV 行情目录")
    select_parser.add_argument("--config", default="./configs.json", help="Selector 配置文件")
    select_parser.add_argument("--date", help="交易日 YYYY-MM-DD；缺省=数据最新日期")
    select_parser.add_argument("--tickers", default="all", help="'all' 或逗号分隔股票代码列表")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        fetch.main()
    elif args.command == "select":
        select.main()
    elif args.command == "init":
        init.init_project(args.data_dir)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()