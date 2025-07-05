# 测试目录

本目录包含 StockTradebyZ 项目的测试代码，按照不同的测试类型进行组织。

## 目录结构

```
tests/
├── __init__.py           # 测试包初始化文件
├── functional/           # 功能测试目录
│   ├── __init__.py       # 功能测试包初始化文件
│   ├── test_detailed.py  # 详细功能测试
│   ├── test_import.py    # 导入测试
│   └── test_simple.py    # 简单功能测试
├── integration/          # 集成测试目录
│   ├── __init__.py       # 集成测试包初始化文件
│   └── test_selector_detailed.py  # 选股器详细集成测试
├── outputs/              # 测试输出目录
│   └── ...               # 各种测试输出文件
├── run_all_tests.sh      # 运行所有测试的脚本
└── unit/                 # 单元测试目录
    ├── __init__.py       # 单元测试包初始化文件
    └── test_selector.py  # 选股器单元测试
```

## 测试类型

1. **单元测试 (unit)**：测试单个组件的功能，如选股器的基本功能。
2. **集成测试 (integration)**：测试多个组件之间的交互，如选股器与数据的集成。
3. **功能测试 (functional)**：测试整个系统的功能，如完整的选股流程。

## 运行测试

### 运行所有测试

```bash
./tests/run_all_tests.sh
```

### 运行单个测试

```bash
# 运行单元测试
python -m tests.unit.test_selector

# 运行集成测试
python -m tests.integration.test_selector_detailed

# 运行功能测试
python -m tests.functional.test_simple
python -m tests.functional.test_detailed
python -m tests.functional.test_import
```

## 测试输出

所有测试的输出文件都保存在 `tests/outputs/` 目录中，包括日志文件和测试结果文件。