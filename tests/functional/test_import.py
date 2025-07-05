#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试导入和基本功能
"""

import sys
import os
from pathlib import Path

# 使用相对导入路径
sys.path.append(str(Path(__file__).parent.parent.parent))

print("Python版本:", sys.version)
print("当前工作目录:", os.getcwd())
print("sys.path:", sys.path)

try:
    print("\n尝试导入 Selector 模块...")
    from Selector import BBIKDJSelector, BBIShortLongSelector, BreakoutVolumeKDJSelector, PeakKDJSelector
    print("成功导入 Selector 模块")
except Exception as e:
    print(f"导入 Selector 模块失败: {e}")

try:
    print("\n尝试导入 pandas...")
    import pandas as pd
    print("成功导入 pandas")
except Exception as e:
    print(f"导入 pandas 失败: {e}")

try:
    print("\n尝试列出 data 目录中的文件...")
    data_dir = str(Path(__file__).parent.parent.parent / "data")
    print(f"data 目录路径: {data_dir}")
    files = os.listdir(data_dir)
    print(f"data 目录中的文件: {files}")
except Exception as e:
    print(f"列出 data 目录中的文件失败: {e}")