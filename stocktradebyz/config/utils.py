#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""配置文件工具"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List


def get_default_config_path(filename: str) -> Path:
    """获取默认配置文件路径"""
    return Path(__file__).parent / filename


def load_config(config_path: Path = None) -> List[Dict[str, Any]]:
    """加载选股器配置
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认配置
        
    Returns:
        配置列表
    """
    if config_path is None:
        config_path = get_default_config_path("configs.json")
        
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件 {config_path} 不存在")
        
    with config_path.open(encoding="utf-8") as f:
        cfg_raw = json.load(f)

    # 兼容三种结构：单对象、对象数组、或带 selectors 键
    if isinstance(cfg_raw, list):
        cfgs = cfg_raw
    elif isinstance(cfg_raw, dict) and "selectors" in cfg_raw:
        cfgs = cfg_raw["selectors"]
    else:
        cfgs = [cfg_raw]

    if not cfgs:
        raise ValueError(f"{config_path} 未定义任何 Selector")

    return cfgs


def load_appendix(appendix_path: Path = None) -> List[str]:
    """加载附加股票池
    
    Args:
        appendix_path: 附加股票池配置文件路径，如果为None则使用默认配置
        
    Returns:
        股票代码列表
    """
    if appendix_path is None:
        appendix_path = get_default_config_path("appendix.json")
        
    if not appendix_path.exists():
        return []
        
    with appendix_path.open(encoding="utf-8") as f:
        data = json.load(f)
        
    return data.get("data", [])


def copy_default_configs(target_dir: str) -> None:
    """复制默认配置文件到指定目录
    
    Args:
        target_dir: 目标目录
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    # 复制默认配置文件
    shutil.copy2(get_default_config_path("configs.json"), target_path / "configs.json")
    shutil.copy2(get_default_config_path("appendix.json"), target_path / "appendix.json")