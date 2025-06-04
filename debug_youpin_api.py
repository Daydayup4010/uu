#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品API调试工具

帮助分析悠悠有品的网络请求和API接口
"""

import asyncio
import aiohttp
import json
import re
import logging
from typing import Optional, Dict, List
from urllib.parse import quote, urljoin

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class YoupinAPIDebugger:
    """悠悠有品API调试器"""
    
    def __init__(self):
        self.base_url = "https://www.youpin898.com"
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=3, ssl=False)
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_basic_connectivity(self):
        """测试基本连接"""
        print("🔗 测试悠悠有品基本连接...")
        
        try:
            async with self.session.get(self.base_url) as response:
                print(f"   状态码: {response.status}")
                print(f"   响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    html = await response.text()
                    print(f"   页面长度: {len(html)} 字符")
                    
                    # 查找可能的API端点
                    api_patterns = [
                        r'/api/[^"\'>\s]+',
                        r'api\.[^"\'>\s]+',
                        r'fetch\(["\']([^"\']+)["\']',
                        r'axios\.get\(["\']([^"\']+)["\']',
                        r'\.get\(["\']([^"\']+)["\']',
                    ]
                    
                    found_apis = set()
                    for pattern in api_patterns:
                        matches = re.findall(pattern, html)
                        found_apis.update(matches)
                    
                    if found_apis:
                        print(f"   🎯 发现可能的API端点:")
                        for api in sorted(found_apis)[:10]:
                            print(f"      {api}")
                    
                    return True
                else:
                    print(f"   ❌ 访问失败: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            return False
    
    async def test_common_endpoints(self):
        """测试常见的API端点"""
        print("\n🔍 测试常见API端点...")
        
        # 常见的端点列表
        endpoints = [
            "/api/search",
            "/api/goods",
            "/api/goods/search",
            "/api/market/search",
            "/api/v1/search",
            "/api/v2/search", 
            "/search/api",
            "/goods/api",
            "/market/api",
            "/api/items",
            "/api/products",
            "/search",
            "/goods",
        ]
        
        for endpoint in endpoints:
            await self._test_endpoint(endpoint)
    
    async def _test_endpoint(self, endpoint: str):
        """测试单个端点"""
        try:
            url = urljoin(self.base_url, endpoint)
            
            # 先尝试GET请求
            async with self.session.get(url) as response:
                print(f"   GET {endpoint}: {response.status}")
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'json' in content_type:
                        try:
                            data = await response.json()
                            print(f"      ✅ JSON响应，数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        except:
                            print(f"      ⚠️ JSON解析失败")
                    else:
                        text = await response.text()
                        print(f"      📄 HTML响应，长度: {len(text)}")
                        
                        # 检查是否包含价格信息
                        if '¥' in text or 'price' in text.lower():
                            print(f"      💰 可能包含价格信息")
                elif response.status == 404:
                    print(f"      ❌ 404 Not Found")
                else:
                    print(f"      ⚠️ 状态码: {response.status}")
                    
        except Exception as e:
            print(f"   {endpoint}: ❌ {e}")
    
    async def test_search_with_params(self):
        """测试带参数的搜索"""
        print("\n🔍 测试带参数的搜索...")
        
        search_configs = [
            {"endpoint": "/search", "params": {"keyword": "AK-47"}},
            {"endpoint": "/search", "params": {"q": "AK-47"}},
            {"endpoint": "/api/search", "params": {"keyword": "AK-47"}},
            {"endpoint": "/api/search", "params": {"q": "AK-47", "game": "csgo"}},
            {"endpoint": "/goods", "params": {"search": "AK-47"}},
            {"endpoint": "/api/goods", "params": {"name": "AK-47"}},
        ]
        
        for config in search_configs:
            await self._test_search_endpoint(config["endpoint"], config["params"])
    
    async def _test_search_endpoint(self, endpoint: str, params: dict):
        """测试搜索端点"""
        try:
            url = urljoin(self.base_url, endpoint)
            
            async with self.session.get(url, params=params) as response:
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                print(f"   GET {endpoint}?{param_str}: {response.status}")
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'json' in content_type:
                        try:
                            data = await response.json()
                            print(f"      ✅ JSON响应")
                            self._analyze_json_response(data)
                        except Exception as e:
                            print(f"      ❌ JSON解析失败: {e}")
                    else:
                        text = await response.text()
                        print(f"      📄 HTML响应")
                        self._analyze_html_response(text)
                        
        except Exception as e:
            print(f"   {endpoint}: ❌ {e}")
    
    def _analyze_json_response(self, data):
        """分析JSON响应"""
        if isinstance(data, dict):
            print(f"         字段: {list(data.keys())}")
            
            # 查找商品数据
            for key in ['data', 'items', 'goods', 'products', 'list']:
                if key in data:
                    items = data[key]
                    if isinstance(items, list) and len(items) > 0:
                        print(f"         找到商品列表: {len(items)} 个商品")
                        first_item = items[0]
                        if isinstance(first_item, dict):
                            print(f"         商品字段: {list(first_item.keys())}")
                            
                            # 查找价格字段
                            price_fields = ['price', 'sell_price', 'min_price', 'lowest_price']
                            for field in price_fields:
                                if field in first_item:
                                    print(f"         💰 价格字段 {field}: {first_item[field]}")
                        break
        elif isinstance(data, list):
            print(f"         列表响应: {len(data)} 个元素")
    
    def _analyze_html_response(self, html):
        """分析HTML响应"""
        print(f"         HTML长度: {len(html)}")
        
        # 检查价格信息
        price_matches = re.findall(r'¥\s*(\d+\.?\d*)', html)
        if price_matches:
            print(f"         💰 发现价格: {price_matches[:5]}")
        
        # 检查商品信息
        if 'AK-47' in html or 'ak-47' in html.lower():
            print(f"         🎯 包含AK-47相关信息")

async def main():
    """主函数"""
    print("🎯 悠悠有品API调试工具")
    print("="*50)
    
    async with YoupinAPIDebugger() as debugger:
        # 1. 测试基本连接
        if await debugger.test_basic_connectivity():
            # 2. 测试常见端点
            await debugger.test_common_endpoints()
            
            # 3. 测试搜索参数
            await debugger.test_search_with_params()
        
        print("\n" + "="*50)
        print("💡 调试建议:")
        print("1. 查看上面的输出，找到返回JSON的端点")
        print("2. 使用浏览器开发者工具查看网络请求")
        print("3. 找到搜索时实际调用的API接口")
        print("4. 提供正确的API端点和参数格式")

if __name__ == "__main__":
    asyncio.run(main()) 