#!/bin/bash

# 运行所有测试的主脚本

# 设置工作目录为项目根目录
cd "$(dirname "$0")/.." || exit

echo "===== 运行单元测试 ====="
python -m tests.unit.test_selector

echo "\n===== 运行集成测试 ====="
python -m tests.integration.test_selector_detailed

echo "\n===== 运行功能测试 ====="
python -m tests.functional.test_simple
python -m tests.functional.test_detailed
python -m tests.functional.test_import

echo "\n所有测试完成！"