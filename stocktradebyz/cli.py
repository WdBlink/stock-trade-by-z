#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""命令行入口"""

import sys
from stocktradebyz import fetch, select


def fetch_kline():
    """抓取K线数据的命令行入口"""
    fetch.main()


def select_stock():
    """选股的命令行入口"""
    select.main()


if __name__ == "__main__":
    print("请使用 'fetch-kline' 或 'select-stock' 命令")
    sys.exit(1)