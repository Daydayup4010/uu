#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品最终API客户端

经过测试验证的完整实现，包含频率控制和价格查询功能
"""

import asyncio
import aiohttp
import json
import re
import logging
import time
from typing import Optional, Dict, List
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YoupinFinalAPI:
    """悠悠有品最终API客户端"""
    
    def __init__(self):
        self.api_base = "https://api.youpin898.com"
        self.web_base = "https://www.youpin898.com"
        self.session = None
        
        # 设备信息
        self.device_id = "5b38ebeb-5a5b-4b1a-afe9-b51edbbb8e01"
        self.device_uk = "5FL1Llbg5qN4z5LjXWo7VlMewPJ7hWEHtwHQpvWQToDNErV6KwbpSj6JBBCjogH1L"
        self.uk = "5FEvkZD2PSMLMTtE0BqOfidTtuoaX9HWBIze4zzFxfdXrsajaPWS4yY5ay96BuX1M"
        self.b3 = "833f3214b9b04819a399c94ed1fab7af-2a9cab244348658f-1"
        
        # 请求头
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'app-version': '5.26.0',
            'apptype': '1',
            'appversion': '5.26.0',
            'b3': self.b3,
            'content-type': 'application/json',
            'deviceid': self.device_id,
            'deviceuk': self.device_uk,
            'origin': self.web_base,
            'platform': 'pc',
            'referer': f'{self.web_base}/',
            'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'secret-v': 'h5_v1',
            'traceparent': f'00-{self.b3.split("-")[0]}-{self.b3.split("-")[1]}-01',
            'uk': self.uk,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0'
        }
        
        # 频率控制
        self.last_request_time = 0
        self.min_interval = 2.0  # 最小请求间隔（秒）
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """频率控制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            print(f"   ⏱️ 频率控制，等待 {sleep_time:.1f} 秒...")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def get_market_goods(self, page_index: int = 1, page_size: int = 20) -> Optional[Dict]:
        """获取市场商品列表"""
        await self._rate_limit()
        
        try:
            url = f"{self.api_base}/api/homepage/pc/goods/market/querySaleTemplate"
            
            payload = {
                "listSortType": 0,
                "sortType": 0,
                "pageSize": page_size,
                "pageIndex": page_index
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    print(f"   ⚠️ 频率限制，增加延迟...")
                    self.min_interval = min(self.min_interval * 1.5, 10.0)  # 动态增加延迟
                    await asyncio.sleep(5)  # 额外等待
                    return None
                else:
                    print(f"   ❌ 请求失败: {response.status}")
                    return None
                    
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
            return None
    
    async def search_item_price(self, item_name: str) -> Optional[float]:
        """搜索商品价格"""
        print(f"\n🔍 搜索悠悠有品价格: {item_name}")
        
        # 搜索前3页，每页20个商品
        for page in range(1, 4):
            print(f"   📄 搜索第 {page} 页...")
            
            market_data = await self.get_market_goods(page_index=page, page_size=20)
            if not market_data:
                continue
            
            goods = self._extract_goods_from_response(market_data)
            if not goods:
                continue
            
            # 查找匹配的商品
            for item in goods:
                if not isinstance(item, dict):
                    continue
                
                goods_name = item.get('name', '')
                if self._is_name_match(item_name, goods_name):
                    price = self._extract_price_from_item(item)
                    if price:
                        print(f"   ✅ 找到匹配商品: {goods_name} - ¥{price}")
                        return price
        
        print(f"   ❌ 未找到商品: {item_name}")
        return None
    
    def _extract_goods_from_response(self, data: Dict) -> List[Dict]:
        """从API响应中提取商品列表"""
        if not isinstance(data, dict):
            return []
        
        # 尝试不同的数据结构路径
        possible_paths = [
            ['data', 'list'],
            ['data', 'items'],
            ['data', 'goods'],
            ['data'],
            ['list'],
            ['items'],
            ['goods']
        ]
        
        for path in possible_paths:
            current = data
            try:
                for key in path:
                    current = current[key]
                
                if isinstance(current, list):
                    return current
                elif isinstance(current, dict) and 'list' in current:
                    return current['list']
                    
            except (KeyError, TypeError):
                continue
        
        return []
    
    def _extract_price_from_item(self, item: Dict) -> Optional[float]:
        """从商品项中提取价格"""
        price_fields = [
            'price', 'sell_price', 'lowest_price', 'min_price',
            'current_price', 'market_price', 'sale_price'
        ]
        
        for field in price_fields:
            if field in item:
                try:
                    price = float(item[field])
                    if price > 0:
                        return price
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _is_name_match(self, search_name: str, goods_name: str) -> bool:
        """检查商品名称是否匹配"""
        if not search_name or not goods_name:
            return False
        
        # 转换为小写进行比较
        search_lower = search_name.lower()
        goods_lower = goods_name.lower()
        
        # 精确匹配
        if search_lower == goods_lower:
            return True
        
        # 包含匹配
        if search_lower in goods_lower:
            return True
        
        # 关键词匹配
        search_keywords = re.findall(r'\w+', search_lower)
        goods_keywords = re.findall(r'\w+', goods_lower)
        
        # 检查是否所有搜索关键词都在商品名称中
        if search_keywords and all(keyword in goods_keywords for keyword in search_keywords):
            return True
        
        return False
    
    async def batch_get_prices(self, item_names: List[str]) -> Dict[str, Optional[float]]:
        """批量获取商品价格"""
        prices = {}
        
        for i, item_name in enumerate(item_names):
            print(f"\n📊 批量获取价格 {i+1}/{len(item_names)}")
            
            price = await self.search_item_price(item_name)
            prices[item_name] = price
        
        return prices

# 测试函数
async def test_youpin_final_api():
    """测试最终版本的悠悠有品API"""
    print("🎯 测试悠悠有品最终API客户端")
    print("="*80)
    
    test_items = [
        "AK-47 | 红线",
        "M4A4 | 龙王", 
        "AWP | 二西莫夫",
    ]
    
    async with YoupinFinalAPI() as client:
        print(f"\n🧪 单个商品测试:")
        for item in test_items:
            price = await client.search_item_price(item)
            
            if price:
                print(f"✅ {item}: ¥{price}")
            else:
                print(f"❌ {item}: 未找到")
        
        print(f"\n📊 批量测试:")
        batch_prices = await client.batch_get_prices(test_items[:2])
        
        for item, price in batch_prices.items():
            if price:
                print(f"✅ {item}: ¥{price}")
            else:
                print(f"❌ {item}: 获取失败")

if __name__ == "__main__":
    asyncio.run(test_youpin_final_api()) 