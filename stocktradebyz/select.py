from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd
import tushare as ts

# ---------- 日志 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        # 将日志写入文件
        logging.FileHandler("select_results.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("select")

# Tushare token 配置
ts_token = "239022239ebb827ebf20e8a87fc68f0c7c851b42593c5dddc5451c75"
ts.set_token(ts_token)
pro = ts.pro_api()


# ---------- 工具 ----------

def load_data(data_dir: Path, codes: Iterable[str]) -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for code in codes:
        fp = data_dir / f"{code}.csv"
        if not fp.exists():
            logger.warning("%s 不存在，跳过", fp.name)
            continue
        df = pd.read_csv(fp, parse_dates=["date"]).sort_values("date")
        frames[code] = df
    return frames


def load_config(cfg_path: Path) -> List[Dict[str, Any]]:
    try:
        from stocktradebyz.config.utils import load_config as load_cfg
        return load_cfg(cfg_path)
    except ImportError:
        # 兼容旧版本
        if not cfg_path.exists():
            logger.error("配置文件 %s 不存在", cfg_path)
            sys.exit(1)
        with cfg_path.open(encoding="utf-8") as f:
            cfg_raw = json.load(f)

        # 兼容三种结构：单对象、对象数组、或带 selectors 键
        if isinstance(cfg_raw, list):
            cfgs = cfg_raw
        elif isinstance(cfg_raw, dict) and "selectors" in cfg_raw:
            cfgs = cfg_raw["selectors"]
        else:
            cfgs = [cfg_raw]

        if not cfgs:
            logger.error("configs.json 未定义任何 Selector")
            sys.exit(1)

        return cfgs


def instantiate_selector(cfg: Dict[str, Any]):
    """动态加载 Selector 类并实例化"""
    cls_name: str = cfg.get("class")
    if not cls_name:
        raise ValueError("缺少 class 字段")

    try:
        module = importlib.import_module("stocktradebyz.selector")
        cls = getattr(module, cls_name)
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(f"无法加载 stocktradebyz.selector.{cls_name}: {e}") from e

    params = cfg.get("params", {})
    return cfg.get("alias", cls_name), cls(**params)


def _to_ts_code(code: str) -> str:
    """将股票代码转换为 Tushare 格式
    
    Args:
        code: 股票代码，如 '000001'
        
    Returns:
        Tushare 格式的股票代码，如 '000001.SZ'
    """
    return f"{code.zfill(6)}.SH" if code.startswith(("60", "68", "9")) else f"{code.zfill(6)}.SZ"


def get_stock_basic_info(picks: List[str]) -> None:
    """获取并打印股票基本信息
    
    Args:
        picks: 筛选出的股票代码列表
    """
    if not picks:
        return
        
    logger.info("")
    logger.info("============== 股票基本信息 ==============")
    
    for code in picks:
        try:
            ts_code = _to_ts_code(code)
            
            # 获取股票基本信息
            basic_info = pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,area,industry,market,list_date')
            
            # 获取最新的财务指标（包含市盈率等）
            daily_basic = pro.daily_basic(ts_code=ts_code, trade_date='', fields='ts_code,pe,pb,ps,dv_ratio,total_mv')
            
            # 获取公司简介
            company_info = pro.stock_company(ts_code=ts_code, fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province,city,introduction,website,email,office,employees,main_business,business_scope')
            
            if not basic_info.empty:
                stock_info = basic_info.iloc[0]
                logger.info(f"股票代码: {code} ({stock_info['name']})")
                logger.info(f"所属行业: {stock_info['industry']}")
                logger.info(f"所属地区: {stock_info['area']}")
                logger.info(f"上市日期: {stock_info['list_date']}")
                
            if not daily_basic.empty:
                financial_info = daily_basic.iloc[0]
                logger.info(f"市盈率(PE): {financial_info['pe'] if pd.notna(financial_info['pe']) else 'N/A'}")
                logger.info(f"市净率(PB): {financial_info['pb'] if pd.notna(financial_info['pb']) else 'N/A'}")
                logger.info(f"市销率(PS): {financial_info['ps'] if pd.notna(financial_info['ps']) else 'N/A'}")
                logger.info(f"总市值(万元): {financial_info['total_mv'] if pd.notna(financial_info['total_mv']) else 'N/A'}")
                
            if not company_info.empty:
                company = company_info.iloc[0]
                logger.info(f"董事长: {company['chairman'] if pd.notna(company['chairman']) else 'N/A'}")
                logger.info(f"总经理: {company['manager'] if pd.notna(company['manager']) else 'N/A'}")
                logger.info(f"注册资本: {company['reg_capital'] if pd.notna(company['reg_capital']) else 'N/A'}")
                logger.info(f"员工人数: {company['employees'] if pd.notna(company['employees']) else 'N/A'}")
                logger.info(f"主营业务: {company['main_business'][:100] + '...' if pd.notna(company['main_business']) and len(str(company['main_business'])) > 100 else company['main_business'] if pd.notna(company['main_business']) else 'N/A'}")
                
                # 公司简介（截取前200字符）
                introduction = company['introduction']
                if pd.notna(introduction) and introduction:
                    intro_text = str(introduction)[:200] + '...' if len(str(introduction)) > 200 else str(introduction)
                    logger.info(f"公司简介: {intro_text}")
                else:
                    logger.info("公司简介: N/A")
                    
            logger.info("-" * 50)
            
        except Exception as e:
            logger.warning(f"获取股票 {code} 基本信息失败: {e}")
            continue


# ---------- 主函数 ----------

def main():
    p = argparse.ArgumentParser(description="Run selectors defined in configs.json")
    p.add_argument("--data-dir", default="./data", help="CSV 行情目录")
    p.add_argument("--config", default="./configs.json", help="Selector 配置文件")
    p.add_argument("--date", help="交易日 YYYY-MM-DD；缺省=数据最新日期")
    p.add_argument("--tickers", default="all", help="'all' 或逗号分隔股票代码列表")
    args = p.parse_args()

    # --- 加载行情 ---
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error("数据目录 %s 不存在", data_dir)
        sys.exit(1)

    codes = (
        [f.stem for f in data_dir.glob("*.csv")]
        if args.tickers.lower() == "all"
        else [c.strip() for c in args.tickers.split(",") if c.strip()]
    )
    if not codes:
        logger.error("股票池为空！")
        sys.exit(1)

    data = load_data(data_dir, codes)
    if not data:
        logger.error("未能加载任何行情数据")
        sys.exit(1)

    trade_date = (
        pd.to_datetime(args.date)
        if args.date
        else max(df["date"].max() for df in data.values())
    )
    if not args.date:
        logger.info("未指定 --date，使用最近日期 %s", trade_date.date())

    # --- 加载 Selector 配置 ---
    selector_cfgs = load_config(Path(args.config))

    # --- 逐个 Selector 运行 ---
    for cfg in selector_cfgs:
        if cfg.get("activate", True) is False:
            continue
        try:
            alias, selector = instantiate_selector(cfg)
        except Exception as e:
            logger.error("跳过配置 %s：%s", cfg, e)
            continue

        picks = selector.select(trade_date, data)

        # 将结果写入日志，同时输出到控制台
        logger.info("")
        logger.info("============== 选股结果 [%s] ==============", alias)
        logger.info("交易日: %s", trade_date.date())
        logger.info("符合条件股票数: %d", len(picks))
        logger.info("%s", ", ".join(picks) if picks else "无符合条件股票")
        
        # 获取并打印股票基本信息
        if picks:
            get_stock_basic_info(picks)


if __name__ == "__main__":
    main()