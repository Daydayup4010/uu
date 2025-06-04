#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品工作版本API客户端

基于真实API调试结果的正确实现
"""

import asyncio
import aiohttp
import json
import re
import time
from typing import Optional, Dict, List

from config import Config  # 导入配置类

class YoupinWorkingAPI:
    """悠悠有品工作版本API客户端"""
    
    def __init__(self):
        self.api_base = "https://api.youpin898.com"
        self.web_base = "https://www.youpin898.com"
        self.session = None
        
        # 从TokenManager加载配置
        self.load_config_from_token_manager()
        
        # 频率控制和重试设置
        self.last_request_time = 0
        self.min_interval = 1.0  # 减少基础间隔到1秒
        self.max_retries = 2  # 最大重试次数
        self.retry_delay = 2.0  # 重试延迟
    
    def load_config_from_token_manager(self):
        """从TokenManager加载配置"""
        try:
            from token_manager import token_manager
            youpin_config = token_manager.get_youpin_config()
            
            # 加载设备信息
            self.device_id = youpin_config.get("device_id", "5b38ebeb-5a5b-4b1a-afe9-b51edbbb8e01")
            self.device_uk = youpin_config.get("device_uk", "5FL1Llbg5qN4z5LjXWo7VlMewPJ7hWEHtwHQpvWQToDNErV6KwbpSj6JBBCjogH1L")
            self.uk = youpin_config.get("uk", "5FEvkZD2PSMLMTtE0BqOfidTtuoaX9HWBIze4zzFxfdXrsajaPWS4yY5ay96BuX1M")
            self.b3 = youpin_config.get("b3", "833f3214b9b04819a399c94ed1fab7af-2a9cab244348658f-1")
            self.authorization = youpin_config.get("authorization", "")
            
            # 加载headers
            base_headers = youpin_config.get("headers", {})
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
            
            # 添加authorization头（如果存在）
            if self.authorization:
                self.headers['authorization'] = self.authorization
            
            # 更新headers（如果TokenManager中有自定义配置）
            if base_headers:
                self.headers.update(base_headers)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"加载TokenManager配置失败: {e}")
            # 使用默认配置
            self.device_id = "5b38ebeb-5a5b-4b1a-afe9-b51edbbb8e01"
            self.device_uk = "5FL1Llbg5qN4z5LjXWo7VlMewPJ7hWEHtwHQpvWQToDNErV6KwbpSj6JBBCjogH1L"
            self.uk = "5FEvkZD2PSMLMTtE0BqOfidTtuoaX9HWBIze4zzFxfdXrsajaPWS4yY5ay96BuX1M"
            self.b3 = "833f3214b9b04819a399c94ed1fab7af-2a9cab244348658f-1"
            self.authorization = ""
            
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
    
    def reload_config(self):
        """重新加载配置"""
        self.load_config_from_token_manager()
        import logging
        logger = logging.getLogger(__name__)
        logger.info("悠悠有品API配置已重新加载")
    
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
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _make_request_with_retry(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """带重试机制的请求方法"""
        for attempt in range(self.max_retries + 1):  # 0,1,2 = 总共3次尝试（1次原始+2次重试）
            try:
                await self._rate_limit()
                
                async with getattr(self.session, method.lower())(url, **kwargs) as response:
                    if response.status == 200:
                        result = await response.json()
                        # 每次成功请求后等待0.5秒，减少频率限制
                        await asyncio.sleep(0.5)
                        return result
                    elif response.status == 429:
                        print(f"   ⚠️ 频率限制 (429), 尝试 {attempt + 1}/{self.max_retries + 1}")
                        if attempt < self.max_retries:
                            # 动态增加延迟时间
                            delay = self.retry_delay * (2 ** attempt)  # 指数退避
                            print(f"   ⏱️ 等待 {delay} 秒后重试...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            print(f"   ❌ 达到最大重试次数，放弃请求")
                            return None
                    elif response.status in [403, 401]:
                        print(f"   ⚠️ 认证失败 ({response.status}), 尝试 {attempt + 1}/{self.max_retries + 1}")
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        else:
                            print(f"   ❌ 认证问题无法解决，跳过")
                            return None
                    else:
                        print(f"   ❌ 请求失败: {response.status}, 尝试 {attempt + 1}/{self.max_retries + 1}")
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        else:
                            await asyncio.sleep(1.0)  # 最终失败也要等待
                            return None
                            
            except Exception as e:
                print(f"   ❌ 请求异常: {e}, 尝试 {attempt + 1}/{self.max_retries + 1}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    await asyncio.sleep(1.0)  # 异常时也要等待
                    return None
        
        return None
    
    async def get_market_goods(self, page_index: int = 1, page_size: int = 100) -> Optional[List[Dict]]:
        """获取市场商品列表 - 默认page_size改为100"""
        url = f"{self.api_base}/api/homepage/pc/goods/market/querySaleTemplate"
        
        payload = {
            "listSortType": 0,
            "sortType": 0,
            "pageSize": page_size,
            "pageIndex": page_index
        }
        
        data = await self._make_request_with_retry('post', url, json=payload)
        
        if data and isinstance(data, dict) and 'Data' in data:
            goods_list = data['Data']
            if isinstance(goods_list, list):
                return goods_list
        
        return None
    
    async def search_item_price(self, item_name: str) -> Optional[float]:
        """搜索商品价格 - 优化版本"""
        print(f"\n🔍 搜索悠悠有品价格: {item_name}")
        
        # 搜索前3页，每页100个商品，总共300个商品
        for page in range(1, 4):
            print(f"   📄 搜索第 {page} 页 (每页100个商品)...")
            
            goods_list = await self.get_market_goods(page_index=page, page_size=100)
            if not goods_list:
                continue
            
            # 在商品列表中查找匹配的商品
            for item in goods_list:
                if not isinstance(item, dict):
                    continue
                
                # 使用正确的字段名
                goods_name = item.get('commodityName', '')
                if self._is_name_match(item_name, goods_name):
                    price = item.get('price')
                    if price and price != '':
                        try:
                            price_float = float(price)
                            print(f"   ✅ 找到匹配商品: {goods_name} - ¥{price_float}")
                            return price_float
                        except (ValueError, TypeError):
                            continue
        
        print(f"   ❌ 未找到商品: {item_name}")
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
    
    async def get_sample_goods(self, count: int = 10) -> List[Dict]:
        """获取样本商品数据"""
        print(f"\n📦 获取 {count} 个样本商品")
        
        goods_list = await self.get_market_goods(page_index=1, page_size=count)
        return goods_list if goods_list else []
    
    async def get_all_items(self) -> Optional[List[Dict]]:
        """分页获取所有悠悠有品商品 - 完全并行版本"""
        print(f"\n📦 开始并行获取所有悠悠有品商品（完全并行版本）...")
        
        try:
            all_goods = []
            max_pages = Config.YOUPIN_MAX_PAGES  # 使用配置中的页数限制
            
            print(f"   🎯 计划并行获取前 {max_pages} 页数据（每页{Config.YOUPIN_PAGE_SIZE}个商品）")
            
            # 🚀 并行获取所有页面
            print(f"   🚀 开始并行获取第1-{max_pages}页...")
            
            # 创建所有页面的任务
            page_tasks = []
            for page in range(1, max_pages + 1):
                task = asyncio.create_task(
                    self.get_market_goods(page_index=page, page_size=Config.YOUPIN_PAGE_SIZE),
                    name=f"youpin_page_{page}"
                )
                page_tasks.append((page, task))
            
            # 并行等待所有页面完成
            print(f"   ⏳ 等待 {len(page_tasks)} 个页面并行完成...")
            start_time = time.time()
            
            # 分批处理以避免过多并发请求
            batch_size = Config.YOUPIN_BATCH_SIZE  # 使用配置中的批次大小
            for i in range(0, len(page_tasks), batch_size):
                batch = page_tasks[i:i + batch_size]
                batch_nums = [num for num, _ in batch]
                batch_tasks = [task for _, task in batch]
                
                print(f"   📦 并行处理第 {batch_nums[0]}-{batch_nums[-1]} 页...")
                results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 处理这批结果
                for (page_num, _), result in zip(batch, results):
                    if isinstance(result, Exception):
                        print(f"   ❌ 第 {page_num} 页异常: {result}")
                    elif result and len(result) > 0:
                        all_goods.extend(result)
                        if page_num % 5 == 0:  # 每5页显示进度
                            print(f"   ✅ 第 {page_num} 页获取了 {len(result)} 个商品")
                    else:
                        print(f"   ⚠️ 第 {page_num} 页无数据")
                
                # 批次间延迟
                if i + batch_size < len(page_tasks):
                    await asyncio.sleep(Config.REQUEST_DELAY)  # 使用配置中的延迟
            
            parallel_time = time.time() - start_time
            print(f"   ⚡ 并行获取完成，耗时: {parallel_time:.2f} 秒")
            
            # 去重处理
            unique_goods = []
            seen_names = set()
            
            for item in all_goods:
                name = item.get('commodityName', '')
                if name and name not in seen_names:
                    unique_goods.append(item)
                    seen_names.add(name)
            
            print(f"   ✅ 总共获取 {len(all_goods)} 个商品")
            print(f"   ✅ 去重后获得 {len(unique_goods)} 个唯一商品")
            
            return unique_goods if unique_goods else []
                
        except Exception as e:
            print(f"   ❌ 获取所有商品异常: {e}")
            return []

# 测试函数
async def test_youpin_working_api():
    """测试工作版本的悠悠有品API"""
    print("🎯 测试悠悠有品工作版本API客户端")
    print("="*80)
    
    async with YoupinWorkingAPI() as client:
        # 1. 获取样本商品
        print(f"\n1️⃣ 获取样本商品测试")
        sample_goods = await client.get_sample_goods(10)
        
        if sample_goods:
            # 2. 使用实际商品名称进行测试
            print(f"\n2️⃣ 使用真实商品名称测试价格查询")
            
            # 从样本商品中选择几个进行测试
            test_items = []
            for item in sample_goods[:3]:
                name = item.get('commodityName', '')
                if name:
                    test_items.append(name)
            
            # 完全匹配测试
            for item in test_items:
                price = await client.search_item_price(item)
                if price:
                    print(f"✅ {item}: ¥{price}")
                else:
                    print(f"❌ {item}: 查询失败")
        
        # 3. 关键词搜索测试
        print(f"\n3️⃣ 关键词搜索测试")
        keyword_tests = ["AK-47", "M4A4", "AWP", "波塞冬"]
        
        for keyword in keyword_tests:
            price = await client.search_item_price(keyword)
            if price:
                print(f"✅ 关键词 '{keyword}': ¥{price}")
            else:
                print(f"❌ 关键词 '{keyword}': 未找到")

if __name__ == "__main__":
    asyncio.run(test_youpin_working_api()) 