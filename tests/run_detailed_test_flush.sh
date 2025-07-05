#!/bin/bash

# 运行详细测试脚本并将输出重定向到文件
python -u test_detailed.py > test_detailed_output_flush.txt 2>&1

# 显示输出文件内容
cat test_detailed_output_flush.txt