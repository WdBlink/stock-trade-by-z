#!/bin/bash

# 运行详细测试脚本并将输出重定向到文件
python /Users/echooo/Documents/Code/github_star/StockTradebyZ/test_detailed.py > /Users/echooo/Documents/Code/github_star/StockTradebyZ/test_detailed_output.txt 2>&1

# 显示输出文件内容
echo "\n详细测试输出结果:"
cat /Users/echooo/Documents/Code/github_star/StockTradebyZ/test_detailed_output.txt