#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置文件
"""

import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Optional, Tuple

load_dotenv()

@dataclass
class Config:
    """系统配置类"""
    
    # 🔥 价格差异区间筛选（元）- 新功能！
    PRICE_DIFF_MIN: float = float(os.getenv('PRICE_DIFF_MIN', 3.0))    # 最小价差
    PRICE_DIFF_MAX: float = float(os.getenv('PRICE_DIFF_MAX', 5.0))    # 最大价差
    
    # 🔥 Buff饰品价格区间筛选（用于增量更新）
    BUFF_PRICE_MIN: float = float(os.getenv('BUFF_PRICE_MIN', 10.0))   # Buff最小价格
    BUFF_PRICE_MAX: float = float(os.getenv('BUFF_PRICE_MAX', 1000.0)) # Buff最大价格
    
    # 兼容性：保留原来的阈值配置
    PRICE_DIFF_THRESHOLD: float = float(os.getenv('PRICE_DIFF_THRESHOLD', 3.0))
    
    # 🔥 更新机制配置
    FULL_UPDATE_INTERVAL_HOURS: int = 1      # 全量更新间隔（小时）
    INCREMENTAL_UPDATE_INTERVAL_MINUTES: int = 1  # 增量更新间隔（分钟）
    INCREMENTAL_CACHE_SIZE: int = 1000       # 增量缓存的hashname数量
    
    # 商品数量配置 - 重新定义语义
    MAX_OUTPUT_ITEMS: int = 300          # 🔥 修改：最大输出商品数量（筛选后）
    BUFF_MAX_PAGES: int = 2000            # Buff最大获取页数
    YOUPIN_MAX_PAGES: int = 2000           # 悠悠有品最大获取页数
    MONITOR_MAX_ITEMS: int = 3000         # 监控服务处理的最大商品数量
    
    # API配置
    BUFF_PAGE_SIZE: int = 80             # Buff每页商品数量
    YOUPIN_PAGE_SIZE: int = 100          # 悠悠有品每页商品数量
    
    # 并发控制 - 已移除页面级并发控制
    # BUFF_BATCH_SIZE: int = 2             # Buff并发批次大小 - 不再需要
    # YOUPIN_BATCH_SIZE: int = 2           # 悠悠有品并发批次大小 - 不再需要
    
    # 请求间隔（秒）
    REQUEST_DELAY: float = 2.0          # 请求延迟（秒）
    RETRY_DELAY: float = 2.0             # 重试延迟
    
    # 数据存储
    DATA_DIR: str = "data"
    ITEMS_DATA_FILE: str = os.path.join(DATA_DIR, "items.json")
    DIFF_DATA_FILE: str = os.path.join(DATA_DIR, "price_diff.json")
    LATEST_DATA_FILE: str = "data/latest_price_diff.json"
    
    # 监控设置
    MONITOR_INTERVAL_MINUTES: int = 5     # 监控检查间隔（分钟）
    FULL_MONITOR_INTERVAL_HOURS: int = 1  # 完整监控间隔（小时）
    
    # 网站配置
    BUFF_BASE_URL: str = "https://buff.163.com"
    YOUPIN_BASE_URL: str = "https://www.youpin898.com"
    
    # 数据采集配置
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3                # 最大重试次数
    
    # 爬虫配置 - 使用default_factory修复mutable default问题
    USER_AGENTS: list = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ])
    
    # 监控配置
    MONITOR_INTERVAL: int = 300  # 监控间隔（秒）
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    @classmethod
    def get_price_range(cls) -> Tuple[float, float]:
        """获取价格差异区间"""
        return (cls.PRICE_DIFF_MIN, cls.PRICE_DIFF_MAX)
    
    @classmethod
    def get_buff_price_range(cls) -> Tuple[float, float]:
        """获取Buff价格筛选区间"""
        return (cls.BUFF_PRICE_MIN, cls.BUFF_PRICE_MAX)
    
    @classmethod
    def is_price_diff_in_range(cls, price_diff: float) -> bool:
        """检查价差是否在指定区间内"""
        return cls.PRICE_DIFF_MIN <= price_diff <= cls.PRICE_DIFF_MAX
    
    @classmethod
    def is_buff_price_in_range(cls, buff_price: float) -> bool:
        """检查Buff价格是否在筛选区间内"""
        return cls.BUFF_PRICE_MIN <= buff_price <= cls.BUFF_PRICE_MAX
    
    @classmethod
    def get_processing_limits(cls) -> dict:
        """获取处理限制配置"""
        return {
            'max_output_items': cls.MAX_OUTPUT_ITEMS,
            'buff_max_pages': cls.BUFF_MAX_PAGES,
            'youpin_max_pages': cls.YOUPIN_MAX_PAGES,
            'monitor_max_items': cls.MONITOR_MAX_ITEMS,
            'buff_page_size': cls.BUFF_PAGE_SIZE,
            'youpin_page_size': cls.YOUPIN_PAGE_SIZE,
            'price_range': cls.get_price_range(),
            'buff_price_range': cls.get_buff_price_range()
        }
    
    @classmethod
    def update_limits(cls, **kwargs):
        """更新处理限制"""
        for key, value in kwargs.items():
            if hasattr(cls, key.upper()):
                setattr(cls, key.upper(), value)
    
    @classmethod
    def update_price_range(cls, min_diff: float, max_diff: float):
        """更新价格差异区间"""
        cls.PRICE_DIFF_MIN = min_diff
        cls.PRICE_DIFF_MAX = max_diff
        print(f"🔄 价格差异区间已更新: {min_diff}元 - {max_diff}元")
    
    @classmethod
    def update_buff_price_range(cls, min_price: float, max_price: float):
        """更新Buff价格筛选区间"""
        cls.BUFF_PRICE_MIN = min_price
        cls.BUFF_PRICE_MAX = max_price
        print(f"🔄 Buff价格筛选区间已更新: {min_price}元 - {max_price}元")
    
    # 环境配置
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 代理设置（可选）
    HTTP_PROXY: Optional[str] = os.getenv("HTTP_PROXY")
    HTTPS_PROXY: Optional[str] = os.getenv("HTTPS_PROXY")
    
    @classmethod
    def update_threshold(cls, new_threshold: float):
        """更新价差阈值（兼容性方法）"""
        cls.PRICE_DIFF_THRESHOLD = new_threshold 