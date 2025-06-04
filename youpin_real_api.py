#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品真实API客户端 - 基于真实curl分析

根据真实的API调用信息实现价格查询功能
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

class YoupinRealAPI:
    """悠悠有品真实API客户端"""
    
    def __init__(self):
        self.api_base = "https://api.youpin898.com"
        self.web_base = "https://www.youpin898.com"
        self.session = None
        
        # 生成设备ID（可以固定使用）
        self.device_id = "5b38ebeb-5a5b-4b1a-afe9-b51edbbb8e01"
        
        # 基础请求头
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'app-version': '5.26.0',
            'apptype': '1',
            'appversion': '5.26.0',
            'content-type': 'application/json',
            'deviceid': self.device_id,
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
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0'
        }
    
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
            
            # 请求体数据
            payload = {
                "listSortType": 0,  # 排序类型
                "sortType": 0,      # 排序方向
                "pageSize": page_size,
                "pageIndex": page_index
            }
            
            print(f"   📤 请求URL: {url}")
            print(f"   📋 请求数据: {payload}")
            
            async with self.session.post(url, json=payload) as response:
                print(f"   📥 响应状态: {response.status}")
                print(f"   📋 响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"   ✅ 成功获取JSON数据")
                        print(f"   📊 响应结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        
                        if isinstance(data, dict):
                            # 分析响应数据结构
                            if 'data' in data:
                                goods_data = data['data']
                                if isinstance(goods_data, list):
                                    print(f"   🎯 找到 {len(goods_data)} 个商品")
                                elif isinstance(goods_data, dict) and 'list' in goods_data:
                                    items = goods_data['list']
                                    print(f"   🎯 找到 {len(items)} 个商品")
                                    
                                    # 显示前几个商品信息
                                    for i, item in enumerate(items[:3]):
                                        if isinstance(item, dict):
                                            name = item.get('name', '未知商品')
                                            price = item.get('price', item.get('sell_price', '未知价格'))
                                            print(f"      #{i+1}: {name} - ¥{price}")
                        
                        return data
                        
                    except Exception as e:
                        print(f"   ❌ JSON解析失败: {e}")
                        text = await response.text()
                        print(f"   📄 原始响应: {text[:500]}...")
                        
                else:
                    error_text = await response.text()
                    print(f"   ❌ 请求失败: {response.status}")
                    print(f"   📄 错误内容: {error_text[:300]}...")
                    
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
        
        return None
    
    async def search_goods(self, keyword: str, page_index: int = 1) -> Optional[Dict]:
        """搜索商品"""
        print(f"\n🔍 搜索商品: {keyword}")
        
        # 尝试不同的搜索API端点
        search_endpoints = [
            "/api/search/goods",
            "/api/homepage/pc/search",
            "/api/goods/search",
            "/api/market/search",
        ]
        
        for endpoint in search_endpoints:
            try:
                url = f"{self.api_base}{endpoint}"
                
                # 不同的请求体格式
                payloads = [
                    {"keyword": keyword, "pageIndex": page_index, "pageSize": 20},
                    {"searchKey": keyword, "page": page_index, "size": 20},
                    {"q": keyword, "pageIndex": page_index, "pageSize": 20},
                ]
                
                for payload in payloads:
                    print(f"   📤 尝试: {endpoint}")
                    print(f"   📋 数据: {payload}")
                    
                    async with self.session.post(url, json=payload) as response:
                        print(f"   📥 状态: {response.status}")
                        
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '')
                            if 'json' in content_type:
                                try:
                                    data = await response.json()
                                    print(f"   ✅ 搜索成功!")
                                    return data
                                except:
                                    pass
                        
                        elif response.status != 404:
                            # 非404错误，显示详细信息
                            error_text = await response.text()
                            print(f"   ⚠️ 错误: {response.status} - {error_text[:200]}...")
                            
            except Exception as e:
                print(f"   ❌ 搜索失败: {e}")
        
        return None
    
    async def test_all_endpoints(self):
        """测试所有可能的API端点"""
        print(f"\n🧪 测试所有API端点...")
        print("="*80)
        
        # 1. 测试获取商品列表
        print(f"\n1️⃣ 测试获取商品列表")
        market_data = await self.get_market_goods(page_index=1, page_size=10)
        
        if market_data:
            print(f"   ✅ 商品列表API正常工作!")
        else:
            print(f"   ❌ 商品列表API无法使用")
        
        # 2. 测试搜索功能
        print(f"\n2️⃣ 测试搜索功能")
        search_data = await self.search_goods("AK-47", page_index=1)
        
        if search_data:
            print(f"   ✅ 搜索API正常工作!")
        else:
            print(f"   ❌ 搜索API无法使用")
        
        # 3. 尝试其他端点
        print(f"\n3️⃣ 测试其他可能的端点")
        other_endpoints = [
            "/api/homepage/pc/goods/list",
            "/api/goods/list", 
            "/api/market/list",
            "/api/items/list",
            "/api/homepage/goods",
        ]
        
        for endpoint in other_endpoints:
            try:
                url = f"{self.api_base}{endpoint}"
                payload = {"pageIndex": 1, "pageSize": 5}
                
                print(f"   📤 测试: {endpoint}")
                async with self.session.post(url, json=payload) as response:
                    print(f"      📥 状态: {response.status}")
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'json' in content_type:
                            print(f"      ✅ 端点可用!")
                        else:
                            print(f"      📄 返回HTML")
                    elif response.status == 401:
                        print(f"      🔐 需要认证")
                    elif response.status == 403:
                        print(f"      🚫 访问被拒绝")
                    else:
                        print(f"      ❌ 不可用")
                        
            except Exception as e:
                print(f"      ❌ 异常: {e}")

async def main():
    """主函数"""
    print("🎯 悠悠有品真实API测试")
    print("="*80)
    print("📝 基于真实curl命令分析的API接口")
    print("🔍 正在测试不需要认证的端点...")
    
    async with YoupinRealAPI() as api:
        await api.test_all_endpoints()
        
        print(f"\n" + "="*80)
        print("💡 总结:")
        print("1. 如果出现401/403错误，说明需要登录认证")
        print("2. 如果某些端点返回数据，我们可以进一步解析")
        print("3. 可能需要模拟登录获取authorization token")

if __name__ == "__main__":
    asyncio.run(main()) 