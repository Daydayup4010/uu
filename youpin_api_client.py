#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品真实API客户端

专门用于获取悠悠有品的真实最低价格
"""

import asyncio
import aiohttp
import json
import re
import logging
from typing import Optional, Dict, List
from urllib.parse import quote
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class YoupinRealAPIClient:
    """悠悠有品真实API客户端"""
    
    def __init__(self):
        self.base_url = "https://www.youpin898.com"
        self.api_url = "https://api.youpin898.com"  # 使用专门的API域名
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'{self.base_url}/',
            'Origin': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=3)
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
        """搜索商品的真实最低价格"""
        print(f"\n🔍 开始搜索悠悠有品价格: {item_name}")
        print("="*60)
        
        # 尝试多种可能的API接口
        api_endpoints = [
            self._search_via_api_domain,
            self._search_via_search_api,
            self._search_via_goods_api,
            self._search_via_market_api,
        ]
        
        for i, api_method in enumerate(api_endpoints):
            print(f"\n📡 尝试方法 {i+1}: {api_method.__name__}")
            try:
                price = await api_method(item_name)
                if price and price > 0:
                    print(f"✅ 成功获取价格: ¥{price}")
                    return price
                else:
                    print(f"❌ 该方法未获取到有效价格")
            except Exception as e:
                print(f"❌ 方法失败: {e}")
                continue
        
        print(f"\n⚠️ 所有方法都失败了，无法获取价格")
        return None
    
    async def _search_via_api_domain(self, item_name: str) -> Optional[float]:
        """通过api.youpin898.com域名搜索"""
        print(f"   🌐 通过API域名搜索...")
        
        # 尝试不同的接口路径
        api_paths = [
            "/search",
            "/goods/search", 
            "/market/search",
            "/product/search",
            "/v1/search",
            "/v2/search"
        ]
        
        for path in api_paths:
            try:
                url = f"{self.api_url}{path}"
                params = {
                    'keyword': item_name,
                    'game': 'csgo',
                    'appid': 730
                }
                
                print(f"      📤 请求: {url}")
                print(f"      📋 参数: {params}")
                
                async with self.session.get(url, params=params) as response:
                    print(f"      📥 响应状态: {response.status}")
                    print(f"      📋 响应头: {dict(response.headers)}")
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        print(f"      📄 内容类型: {content_type}")
                        
                        if 'json' in content_type:
                            try:
                                data = await response.json()
                                print(f"      📊 JSON数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                                print(f"      📊 JSON内容预览: {str(data)[:200]}...")
                                
                                price = self._extract_price_from_api_response(data)
                                if price:
                                    print(f"      💰 提取到价格: ¥{price}")
                                    return price
                            except Exception as e:
                                print(f"      ❌ JSON解析失败: {e}")
                        else:
                            # 如果返回HTML，尝试从中提取价格
                            html = await response.text()
                            print(f"      📄 HTML长度: {len(html)} 字符")
                            print(f"      📄 HTML内容预览: {html[:300]}...")
                            
                            price = self._extract_price_from_html(html)
                            if price:
                                print(f"      💰 从HTML提取到价格: ¥{price}")
                                return price
                    else:
                        # 即使状态码不是200，也尝试读取响应内容
                        try:
                            text = await response.text()
                            print(f"      📄 错误响应内容: {text[:200]}...")
                        except:
                            print(f"      ❌ 无法读取错误响应内容")
                
            except Exception as e:
                print(f"      ❌ 请求 {path} 失败: {e}")
                continue
        
        return None
    
    async def _search_via_search_api(self, item_name: str) -> Optional[float]:
        """通过搜索API接口"""
        print(f"   🔍 通过搜索API...")
        
        # 常见的搜索API格式
        search_urls = [
            f"{self.base_url}/api/search",
            f"{self.base_url}/search/api",
            f"{self.api_url}/search",
        ]
        
        for url in search_urls:
            try:
                params = {
                    'keyword': item_name,
                    'q': item_name,
                    'game': 'csgo',
                    'type': 'weapon'
                }
                
                print(f"      📤 请求: {url}")
                print(f"      📋 参数: {params}")
                
                async with self.session.get(url, params=params) as response:
                    print(f"      📥 响应状态: {response.status}")
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        print(f"      📄 内容类型: {content_type}")
                        
                        try:
                            if 'json' in content_type:
                                data = await response.json()
                                print(f"      📊 JSON内容: {str(data)[:300]}...")
                            else:
                                data = await response.text()
                                print(f"      📄 HTML内容: {data[:300]}...")
                            
                            if isinstance(data, dict):
                                price = self._extract_price_from_api_response(data)
                            else:
                                price = self._extract_price_from_html(str(data))
                            
                            if price:
                                return price
                        except Exception as e:
                            print(f"      ❌ 解析响应失败: {e}")
                    else:
                        try:
                            error_text = await response.text()
                            print(f"      📄 错误内容: {error_text[:200]}...")
                        except:
                            pass
                    
            except Exception as e:
                print(f"      ❌ 请求失败: {e}")
                continue
        
        return None
    
    async def _search_via_goods_api(self, item_name: str) -> Optional[float]:
        """通过商品API接口"""
        print(f"   📦 通过商品API...")
        
        goods_urls = [
            f"{self.base_url}/api/goods",
            f"{self.api_url}/goods", 
            f"{self.api_url}/goods/search"
        ]
        
        for url in goods_urls:
            try:
                params = {
                    'name': item_name,
                    'search': item_name,
                    'keyword': item_name
                }
                
                print(f"      📤 请求: {url}")
                print(f"      📋 参数: {params}")
                
                async with self.session.get(url, params=params) as response:
                    print(f"      📥 响应状态: {response.status}")
                    
                    if response.status == 200:
                        try:
                            content_type = response.headers.get('content-type', '')
                            if 'json' in content_type:
                                data = await response.json()
                                print(f"      📊 JSON内容: {str(data)[:300]}...")
                                price = self._extract_price_from_api_response(data)
                                if price:
                                    return price
                            else:
                                text = await response.text()
                                print(f"      📄 文本内容: {text[:300]}...")
                        except Exception as e:
                            print(f"      ❌ 解析失败: {e}")
                    
            except Exception as e:
                print(f"      ❌ 请求失败: {e}")
                continue
        
        return None
    
    async def _search_via_market_api(self, item_name: str) -> Optional[float]:
        """通过市场API接口"""
        print(f"   🏪 通过市场API...")
        
        market_urls = [
            f"{self.base_url}/api/market/search",
            f"{self.api_url}/market/search",
            f"{self.api_url}/market"
        ]
        
        for url in market_urls:
            try:
                params = {
                    'q': item_name,
                    'keyword': item_name,
                    'game_id': 730,
                    'sort': 'price_asc'
                }
                
                print(f"      📤 请求: {url}")
                print(f"      📋 参数: {params}")
                
                async with self.session.get(url, params=params) as response:
                    print(f"      📥 响应状态: {response.status}")
                    
                    if response.status == 200:
                        try:
                            content_type = response.headers.get('content-type', '')
                            if 'json' in content_type:
                                data = await response.json()
                                print(f"      📊 JSON内容: {str(data)[:300]}...")
                                price = self._extract_price_from_api_response(data)
                                if price:
                                    return price
                            else:
                                text = await response.text()
                                print(f"      📄 文本内容: {text[:300]}...")
                        except Exception as e:
                            print(f"      ❌ 解析失败: {e}")
                    
            except Exception as e:
                print(f"      ❌ 请求失败: {e}")
                continue
        
        return None
    
    def _extract_price_from_api_response(self, data: dict) -> Optional[float]:
        """从API响应中提取价格"""
        try:
            print(f"      🔍 分析API响应数据...")
            
            # 尝试各种可能的数据结构
            possible_paths = [
                # 标准API响应格式
                ['data', 'items'],
                ['data', 'list'],
                ['data', 'goods'],
                ['data', 'products'],
                ['result', 'items'],
                ['items'],
                ['list'],
                ['goods'],
                ['products'],
                # 直接在data中
                ['data'],
            ]
            
            items = None
            for path in possible_paths:
                current = data
                try:
                    for key in path:
                        current = current[key]
                    if isinstance(current, list) and len(current) > 0:
                        items = current
                        print(f"      ✅ 在路径 {' -> '.join(path)} 找到 {len(items)} 个商品")
                        break
                    elif isinstance(current, dict) and current:
                        # 如果是单个商品对象
                        items = [current]
                        print(f"      ✅ 在路径 {' -> '.join(path)} 找到单个商品")
                        break
                except (KeyError, TypeError):
                    continue
            
            if not items:
                print(f"      ❌ 未找到商品数据，响应结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                return None
            
            # 从商品列表中提取最低价格
            min_price = None
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                
                print(f"      🔍 分析第 {i+1} 个商品: {list(item.keys())}")
                
                # 尝试各种可能的价格字段
                price_fields = [
                    'price', 'sell_price', 'lowest_price', 'min_price',
                    'current_price', 'market_price', 'sale_price',
                    'start_price', 'low_price', '价格'
                ]
                
                for field in price_fields:
                    if field in item:
                        try:
                            price = float(item[field])
                            if price > 0:
                                if min_price is None or price < min_price:
                                    min_price = price
                                print(f"      💰 找到价格字段 {field}: ¥{price}")
                        except (ValueError, TypeError):
                            print(f"      ⚠️ 价格字段 {field} 值无效: {item[field]}")
                            continue
            
            if min_price:
                print(f"      ✅ 最终提取价格: ¥{min_price}")
            
            return min_price
            
        except Exception as e:
            print(f"      ❌ 提取价格失败: {e}")
            return None
    
    def _extract_price_from_html(self, html: str) -> Optional[float]:
        """从HTML中提取价格"""
        try:
            print(f"      🔍 从HTML提取价格...")
            
            # 价格提取模式
            price_patterns = [
                r'¥\s*(\d+\.?\d*)',
                r'"price":\s*(\d+\.?\d*)',
                r'"sell_price":\s*(\d+\.?\d*)',
                r'"lowest_price":\s*(\d+\.?\d*)',
                r'data-price="(\d+\.?\d*)"',
                r'class="price"[^>]*>.*?(\d+\.?\d*)',
            ]
            
            found_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    try:
                        price = float(match)
                        if 1 <= price <= 50000:  # 合理的价格范围
                            found_prices.append(price)
                    except ValueError:
                        continue
            
            if found_prices:
                min_price = min(found_prices)
                print(f"      💰 从HTML提取价格: {found_prices[:5]}, 返回最低价: ¥{min_price}")
                return min_price
            else:
                print(f"      ❌ HTML中未找到价格信息")
            
            return None
            
        except Exception as e:
            print(f"      ❌ HTML价格提取失败: {e}")
            return None
    
    async def batch_get_prices(self, item_names: List[str]) -> Dict[str, Optional[float]]:
        """批量获取商品价格"""
        prices = {}
        
        for i, item_name in enumerate(item_names):
            print(f"\n{'='*80}")
            print(f"📊 批量获取价格 {i+1}/{len(item_names)}: {item_name}")
            
            price = await self.search_item_price(item_name)
            prices[item_name] = price
            
            # 控制请求频率
            if i < len(item_names) - 1:
                print(f"⏱️ 等待1秒...")
                await asyncio.sleep(1)  # 1秒延迟
        
        return prices

# 测试函数
async def test_youpin_api():
    """测试悠悠有品API客户端"""
    print("🎯 测试悠悠有品真实API客户端")
    print("="*80)
    
    test_items = [
        "AK-47",
        "M4A4",
        "AWP",
    ]
    
    async with YoupinRealAPIClient() as client:
        for item in test_items:
            price = await client.search_item_price(item)
            
            print(f"\n🎯 最终结果:")
            if price:
                print(f"✅ {item} 的悠悠有品价格: ¥{price}")
            else:
                print(f"❌ {item} 无法获取价格")
            
            print(f"\n{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_youpin_api()) 