#!/bin/bash

# 运行测试脚本并将输出重定向到文件
python /Users/echooo/Documents/Code/github_star/StockTradebyZ/test_simple.py > /Users/echooo/Documents/Code/github_star/StockTradebyZ/test_simple_output.txt 2>&1

# 显示输出文件内容
echo "\n测试输出结果:"
cat /Users/echooo/Documents/Code/github_star/StockTradebyZ/test_simple_output.txt