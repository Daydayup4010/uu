#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索API客户端 - 支持悠悠有品和Buff的关键词搜索
用于增量更新功能
"""

import asyncio
import aiohttp
import json
import logging
import urllib.parse
from typing import List, Dict, Optional
from dataclasses import dataclass

from token_manager import TokenManager
from config import Config

# 🔥 导入优化客户端以共享全局延迟
try:
    from optimized_api_client import OptimizedYoupinClient
    YOUPIN_GLOBAL_DELAY_AVAILABLE = True
except ImportError:
    YOUPIN_GLOBAL_DELAY_AVAILABLE = False

logger = logging.getLogger(__name__)

# 🔥 全局延迟控制 - 所有API客户端共享
class GlobalRateLimiter:
    """全局API速率限制器"""
    _last_request_time = 0
    _lock = None
    
    @classmethod
    async def wait_if_needed(cls, min_delay: float, api_name: str = "API"):
        """如果需要，等待足够的时间间隔"""
        # 🔥 修复：在每次使用时获取当前事件循环的锁
        if cls._lock is None:
            try:
                cls._lock = asyncio.Lock()
            except RuntimeError:
                # 如果没有运行中的事件循环，先获取事件循环
                loop = asyncio.get_event_loop()
                cls._lock = asyncio.Lock()
        
        # 🔥 修复：如果锁绑定到错误的事件循环，重新创建
        try:
            async with cls._lock:
                import time
                current_time = time.time()
                time_since_last = current_time - cls._last_request_time
                
                if time_since_last < min_delay:
                    wait_time = min_delay - time_since_last
                    logger.info(f"{api_name}全局延迟 {wait_time:.1f}秒 (跨平台延迟控制)...")
                    await asyncio.sleep(wait_time)
                
                cls._last_request_time = time.time()
        except RuntimeError as e:
            if "different loop" in str(e):
                # 重新创建锁
                cls._lock = asyncio.Lock()
                async with cls._lock:
                    import time
                    current_time = time.time()
                    time_since_last = current_time - cls._last_request_time
                    
                    if time_since_last < min_delay:
                        wait_time = min_delay - time_since_last
                        logger.info(f"{api_name}全局延迟 {wait_time:.1f}秒 (跨平台延迟控制)...")
                        await asyncio.sleep(wait_time)
                    
                    cls._last_request_time = time.time()
            else:
                raise

@dataclass
class SearchResult:
    """搜索结果数据类"""
    id: str
    name: str
    price: float
    hash_name: str
    image_url: str = ""
    market_url: str = ""
    platform: str = ""  # 'buff' or 'youpin'

class YouPinSearchClient:
    """悠悠有品搜索客户端"""
    
    # 🔥 类级别的全局延迟控制，与其他悠悠有品客户端共享
    _global_last_request_time = 0
    
    def __init__(self):
        self.base_url = "https://api.youpin898.com"
        self.session = None
        self.token_manager = TokenManager()
        self.headers = self._get_headers()
        self.last_request_time = 0  # 保留实例级别用于兼容
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        config = self.token_manager.get_youpin_config()
        
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'App-Version': '5.26.0',
            'AppVersion': '5.26.0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://www.youpin898.com',
            'Referer': 'https://www.youpin898.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
            'appType': '1',
            'authorization': config.get('authorization', ''),
            'b3': config.get('b3', ''),
            'deviceId': config.get('device_id', ''),
            'deviceUk': config.get('device_uk', ''),
            'platform': 'pc',
            'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'secret-v': 'h5_v1',
            'uk': config.get('uk', '')
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def search_by_keyword(self, keyword: str, page_index: int = 1, page_size: int = 20) -> List[SearchResult]:
        """根据关键词搜索商品"""
        try:
            # 🔥 使用统一的全局延迟控制器
            await GlobalRateLimiter.wait_if_needed(Config.YOUPIN_API_DELAY, "悠悠有品搜索")
            
            url = f"{self.base_url}/api/homepage/pc/goods/market/querySaleTemplate"
            
            data = {
                "listSortType": 0,
                "sortType": 0,
                "keyWords": keyword,
                "pageSize": page_size,
                "pageIndex": page_index
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._parse_search_results(result)
                elif response.status == 429:
                    logger.error(f"悠悠有品搜索频率限制 (429): {keyword} - 可能需要增加 YOUPIN_API_DELAY")
                    return []
                else:
                    logger.error(f"悠悠有品搜索失败: {response.status} - {keyword}")
                    return []
                    
        except Exception as e:
            logger.error(f"悠悠有品搜索出错: {e} - {keyword}")
            return []
    
    def _parse_search_results(self, data: Dict) -> List[SearchResult]:
        """解析搜索结果"""
        results = []
        
        try:
            if data.get('code') == 200 and data.get('data'):
                items = data['data'].get('dataList', [])
                
                for item in items:
                    try:
                        result = SearchResult(
                            id=str(item.get('commodityId', '')),
                            name=item.get('commodityName', ''),
                            price=float(item.get('price', 0)),
                            hash_name=item.get('commodityHashName', ''),
                            image_url=item.get('commodityUrl', ''),
                            market_url=f"https://www.youpin898.com/goodsDetail?id={item.get('commodityId', '')}",
                            platform='youpin'
                        )
                        
                        if result.price > 0:
                            results.append(result)
                            
                    except (ValueError, TypeError) as e:
                        logger.warning(f"解析悠悠有品商品失败: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"解析悠悠有品搜索结果失败: {e}")
        
        return results

class BuffSearchClient:
    """Buff搜索客户端"""
    
    # 🔥 类级别的全局延迟控制，与其他Buff客户端共享
    _global_last_request_time = 0
    
    def __init__(self):
        self.base_url = "https://buff.163.com"
        self.session = None
        self.token_manager = TokenManager()
        self.headers = self._get_headers()
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        config = self.token_manager.get_buff_config()
        
        return {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
            'referer': 'https://buff.163.com/market/csgo',
            'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
            'x-requested-with': 'XMLHttpRequest'
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 获取cookies
        config = self.token_manager.get_buff_config()
        cookies = config.get('cookies', {})
        
        # 如果cookies是字符串，解析为字典
        if isinstance(cookies, str):
            cookie_dict = {}
            for item in cookies.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookie_dict[key] = value
            cookies = cookie_dict
        
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers,
            cookies=cookies
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def search_by_keyword(self, keyword: str, page_num: int = 1) -> List[SearchResult]:
        """根据关键词搜索商品"""
        try:
            # 🔥 使用统一的全局延迟控制器
            await GlobalRateLimiter.wait_if_needed(Config.BUFF_API_DELAY, "Buff搜索")
            
            # URL编码关键词
            encoded_keyword = urllib.parse.quote(keyword)
            
            url = f"{self.base_url}/api/market/goods"
            params = {
                'game': 'csgo',
                'page_num': page_num,
                'search': encoded_keyword,
                'tab': 'selling',
                '_': str(int(asyncio.get_event_loop().time() * 1000))
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._parse_search_results(result)
                elif response.status == 429:
                    logger.error(f"Buff搜索频率限制 (429): {keyword} - 可能需要增加 BUFF_API_DELAY")
                    return []
                else:
                    logger.error(f"Buff搜索失败: {response.status} - {keyword}")
                    return []
                    
        except Exception as e:
            logger.error(f"Buff搜索出错: {e} - {keyword}")
            return []
    
    def _parse_search_results(self, data: Dict) -> List[SearchResult]:
        """解析搜索结果"""
        results = []
        
        try:
            if data.get('code') == 'OK' and data.get('data'):
                items = data['data'].get('items', [])
                
                for item in items:
                    try:
                        # 获取最低价格
                        sell_min_price = item.get('sell_min_price', '0')
                        try:
                            price = float(sell_min_price) if sell_min_price else 0.0
                        except (ValueError, TypeError):
                            price = 0.0
                        
                        result = SearchResult(
                            id=str(item.get('id', '')),
                            name=item.get('name', ''),
                            price=price,
                            hash_name=item.get('market_hash_name', ''),
                            image_url=item.get('goods_info', {}).get('icon_url', ''),
                            market_url=f"https://buff.163.com/goods/{item.get('id', '')}",
                            platform='buff'
                        )
                        
                        if result.price > 0:
                            results.append(result)
                            
                    except Exception as e:
                        logger.warning(f"解析Buff商品失败: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"解析Buff搜索结果失败: {e}")
        
        return results

class SearchManager:
    """搜索管理器 - 整合悠悠有品和Buff搜索"""
    
    def __init__(self):
        self.youpin_client = None
        self.buff_client = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.youpin_client = await YouPinSearchClient().__aenter__()
        self.buff_client = await BuffSearchClient().__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.youpin_client:
            await self.youpin_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.buff_client:
            await self.buff_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def search_both_platforms(self, keyword: str) -> Dict[str, List[SearchResult]]:
        """在两个平台上搜索关键词 - 串行执行确保全局延迟控制生效"""
        try:
            # 🔥 修改为串行搜索，确保全局延迟控制生效
            youpin_results = []
            buff_results = []
            
            # 先搜索悠悠有品
            try:
                youpin_results = await self.youpin_client.search_by_keyword(keyword)
            except Exception as e:
                logger.error(f"悠悠有品搜索异常: {e}")
                youpin_results = []
            
            # 再搜索Buff（会自动遵守全局延迟控制）
            try:
                buff_results = await self.buff_client.search_by_keyword(keyword)
            except Exception as e:
                logger.error(f"Buff搜索异常: {e}")
                buff_results = []
            
            return {
                'youpin': youpin_results or [],
                'buff': buff_results or []
            }
            
        except Exception as e:
            logger.error(f"搜索管理器出错: {e}")
            return {'youpin': [], 'buff': []}

# 测试功能
async def test_search_clients():
    """测试搜索客户端"""
    print("🔍 测试搜索API客户端")
    print("="*50)
    
    async with SearchManager() as manager:
        # 测试搜索关键词
        test_keywords = ["印花集", "AK-47", "刺刀"]
        
        for keyword in test_keywords:
            print(f"\n🔎 搜索关键词: {keyword}")
            results = await manager.search_both_platforms(keyword)
            
            print(f"悠悠有品结果: {len(results['youpin'])}个")
            for item in results['youpin'][:3]:  # 显示前3个
                print(f"  - {item.name}: ¥{item.price}")
            
            print(f"Buff结果: {len(results['buff'])}个")
            for item in results['buff'][:3]:  # 显示前3个
                print(f"  - {item.name}: ¥{item.price}")

if __name__ == "__main__":
    asyncio.run(test_search_clients()) 
