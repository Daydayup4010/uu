#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品完整API客户端

基于真实curl命令的完整实现，包含所有必要的认证头
"""

import asyncio
import aiohttp
import json
import re
import logging
import uuid
import time
from typing import Optional, Dict, List
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YoupinCompleteAPI:
    """悠悠有品完整API客户端"""
    
    def __init__(self, authorization_token: Optional[str] = None):
        self.api_base = "https://api.youpin898.com"
        self.web_base = "https://www.youpin898.com"
        self.session = None
        
        # 从curl命令中提取的设备信息
        self.device_id = "5b38ebeb-5a5b-4b1a-afe9-b51edbbb8e01"
        self.device_uk = "5FL1Llbg5qN4z5LjXWo7VlMewPJ7hWEHtwHQpvWQToDNErV6KwbpSj6JBBCjogH1L"
        self.uk = "5FEvkZD2PSMLMTtE0BqOfidTtuoaX9HWBIze4zzFxfdXrsajaPWS4yY5ay96BuX1M"
        self.b3 = "833f3214b9b04819a399c94ed1fab7af-2a9cab244348658f-1"
        
        # 完整的请求头（基于真实curl命令）
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
            'priority': 'u=1, i',
            'referer': f'{self.web_base}/',
            'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'secret-v': 'h5_v1',
            'traceparent': f'00-{self.b3.split("-")[0]}-{self.b3.split("-")[1]}-01',
            'tracestate': 'rum=v2&browser&hwztx6svg3@74450dd02fdbfcd&fff04f8b64f947b5a16415e7d67562b0&uid_tue2krrblr9aefu0',
            'uk': self.uk,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0'
        }
        
        # 如果提供了认证token，添加到请求头
        if authorization_token:
            self.headers['authorization'] = authorization_token
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
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
    
    async def get_market_goods(self, page_index: int = 1, page_size: int = 20) -> Optional[Dict]:
        """获取市场商品列表"""
        print(f"\n🛒 获取市场商品列表 (页码: {page_index}, 每页: {page_size})")
        
        try:
            url = f"{self.api_base}/api/homepage/pc/goods/market/querySaleTemplate"
            
            # 请求体数据（与curl命令完全一致）
            payload = {
                "listSortType": 0,
                "sortType": 0,
                "pageSize": page_size,
                "pageIndex": page_index
            }
            
            print(f"   📤 请求URL: {url}")
            print(f"   📋 请求数据: {payload}")
            print(f"   🔐 认证状态: {'有Token' if 'authorization' in self.headers else '无Token'}")
            
            async with self.session.post(url, json=payload) as response:
                print(f"   📥 响应状态: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"   ✅ 成功获取JSON数据")
                        
                        # 解析商品数据
                        goods = self._extract_goods_from_response(data)
                        if goods:
                            print(f"   🎯 成功解析 {len(goods)} 个商品:")
                            for i, item in enumerate(goods[:3]):
                                name = item.get('name', '未知商品')
                                price = item.get('price', item.get('sell_price', '未知价格'))
                                print(f"      #{i+1}: {name} - ¥{price}")
                        
                        return data
                        
                    except Exception as e:
                        print(f"   ❌ JSON解析失败: {e}")
                        text = await response.text()
                        print(f"   📄 原始响应: {text[:300]}...")
                        
                elif response.status == 401:
                    print(f"   🔐 需要登录认证")
                    error_text = await response.text()
                    print(f"   📄 错误详情: {error_text}")
                    
                elif response.status == 429:
                    print(f"   ⏰ 请求频率限制或版本问题")
                    error_text = await response.text()
                    print(f"   📄 错误详情: {error_text}")
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ 请求失败: {response.status}")
                    print(f"   📄 错误内容: {error_text[:300]}...")
                    
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
        
        return None
    
    async def search_goods_by_name(self, item_name: str) -> Optional[float]:
        """根据商品名称搜索并获取价格"""
        print(f"\n🔍 搜索商品价格: {item_name}")
        
        # 尝试从市场商品列表中搜索
        for page in range(1, 6):  # 搜索前5页
            print(f"   📄 搜索第 {page} 页...")
            
            market_data = await self.get_market_goods(page_index=page, page_size=50)
            if not market_data:
                continue
            
            goods = self._extract_goods_from_response(market_data)
            if not goods:
                continue
            
            # 在商品列表中查找匹配的商品
            for item in goods:
                if not isinstance(item, dict):
                    continue
                
                goods_name = item.get('name', '')
                if self._is_name_match(item_name, goods_name):
                    price = self._extract_price_from_item(item)
                    if price:
                        print(f"   ✅ 找到匹配商品: {goods_name} - ¥{price}")
                        return price
            
            # 避免请求过快
            await asyncio.sleep(0.5)
        
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
        
        # 关键词匹配（去除特殊字符）
        search_keywords = re.findall(r'\w+', search_lower)
        goods_keywords = re.findall(r'\w+', goods_lower)
        
        # 检查是否所有搜索关键词都在商品名称中
        if search_keywords and all(keyword in goods_keywords for keyword in search_keywords):
            return True
        
        return False
    
    async def test_api_with_auth(self):
        """测试带认证的API"""
        print(f"\n🧪 测试API功能...")
        print("="*80)
        
        # 1. 测试获取商品列表
        print(f"\n1️⃣ 测试获取商品列表")
        market_data = await self.get_market_goods(page_index=1, page_size=5)
        
        if market_data:
            print(f"   ✅ 商品列表API正常工作!")
            
            # 2. 测试搜索功能
            print(f"\n2️⃣ 测试搜索功能")
            test_items = ["AK-47", "M4A4", "AWP"]
            
            for item in test_items:
                price = await self.search_goods_by_name(item)
                if price:
                    print(f"   ✅ {item}: ¥{price}")
                else:
                    print(f"   ❌ {item}: 未找到")
        else:
            print(f"   ❌ 商品列表API无法使用")

async def test_without_auth():
    """测试不带认证的API"""
    print("🔓 测试不带认证的API...")
    
    async with YoupinCompleteAPI() as api:
        await api.test_api_with_auth()

async def test_with_auth():
    """测试带认证的API"""
    print("🔐 测试带认证的API...")
    
    # 使用您提供的JWT token
    auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJjNmJkZTE3YjNkNWU0YWE0OTE3ZDlkYmNiNjYwOGM0ZSIsIm5hbWVpZCI6IjE2MjU2MDIiLCJJZCI6IjE2MjU2MDIiLCJ1bmlxdWVfbmFtZSI6IllQMDAwMTYyNTYwMiIsIk5hbWUiOiJZUDAwMDE2MjU2MDIiLCJ2ZXJzaW9uIjoick9YIiwibmJmIjoxNzQ4OTI0Mjk5LCJleHAiOjE3NDk3ODgyOTksImlzcyI6InlvdXBpbjg5OC5jb20iLCJkZXZpY2VJZCI6IjViMzhlYmViLTVhNWItNGIxYS1hZmU5LWI1MWVkYmJiOGUwMSIsImF1ZCI6InVzZXIifQ.NQWwc8cAZzI62iconMhg3RUiaPQNOWz1rRpaULnJKws"
    
    async with YoupinCompleteAPI(authorization_token=auth_token) as api:
        await api.test_api_with_auth()

async def main():
    """主函数"""
    print("🎯 悠悠有品完整API测试")
    print("="*80)
    print("📝 基于真实curl命令的完整实现")
    
    # 先测试不带认证
    await test_without_auth()
    
    print(f"\n" + "="*80)
    
    # 再测试带认证
    await test_with_auth()
    
    print(f"\n" + "="*80)
    print("💡 总结:")
    print("1. 如果带认证的API工作，我们就可以获取真实价格")
    print("2. 可以集成到现有的价差分析系统中")
    print("3. 需要定期更新JWT token以保持认证状态")

if __name__ == "__main__":
    asyncio.run(main()) 