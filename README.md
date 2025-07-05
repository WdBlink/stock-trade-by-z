# Z哥战法的Python实现

> **更新时间：2025-07-03** – 增加填坑战法。

---

## 目录

* [项目简介](#项目简介)
* [快速上手](#快速上手)

  * [安装依赖](#安装依赖)
  * [初始化项目](#初始化项目)
  * [Tushare Token（可选）](#tushare-token可选)
  * [Mootdx 运行前置步骤](#mootdx-运行前置步骤)
  * [下载历史行情](#下载历史行情)
  * [运行选股](#运行选股)
* [参数说明](#参数说明)

  * [命令行工具](#命令行工具)
  * [K 线频率编码](#k-线频率编码)
  * [内置策略参数](#内置策略参数)

    * [1. BBIKDJSelector（少妇战法）](#1-bbikdjselector少妇战法)
    * [2. PeakKDJSelector（填坑战法）](#2-peakkdjselector填坑战法)
    * [3. BBIShortLongSelector（补票战法）](#3-bbishortlongselector补票战法)
    * [4. BreakoutVolumeKDJSelector（TePu 战法）](#4-breakoutvolumekdjselectortepu-战法)
* [项目结构](#项目结构)
* [免责声明](#免责声明)

---

## 项目简介

一个基于Python的A股量化选股工具，包含以下功能：

| 名称                    | 功能简介                                                                                                             |
| --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **`fetch-kline`**  | *按市值筛选* A 股股票，并抓取其**历史 K 线**保存为 CSV。支持 **AkShare / Tushare / Mootdx** 三大数据源，自动增量更新、多线程下载。*本版本不再保存市值快照*，每次运行实时拉取。 |
| **`select-stock`** | 读取本地 CSV 行情，依据 `configs.json` 中的 **Selector** 定义批量选股，结果输出到 `select_results.log` 与控制台。                            |

内置策略：

* **BBIKDJSelector**（少妇战法）
* **PeakKDJSelector**（填坑战法）
* **BBIShortLongSelector**（补票战法）
* **BreakoutVolumeKDJSelector**（TePu 战法）

---

## 快速上手

### 安装依赖

```bash
# 使用 Poetry 安装（推荐）
pip install poetry
poetry install

# 或者使用传统方式安装
pip install -r requirements.txt
```

> 主要依赖：`akshare`、`tushare`、`mootdx`、`pandas`、`tqdm` 等。

### 初始化项目

```bash
# 使用 Poetry 安装后
poetry run init-stocktrade

# 或者直接运行
python -m stocktradebyz.init
```

这将创建必要的目录和配置文件。

### Tushare Token（可选）

若选择 **Tushare** 作为数据源，请按以下步骤操作：

1. **注册账号**
   点击专属注册链接 [https://tushare.pro/register?reg=820660](https://tushare.pro/register?reg=820660) 完成注册。*通过该链接注册，我将获得 50 积分 – 感谢支持！*
2. **开通基础权限**
   登录后进入「**平台介绍 → 社区捐助**」，按提示捐赠 **200 元/年** 可解锁 Tushare 基础接口。
3. **获取 Token**
   打开个人主页，点击 **「接口 Token」**，复制生成的 Token。
4. **填入代码**
   在 `stocktradebyz/fetch.py` 中找到以下代码并替换：

   ```python
   ts_token = " "  # ← 替换为你的 Token
   ```

### Mootdx 运行前置步骤
**注意，Mootdx下载的数据是未复权数据，会使选股结果存在偏差，请尽量使用Tushare**  
使用 **Mootdx** 数据源前，需先探测最快行情服务器一次：

```bash
python -m mootdx bestip -vv
```

脚本将保存最佳 IP，后续抓取更稳定。

### 下载历史行情

```bash
# 使用 Poetry 安装后
poetry run fetch-kline --datasource tushare --start 20200101 --end today

# 或者直接运行
python -m stocktradebyz.cli fetch-kline --datasource tushare --start 20200101 --end today

# 或者使用主入口脚本
python main.py fetch --datasource tushare --start 20200101 --end today
```

完整参数：

```bash
python main.py fetch \
  --datasource tushare      # tushare / akshare / mootdx
  --frequency 4            # K 线频率编码（4 = 日线）
  --exclude-gem            # 排除创业板 / 科创板 / 北交所
  --min-mktcap 5e9         # 最小总市值（元）
  --max-mktcap +inf        # 最大总市值（元）
  --start 20200101         # 起始日期（YYYYMMDD 或 today）
  --end today              # 结束日期
  --out ./data             # 输出目录
  --workers 3              # 并发线程数
```

*首跑* 下载完整历史；之后脚本会 **增量更新**。  

### 运行选股

```bash
# 使用 Poetry 安装后
poetry run select-stock

# 或者直接运行
python -m stocktradebyz.cli select-stock

# 或者使用主入口脚本
python main.py select
```

完整参数：

```bash
python main.py select \
  --data-dir ./data        # CSV 行情目录
  --config ./configs.json  # Selector 配置
  --date 2025-07-02        # 交易日（缺省 = 最新）
```

示例输出：

```
============== 选股结果 [填坑战法] ===============
交易日: 2025-07-02
符合条件股票数: 2
600690, 000333
```

---

## 参数说明

### 命令行工具

项目提供了以下命令行工具：

| 命令                | 说明                |
| ------------------- | ------------------- |
| `init-stocktrade`   | 初始化项目           |
| `fetch-kline`       | 抓取历史K线数据       |
| `select-stock`      | 运行选股策略         |

也可以使用主入口脚本 `main.py`：

```bash
python main.py init    # 初始化项目
python main.py fetch   # 抓取历史K线数据
python main.py select  # 运行选股策略
```

#### fetch-kline 参数

| 参数                  | 默认值      | 说明                                   |
| ------------------- | -------- | ------------------------------------ |
| `--datasource`      | `tushare` | 数据源：`tushare` / `akshare` / `mootdx` |
| `--frequency`       | `4`      | K 线频率编码（下表）                          |
| `--exclude-gem`     | flag     | 排除创业板/科创板/北交所                        |
| `--min-mktcap`      | `5e9`    | 最小总市值（元）                             |
| `--max-mktcap`      | `+inf`   | 最大总市值（元）                             |
| `--start` / `--end` | `today`  | 日期范围，`YYYYMMDD` 或 `today`            |
| `--out`             | `./data` | 输出目录                                 |
| `--workers`         | `3`     | 并发线程数                                |

#### select-stock 参数

| 参数           | 默认值              | 说明            |
| ------------ | ---------------- | ------------- |
| `--data-dir` | `./data`         | CSV 行情目录      |
| `--config`   | `./configs.json` | Selector 配置文件 |
| `--date`     | 最新交易日            | 选股日期          |
| `--tickers`  | `all`            | 股票池（逗号分隔列表）   |

### K 线频率编码

|  编码 |  周期  | Mootdx 关键字 | 用途   |
| :-: | :--: | :--------: | ---- |
|  0  |  5 分 |    `5m`    | 高频   |
|  1  | 15 分 |    `15m`   | 高频   |
|  2  | 30 分 |    `30m`   | 高频   |
|  3  | 60 分 |    `1h`    | 波段   |
|  4  |  日线  |    `day`   | ★ 常用 |
|  5  |  周线  |   `week`   | 中长线  |
|  6  |  月线  |    `mon`   | 中长线  |
|  7  |  1 分 |    `1m`    | Tick |
|  8  |  1 分 |    `1m`    | Tick |
|  9  |  日线  |    `day`   | 备用   |
|  10 |  季线  |   `3mon`   | 长周期  |
|  11 |  年线  |   `year`   | 长周期  |

### 内置策略参数

以下参数均来自 **`configs.json`**，可根据个人喜好自由调整。

#### 1. BBIKDJSelector（少妇战法）

| 参数                | 预设值    | 说明                                                  |
| ----------------- | ------ | --------------------------------------------------- |
| `j_threshold`     | `1`    | 当日 **J** 值必须 *小于* 该阈值                               |
| `bbi_min_window`  | `20`   | 检测 BBI 上升的最短窗口（交易日）                                 |
| `max_window`      | `60`   | 参与检测的最大窗口（交易日）                                      |
| `price_range_pct` | `0.5`  | 最近 *max\_window* 根 K 线内，收盘价最大波动（`high/low−1`）不得超过此值 |
| `bbi_q_threshold` | `0.1`  | 允许 BBI 一阶差分为负的分位阈值（回撤容忍度）                           |
| `j_q_threshold`   | `0.10` | 当日 **J** 值需 *不高于* 最近窗口内该分位数                         |

#### 2. PeakKDJSelector（填坑战法）

| 参数               | 预设值    | 说明                                                              |
| ---------------- | ------ | --------------------------------------------------------------- |
| `j_threshold`    | `10`   | 当日 **J** 值必须 *小于* 该阈值                                           |
| `max_window`     | `100`  | 参与检测的最大窗口（交易日）                                                  |
| `fluc_threshold` | `0.03` | 当日收盘价与坑口的最大允许波动率                               |
| `gap_threshold`  | `0.2`  | 要求坑口高于区间最低收盘价的幅度（`oc_prev > min_close × (1+gap_threshold)`） |
| `j_q_threshold`  | `0.10` | 当日 **J** 值需 *不高于* 最近窗口内该分位数                                     |

#### 3. BBIShortLongSelector（补票战法）

| 参数                | 预设值   | 说明                      |
| ----------------- | ----- | ----------------------- |
| `n_short`         | `3`   | 计算短周期 **RSV** 的窗口（交易日）  |
| `n_long`          | `21`  | 计算长周期 **RSV** 的窗口（交易日）  |
| `m`               | `3`   | 最近 *m* 天满足短 RSV 条件的判别窗口 |
| `bbi_min_window`  | `2`   | 检测 BBI 上升的最短窗口（交易日）     |
| `max_window`      | `60`  | 参与检测的最大窗口（交易日）          |
| `bbi_q_threshold` | `0.2` | 允许 BBI 一阶差分为负的分位阈值      |

#### 4. BreakoutVolumeKDJSelector（TePu 战法）

| 参数                 | 预设值      | 说明                                                  |
| ------------------ | -------- | --------------------------------------------------- |
| `j_threshold`      | `1`      | 当日 **J** 值必须 *小于* 该阈值                               |
| `j_q_threshold`    | `0.10`   | 当日 **J** 值需 *不高于* 最近窗口内该分位数                         |
| `up_threshold`     | `3.0`    | 单日涨幅不低于该百分比，视为"突破"                                  |
| `volume_threshold` | `0.6667` | 放量日成交量需 **≥ 1/(1−volume\_threshold)** 倍于窗口内其他任意日    |
| `offset`           | `15`     | 向前回溯的突破判定窗口（交易日）                                    |
| `max_window`       | `60`     | 参与检测的最大窗口（交易日）                                      |
| `price_range_pct`  | `0.5`    | 最近 *max\_window* 根 K 线内，收盘价最大波动不得超过此值（`high/low−1`） |

---

## 项目结构

```
.
├── README.md               # 项目说明
├── pyproject.toml          # Poetry 配置文件
├── requirements.txt        # 依赖列表
├── main.py                 # 主入口脚本
├── appendix.json           # 附加股票池
├── configs.json            # Selector 配置
├── stocktradebyz/          # 包目录
│   ├── __init__.py         # 包初始化
│   ├── selector.py         # 策略实现
│   ├── fetch.py            # 行情抓取模块
│   ├── select.py           # 批量选股模块
│   ├── cli.py              # 命令行入口
│   ├── init.py             # 初始化模块
│   └── config/             # 配置目录
│       ├── __init__.py     # 配置包初始化
│       ├── utils.py        # 配置工具
│       ├── configs.json    # 默认选股配置
│       └── appendix.json   # 默认附加股票池
├── tests/                  # 测试目录
│   ├── __init__.py         # 测试包初始化文件
│   ├── README.md           # 测试说明文档
│   ├── run_all_tests.sh    # 运行所有测试的脚本
│   ├── functional/         # 功能测试目录
│   ├── integration/        # 集成测试目录
│   ├── outputs/            # 测试输出目录
│   └── unit/               # 单元测试目录
├── data/                   # CSV 数据输出目录
├── fetch.log               # 抓取日志
└── select_results.log      # 选股日志
```

---

## 免责声明

* 本仓库仅供学习与技术研究之用，**不构成任何投资建议**。股市有风险，入市需审慎。
* 致谢 **@Zettaranc** 在 Bilibili 的无私分享：[https://b23.tv/JxIOaNE](https://b23.tv/JxIOaNE)
