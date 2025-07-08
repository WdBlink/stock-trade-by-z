from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import random
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

import akshare as ak
import pandas as pd
import tushare as ts
from mootdx.quotes import Quotes
from tqdm import tqdm

warnings.filterwarnings("ignore")

# --------------------------- 全局日志配置 --------------------------- #
LOG_FILE = Path("fetch.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("fetch_mktcap")

# 屏蔽第三方库多余 INFO 日志
for noisy in ("httpx", "urllib3", "_client", "akshare"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# --------------------------- 市值快照 --------------------------- #

def _get_mktcap_ak() -> pd.DataFrame:
    """实时快照，返回列：code, mktcap（单位：元）"""
    for attempt in range(1, 4):
        try:
            df = ak.stock_zh_a_spot_em()
            break
        except Exception as e:
            logger.warning("AKShare 获取市值快照失败(%d/3): %s", attempt, e)
            time.sleep(backoff := random.uniform(1, 3) * attempt)
    else:
        raise RuntimeError("AKShare 连续三次拉取市值快照失败！")

    df = df[["代码", "总市值"]].rename(columns={"代码": "code", "总市值": "mktcap"})
    df["mktcap"] = pd.to_numeric(df["mktcap"], errors="coerce")
    return df

# --------------------------- 股票池筛选 --------------------------- #

def get_constituents(
    min_cap: float,
    max_cap: float,
    small_player: bool,
    mktcap_df: Optional[pd.DataFrame] = None,
) -> List[str]:
    df = mktcap_df if mktcap_df is not None else _get_mktcap_ak()

    cond = (df["mktcap"] >= min_cap) & (df["mktcap"] <= max_cap)
    if small_player:
        cond &= ~df["code"].str.startswith(("300", "301", "688", "8", "4"))

    codes = df.loc[cond, "code"].str.zfill(6).tolist()

    # 附加股票池 appendix.json
    try:
        with open("appendix.json", "r", encoding="utf-8") as f:
            appendix_codes = json.load(f)["data"]
    except FileNotFoundError:
        appendix_codes = []
    codes = list(dict.fromkeys(appendix_codes + codes))  # 去重保持顺序

    logger.info("筛选得到 %d 只股票", len(codes))
    return codes

# --------------------------- 历史 K 线抓取 --------------------------- #
COLUMN_MAP_HIST_AK = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "换手率": "turnover",
}

_FREQ_MAP = {
    0: "5m",
    1: "15m",
    2: "30m",
    3: "1h",
    4: "day",
    5: "week",
    6: "mon",
    7: "1m",
    8: "1m",
    9: "day",
    10: "3mon",
    11: "year",
}

# ---------- Tushare 工具函数 ---------- #

def _to_ts_code(code: str) -> str:
    return f"{code.zfill(6)}.SH" if code.startswith(("60", "68", "9")) else f"{code.zfill(6)}.SZ"


def _get_kline_tushare(code: str, start: str, end: str, adjust: str) -> pd.DataFrame:
    ts_code = _to_ts_code(code)
    adj_flag = None if adjust == "" else adjust
    for attempt in range(1, 4):
        try:
            df = ts.pro_bar(
                ts_code=ts_code,
                adj=adj_flag,
                start_date=start,
                end_date=end,
                freq="D",
            )
            break
        except Exception as e:
            logger.warning("Tushare 拉取 %s 失败(%d/3): %s", code, attempt, e)
            time.sleep(random.uniform(1, 2) * attempt)
    else:
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.rename(columns={"trade_date": "date", "vol": "volume"})[
        ["date", "open", "close", "high", "low", "volume"]
    ].copy()
    df["date"] = pd.to_datetime(df["date"])
    df[[c for c in df.columns if c != "date"]] = df[[c for c in df.columns if c != "date"]].apply(
        pd.to_numeric, errors="coerce"
    )    
    return df.sort_values("date").reset_index(drop=True)

# ---------- AKShare 工具函数 ---------- #

def _get_kline_akshare(code: str, start: str, end: str, adjust: str) -> pd.DataFrame:
    for attempt in range(1, 4):
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start,
                end_date=end,
                adjust=adjust,
            )
            break
        except Exception as e:
            logger.warning("AKShare 拉取 %s 失败(%d/3): %s", code, attempt, e)
            time.sleep(random.uniform(1, 2) * attempt)
    else:
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    df = (
        df[list(COLUMN_MAP_HIST_AK)]
        .rename(columns=COLUMN_MAP_HIST_AK)
        .assign(date=lambda x: pd.to_datetime(x["date"]))
    )
    df[[c for c in df.columns if c != "date"]] = df[[c for c in df.columns if c != "date"]].apply(
        pd.to_numeric, errors="coerce"
    )
    df = df[["date", "open", "close", "high", "low", "volume"]]
    return df.sort_values("date").reset_index(drop=True)

# ---------- 港股 AKShare 工具函数 ---------- #

def _get_kline_hk_akshare(code: str, start: str, end: str, adjust: str) -> pd.DataFrame:
    """获取港股历史K线数据
    
    Args:
        code: 港股代码，例如 "00700"（腾讯控股）
        start: 开始日期，格式为 YYYYMMDD
        end: 结束日期，格式为 YYYYMMDD
        adjust: 复权类型，可选值为 "qfq"（前复权）、"hfq"（后复权）或 ""（不复权）
        
    Returns:
        包含日期、开盘价、收盘价、最高价、最低价和成交量的DataFrame
    """
    logger.info("开始获取港股 %s 的历史数据，日期范围：%s 至 %s", code, start, end)
    for attempt in range(1, 4):
        try:
            logger.info("尝试调用 ak.stock_hk_hist 获取港股 %s 数据 (尝试 %d/3)", code, attempt)
            df = ak.stock_hk_hist(
                symbol=code,
                start_date=start,
                end_date=end,
                adjust=adjust,
            )
            logger.info("成功获取港股 %s 数据", code)
            break
        except Exception as e:
            logger.warning("AKShare 拉取港股 %s 失败(%d/3): %s", code, attempt, e)
            time.sleep(random.uniform(1, 2) * attempt)
    else:
        logger.error("港股 %s 数据获取失败，已尝试3次", code)
        return pd.DataFrame()

    if df is None or df.empty:
        logger.warning("港股 %s 返回的数据为空", code)
        return pd.DataFrame()
    
    logger.info("港股 %s 数据获取成功，原始数据列：%s", code, df.columns.tolist())

    # 港股数据列名可能与A股不同，需要适配
    column_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount"
    }
    
    # 确保所有需要的列都存在
    available_columns = [col for col in column_map.keys() if col in df.columns]
    
    df = (
        df[available_columns]
        .rename(columns={col: column_map[col] for col in available_columns})
        .assign(date=lambda x: pd.to_datetime(x["date"]))
    )
    
    # 确保必要的列存在
    required_columns = ["date", "open", "close", "high", "low", "volume"]
    for col in required_columns:
        if col not in df.columns:
            logger.warning(f"港股 {code} 数据缺少 {col} 列")
            return pd.DataFrame()
    
    # 转换为数值类型
    df[[c for c in df.columns if c != "date"]] = df[[c for c in df.columns if c != "date"]].apply(
        pd.to_numeric, errors="coerce"
    )
    
    df = df[required_columns]
    return df.sort_values("date").reset_index(drop=True)

# ---------- Mootdx 工具函数 ---------- #

def _get_kline_mootdx(code: str, start: str, end: str, adjust: str, freq_code: int) -> pd.DataFrame:    
    symbol = code.zfill(6)
    freq = _FREQ_MAP.get(freq_code, "day")
    client = Quotes.factory(market="std")
    try:
        df = client.bars(symbol=symbol, frequency=freq, adjust=adjust or None)
    except Exception as e:
        logger.warning("Mootdx 拉取 %s 失败: %s", code, e)
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    
    df = df.rename(
        columns={"datetime": "date", "open": "open", "high": "high", "low": "low", "close": "close", "vol": "volume"}
    )
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    start_ts = pd.to_datetime(start, format="%Y%m%d")
    end_ts = pd.to_datetime(end, format="%Y%m%d")
    df = df[(df["date"].dt.date >= start_ts.date()) & (df["date"].dt.date <= end_ts.date())].copy()    
    df = df.sort_values("date").reset_index(drop=True)    
    return df[["date", "open", "close", "high", "low", "volume"]]

# ---------- 通用接口 ---------- #

def get_kline(
    code: str,
    start: str,
    end: str,
    adjust: str,
    datasource: str,
    freq_code: int = 4,
    market: str = "A",  # 新增参数，默认为A股市场
) -> pd.DataFrame:
    logger.info("调用 get_kline 函数获取 %s 股票 %s 的数据，数据源: %s", "港" if market == "HK" else "A", code, datasource)
    # 港股市场只支持akshare数据源
    if market == "HK":
        if datasource != "akshare":
            logger.warning("港股数据目前仅支持AKShare数据源，已自动切换为AKShare")
        logger.info("开始调用 _get_kline_hk_akshare 函数获取港股 %s 数据", code)
        return _get_kline_hk_akshare(code, start, end, adjust)
    
    # A股市场支持多种数据源
    if datasource == "tushare":
        return _get_kline_tushare(code, start, end, adjust)
    elif datasource == "akshare":
        return _get_kline_akshare(code, start, end, adjust)
    elif datasource == "mootdx":        
        return _get_kline_mootdx(code, start, end, adjust, freq_code)
    else:
        raise ValueError("datasource 仅支持 'tushare', 'akshare' 或 'mootdx'")

# ---------- 数据校验 ---------- #

def validate(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
    if df["date"].isna().any():
        raise ValueError("存在缺失日期！")
    if (df["date"] > pd.Timestamp.today()).any():
        raise ValueError("数据包含未来日期，可能抓取错误！")
    return df

def drop_dup_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.duplicated()]
# ---------- 单只股票抓取 ---------- #
def fetch_one(
    code: str,
    start: str,
    end: str,
    out_dir: Path,
    incremental: bool,
    datasource: str,
    freq_code: int,
    market: str = "A",  # 新增参数，默认为A股市场
):    
    # 对于港股，文件名添加HK前缀以区分
    prefix = "HK_" if market == "HK" else ""
    csv_path = out_dir / f"{prefix}{code}.csv"
    
    logger.info("%s股票 %s 开始获取数据，输出路径: %s", "港" if market == "HK" else "A", code, csv_path)

    # 增量更新：若本地已有数据则从最后一天开始
    if incremental and csv_path.exists():
        try:
            existing = pd.read_csv(csv_path, parse_dates=["date"])
            last_date = existing["date"].max()
            if last_date.date() > pd.to_datetime(end, format="%Y%m%d").date():
                logger.debug("%s 已是最新，无需更新", code)
                return
            start = last_date.strftime("%Y%m%d")
        except Exception:
            logger.exception("读取 %s 失败，将重新下载", csv_path)

    for attempt in range(1, 4):
        try:            
            new_df = get_kline(code, start, end, "qfq", datasource, freq_code, market)
            if new_df.empty:
                logger.debug("%s 无新数据", code)
                break
            new_df = validate(new_df)
            if csv_path.exists() and incremental:
                old_df = pd.read_csv(
                    csv_path,
                    parse_dates=["date"],
                    index_col=False
                )
                old_df = drop_dup_columns(old_df)
                new_df = drop_dup_columns(new_df)
                new_df = (
                    pd.concat([old_df, new_df], ignore_index=True)
                    .drop_duplicates(subset="date")
                    .sort_values("date")
                )
            new_df.to_csv(csv_path, index=False)
            break
        except Exception:
            logger.exception("%s 第 %d 次抓取失败", code, attempt)
            time.sleep(random.uniform(1, 3) * attempt)  # 指数退避
    else:
        logger.error("%s 三次抓取均失败，已跳过！", code)


# ---------- 主入口 ---------- #

def main():
    parser = argparse.ArgumentParser(description="按市值筛选股票并抓取历史 K 线")
    parser.add_argument("--datasource", choices=["tushare", "akshare", "mootdx"], default="tushare", help="历史 K 线数据源")
    parser.add_argument("--frequency", type=int, choices=list(_FREQ_MAP.keys()), default=4, help="K线频率编码，参见说明")
    parser.add_argument("--exclude-gem", default=True, help="True则排除创业板/科创板/北交所")
    parser.add_argument("--min-mktcap", type=float, default=5e9, help="最小总市值（含），单位：元")
    parser.add_argument("--max-mktcap", type=float, default=float("+inf"), help="最大总市值（含），单位：元，默认无限制")
    parser.add_argument("--start", default="20190101", help="起始日期 YYYYMMDD 或 'today'")
    parser.add_argument("--end", default="today", help="结束日期 YYYYMMDD 或 'today'")
    parser.add_argument("--out", default="./data", help="输出目录")
    parser.add_argument("--workers", type=int, default=3, help="并发线程数")
    parser.add_argument("--include-hk", action="store_true", help="是否包含港股数据")
    parser.add_argument("--hk-codes", default="", help="港股代码列表，逗号分隔，例如：00700,02318,03690")
    args = parser.parse_args()

    # ---------- Token 处理 ---------- #
    if args.datasource == "tushare":
        ts_token = "239022239ebb827ebf20e8a87fc68f0c7c851b42593c5dddc5451c75"  # 在这里补充token
        ts.set_token(ts_token)
        global pro
        pro = ts.pro_api()

    # ---------- 日期解析 ---------- #
    start = dt.date.today().strftime("%Y%m%d") if args.start.lower() == "today" else args.start
    end = dt.date.today().strftime("%Y%m%d") if args.end.lower() == "today" else args.end

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 市值快照 & 股票池 ---------- #
    mktcap_df = _get_mktcap_ak()    

    codes_from_filter = get_constituents(
        args.min_mktcap,
        args.max_mktcap,
        args.exclude_gem,
        mktcap_df=mktcap_df,
    )    
    # 加上本地已有的股票，确保旧数据也能更新
    local_codes = [p.stem for p in out_dir.glob("*.csv")]
    codes = sorted(set(codes_from_filter) | set(local_codes))

    if not codes:
        logger.error("筛选结果为空，请调整参数！")
        sys.exit(1)

    # ---------- 处理港股代码 ---------- #
    hk_codes = []
    if args.include_hk:
        logger.info("检测到 --include-hk 参数，将获取港股数据")
        if args.hk_codes:
            # 从命令行参数获取港股代码
            hk_codes = [code.strip() for code in args.hk_codes.split(",") if code.strip()]
            logger.info("从命令行参数获取 %d 只港股: %s", len(hk_codes), hk_codes)
        else:
            # 如果没有指定港股代码，可以添加一些默认的热门港股
            default_hk_codes = ["00700", "01810", "03690", "09988", "02318", "00388", "00941", "02020"]
            hk_codes = default_hk_codes
            logger.info("使用默认的 %d 只热门港股: %s", len(hk_codes), hk_codes)
    
    # 日志输出
    market_info = "A股"
    if args.include_hk:
        market_info = "A股和港股"
    
    logger.info(
        "开始抓取 %d 支%s | 数据源:%s | 频率:%s | 日期:%s → %s",
        len(codes) + (len(hk_codes) if args.include_hk else 0),
        market_info,
        args.datasource,
        _FREQ_MAP[args.frequency],
        start,
        end,
    )
    
    # ---------- 多线程抓取 ---------- #
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # A股抓取任务
        a_futures = []
        if codes:
            logger.info("开始提交 %d 只A股抓取任务", len(codes))
            a_futures = [
                executor.submit(
                    fetch_one,
                    code,
                    start,
                    end,
                    out_dir,
                    True,
                    args.datasource,
                    args.frequency,
                    "A",  # A股市场
                )
                for code in codes
            ]
        
        # 港股抓取任务
        hk_futures = []
        if args.include_hk and hk_codes:
            logger.info("开始提交 %d 只港股抓取任务", len(hk_codes))
            # 如果只获取港股数据，则单独处理
            if not codes:
                logger.info("仅获取港股数据")
            
            hk_futures = [
                executor.submit(
                    fetch_one,
                    code,
                    start,
                    end,
                    out_dir,
                    True,
                    "akshare",  # 港股只支持akshare
                    args.frequency,
                    "HK",  # 港股市场
                )
                for code in hk_codes
            ]
        
        # 合并所有任务
        all_futures = a_futures + hk_futures
        logger.info("总共提交 %d 个抓取任务", len(all_futures))
        for _ in tqdm(as_completed(all_futures), total=len(all_futures), desc="下载进度"):
            pass

    logger.info("全部任务完成，数据已保存至 %s", out_dir.resolve())


if __name__ == "__main__":
    main()
