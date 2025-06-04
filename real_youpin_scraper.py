#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品真实价格爬虫

直接从悠悠有品网站获取真实的最低价格
"""

import asyncio
import aiohttp
import re
import json
import time
import logging
from typing import Optional, Dict, List
from urllib.parse import quote
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealYoupinScraper:
    """悠悠有品真实价格爬虫"""
    
    def __init__(self):
        self.base_url = "https://www.youpin898.com"
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=3, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=15)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def search_item_price(self, item_name: str) -> Optional[float]:
        """搜索商品的真实价格"""
        try:
            # 1. 首先尝试搜索页面
            price = await self._search_via_search_page(item_name)
            if price:
                return price
            
            # 2. 尝试商品列表页面
            price = await self._search_via_goods_page(item_name)
            if price:
                return price
            
            # 3. 如果都失败，返回None
            logger.warning(f"无法获取 {item_name} 的真实价格")
            return None
            
        except Exception as e:
            logger.error(f"获取商品价格失败 ({item_name}): {e}")
            return None
    
    async def _search_via_search_page(self, item_name: str) -> Optional[float]:
        """通过搜索页面获取价格"""
        try:
            # 构建搜索URL
            search_url = f"{self.base_url}/search"
            params = {'keyword': item_name}
            
            # 添加随机延迟避免被检测
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # 从HTML中提取价格
                    price = self._extract_price_from_html(html)
                    if price:
                        logger.info(f"通过搜索页面获取 {item_name} 价格: ¥{price}")
                        return price
                        
        except Exception as e:
            logger.error(f"搜索页面获取价格失败: {e}")
        
        return None
    
    async def _search_via_goods_page(self, item_name: str) -> Optional[float]:
        """通过商品页面获取价格"""
        try:
            # 尝试访问商品列表页面
            goods_url = f"{self.base_url}/goods"
            params = {'search': item_name}
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            async with self.session.get(goods_url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    price = self._extract_price_from_html(html)
                    if price:
                        logger.info(f"通过商品页面获取 {item_name} 价格: ¥{price}")
                        return price
                        
        except Exception as e:
            logger.error(f"商品页面获取价格失败: {e}")
        
        return None
    
    def _extract_price_from_html(self, html: str) -> Optional[float]:
        """从HTML中提取价格信息"""
        try:
            # 价格提取模式，按优先级排序
            price_patterns = [
                # 常见的价格模式
                r'¥\s*(\d+\.?\d*)',
                r'price["\']?\s*[:=]\s*["\']?(\d+\.?\d*)["\']?',
                r'售价[：:]\s*¥?\s*(\d+\.?\d*)',
                r'最低价[：:]\s*¥?\s*(\d+\.?\d*)',
                r'起售价[：:]\s*¥?\s*(\d+\.?\d*)',
                # JSON数据中的价格
                r'"price"\s*:\s*(\d+\.?\d*)',
                r'"sell_price"\s*:\s*(\d+\.?\d*)',
                r'"min_price"\s*:\s*(\d+\.?\d*)',
                r'"lowest_price"\s*:\s*(\d+\.?\d*)',
                # 其他可能的模式
                r'data-price\s*=\s*["\'](\d+\.?\d*)["\']',
                r'class="price"[^>]*>¥?\s*(\d+\.?\d*)',
                r'class="sell-price"[^>]*>¥?\s*(\d+\.?\d*)',
            ]
            
            found_prices = []
            
            for pattern in price_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match)
                        if 1 <= price <= 50000:  # 合理的价格范围
                            found_prices.append(price)
                    except ValueError:
                        continue
            
            if found_prices:
                # 返回最低价格
                min_price = min(found_prices)
                logger.debug(f"找到价格: {found_prices}, 返回最低价: {min_price}")
                return min_price
            
            return None
            
        except Exception as e:
            logger.error(f"提取价格失败: {e}")
            return None
    
    async def batch_get_prices(self, item_names: List[str]) -> Dict[str, Optional[float]]:
        """批量获取商品价格"""
        prices = {}
        
        for i, item_name in enumerate(item_names):
            logger.info(f"获取第 {i+1}/{len(item_names)} 个商品价格: {item_name}")
            
            price = await self.search_item_price(item_name)
            prices[item_name] = price
            
            # 控制请求频率，避免被封
            if i < len(item_names) - 1:
                delay = random.uniform(2, 4)  # 2-4秒随机延迟
                await asyncio.sleep(delay)
        
        return prices

# 使用Steam市场作为备用价格源
class SteamMarketClient:
    """Steam市场价格客户端"""
    
    def __init__(self):
        self.base_url = "https://steamcommunity.com/market/priceoverview"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_price(self, item_name: str) -> Optional[float]:
        """获取Steam市场价格"""
        try:
            params = {
                'appid': 730,  # CS:GO
                'currency': 23,  # CNY (人民币)
                'market_hash_name': item_name
            }
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success'):
                        # 获取最低价格
                        lowest_price = data.get('lowest_price', '')
                        if lowest_price:
                            # 提取价格数字
                            price_match = re.search(r'¥\s*(\d+\.?\d*)', lowest_price)
                            if price_match:
                                price = float(price_match.group(1))
                                logger.info(f"Steam市场价格 {item_name}: ¥{price}")
                                return price
            
            return None
            
        except Exception as e:
            logger.error(f"获取Steam价格失败 ({item_name}): {e}")
            return None

# 组合价格获取器
class RealPriceCollector:
    """真实价格收集器"""
    
    def __init__(self):
        self.youpin_scraper = RealYoupinScraper()
        self.steam_client = SteamMarketClient()
    
    async def get_real_price(self, item_name: str) -> Optional[float]:
        """获取真实价格（优先悠悠有品，备用Steam）"""
        try:
            async with self.youpin_scraper:
                # 首先尝试悠悠有品
                youpin_price = await self.youpin_scraper.search_item_price(item_name)
                if youpin_price:
                    return youpin_price
            
            async with self.steam_client:
                # 备用Steam市场
                steam_price = await self.steam_client.get_price(item_name)
                if steam_price:
                    logger.info(f"使用Steam价格作为 {item_name} 的备用价格")
                    return steam_price
            
            return None
            
        except Exception as e:
            logger.error(f"获取真实价格失败 ({item_name}): {e}")
            return None

# 测试函数
async def test_real_price_scraper():
    """测试真实价格爬虫"""
    print("🎯 测试悠悠有品真实价格获取")
    print("="*50)
    
    test_items = [
        "AK-47 | 红线 (略有磨损)",
        "M4A4 | 龙王 (崭新出厂)",
        "AWP | 二西莫夫 (略有磨损)",
    ]
    
    collector = RealPriceCollector()
    
    for item in test_items:
        print(f"🔍 获取 {item} 的真实价格...")
        price = await collector.get_real_price(item)
        
        if price:
            print(f"✅ 真实价格: ¥{price}")
        else:
            print(f"❌ 无法获取价格")
        print()

if __name__ == "__main__":
    asyncio.run(test_real_price_scraper()) 