#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于API的数据收集器

使用Buff和悠悠有品的官方API接口获取饰品数据，
比HTML解析更稳定和高效，能够遍历所有饰品
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import List, Dict, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime

from config import Config
from models import SkinItem
from real_price_comparator import RealPriceComparator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """API响应数据类"""
    success: bool
    data: dict
    message: str = ""
    status_code: int = 200

class BuffAPIClient:
    """Buff API客户端"""
    
    def __init__(self):
        self.base_url = "https://buff.163.com"
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'{self.base_url}/market/csgo',
            'X-Requested-With': 'XMLHttpRequest',
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
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
    
    async def get_goods_list(self, page_num: int = 1, page_size: int = 100) -> APIResponse:
        """获取商品列表"""
        try:
            url = f"{self.base_url}/api/market/goods"
            params = {
                'game': 'csgo',
                'page_num': page_num,
                'page_size': page_size
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return APIResponse(
                        success=True,
                        data=data,
                        status_code=response.status
                    )
                else:
                    return APIResponse(
                        success=False,
                        data={},
                        message=f"HTTP {response.status}",
                        status_code=response.status
                    )
                    
        except Exception as e:
            logger.error(f"获取商品列表失败 (页{page_num}): {e}")
            return APIResponse(
                success=False,
                data={},
                message=str(e)
            )
    
    async def search_goods(self, keyword: str, page_num: int = 1, page_size: int = 20) -> APIResponse:
        """搜索商品"""
        try:
            url = f"{self.base_url}/api/market/search"
            params = {
                'game': 'csgo',
                'keyword': keyword,
                'page_num': page_num,
                'page_size': page_size
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return APIResponse(
                        success=True,
                        data=data,
                        status_code=response.status
                    )
                else:
                    return APIResponse(
                        success=False,
                        data={},
                        message=f"HTTP {response.status}",
                        status_code=response.status
                    )
                    
        except Exception as e:
            logger.error(f"搜索商品失败 ({keyword}): {e}")
            return APIResponse(
                success=False,
                data={},
                message=str(e)
            )
    
    def parse_goods_item(self, item_data: dict) -> Optional[SkinItem]:
        """解析商品数据"""
        try:
            # 提取基本信息
            goods_id = str(item_data.get('id', ''))
            name = item_data.get('name', '')
            short_name = item_data.get('short_name', name)
            
            # 提取价格信息
            buff_price = float(item_data.get('sell_min_price', 0))
            if buff_price <= 0:
                buff_price = float(item_data.get('sell_reference_price', 0))
            
            # 提取图片信息
            goods_info = item_data.get('goods_info', {})
            image_url = goods_info.get('icon_url', '')
            
            # 构建购买链接
            buff_url = f"{self.base_url}/goods/{goods_id}"
            
            # 提取类别信息
            category = "未知"
            tags = goods_info.get('info', {}).get('tags', {})
            if 'weapon' in tags:
                category = tags['weapon'].get('localized_name', '未知')
            elif 'type' in tags:
                category = tags['type'].get('localized_name', '未知')
            
            return SkinItem(
                id=f"buff_{goods_id}",
                name=name,
                buff_price=buff_price,
                buff_url=buff_url,
                image_url=image_url,
                category=category,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"解析商品数据失败: {e}")
            return None

class YoupinAPIClient:
    """悠悠有品真实API客户端 - 已集成"""
    
    def __init__(self):
        # 导入真实的悠悠有品API客户端
        from youpin_working_api import YoupinWorkingAPI
        self.real_client = YoupinWorkingAPI()
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.real_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.real_client:
            await self.real_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def search_item(self, name: str, buff_price: float = 0) -> Optional[float]:
        """搜索商品并获取真实价格"""
        try:
            print(f"   🔍 从悠悠有品获取真实价格: {name}")
            
            # 使用真实API获取价格
            youpin_price = await self.real_client.search_item_price(name)
            
            if youpin_price:
                print(f"   ✅ 悠悠有品真实价格: ¥{youpin_price}")
                return youpin_price
            else:
                print(f"   ❌ 在悠悠有品未找到商品: {name}")
                return None
                
        except Exception as e:
            print(f"   ⚠️ 获取悠悠有品价格失败: {e}")
            return None
    
    def get_price_explanation(self, name: str, price: float, source: str = "悠悠有品真实API") -> str:
        """获取价格说明"""
        return f"通过{source}获取的真实最低价: ¥{price}"

class APIDataCollector:
    """基于API的数据收集器"""
    
    def __init__(self):
        self.buff_client = BuffAPIClient()
        self.youpin_client = YoupinAPIClient()
    
    async def collect_all_items(self, max_pages: int = None) -> List[SkinItem]:
        """收集所有饰品数据"""
        logger.info("开始使用API收集所有饰品数据...")
        
        async with self.buff_client, self.youpin_client:
            all_items = []
            
            # 首先获取总页数
            first_response = await self.buff_client.get_goods_list(page_num=1, page_size=100)
            if not first_response.success:
                logger.error("无法获取商品列表")
                return []
            
            data = first_response.data.get('data', {})
            total_pages = data.get('total_page', 1)
            total_count = data.get('total_count', 0)
            
            logger.info(f"发现 {total_count} 个商品，共 {total_pages} 页")
            
            # 限制页数（避免过多请求）
            if max_pages:
                total_pages = min(total_pages, max_pages)
                logger.info(f"限制获取前 {total_pages} 页")
            
            # 并发获取所有页面的数据
            semaphore = asyncio.Semaphore(5)  # 限制并发数
            tasks = []
            
            for page_num in range(1, total_pages + 1):
                task = self._collect_page_data(semaphore, page_num)
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for i, result in enumerate(results, 1):
                if isinstance(result, Exception):
                    logger.error(f"第{i}页数据收集失败: {result}")
                elif isinstance(result, list):
                    all_items.extend(result)
                    logger.info(f"第{i}页收集完成，获得 {len(result)} 个商品")
            
            logger.info(f"API数据收集完成，共获得 {len(all_items)} 个商品")
            return all_items
    
    async def _collect_page_data(self, semaphore: asyncio.Semaphore, page_num: int) -> List[SkinItem]:
        """收集单页数据"""
        async with semaphore:
            try:
                # 获取Buff数据
                buff_response = await self.buff_client.get_goods_list(page_num=page_num, page_size=100)
                if not buff_response.success:
                    return []
                
                items = buff_response.data.get('data', {}).get('items', [])
                skin_items = []
                
                for item_data in items:
                    # 解析Buff商品
                    skin_item = self.buff_client.parse_goods_item(item_data)
                    if not skin_item:
                        continue
                    
                    # 获取悠悠有品价格
                    youpin_price = await self.youpin_client.search_item(skin_item.name, skin_item.buff_price)
                    if youpin_price:
                        skin_item.youpin_price = youpin_price
                        skin_item.youpin_url = f"{self.youpin_client.base_url}/search?keyword={skin_item.name}"
                    
                    skin_items.append(skin_item)
                    
                    # 控制请求频率
                    await asyncio.sleep(0.1)
                
                return skin_items
                
            except Exception as e:
                logger.error(f"收集第{page_num}页数据失败: {e}")
                return []
    
    async def collect_sample_items(self, count: int = 100) -> List[SkinItem]:
        """收集样本数据（用于测试）"""
        logger.info(f"收集 {count} 个样本商品...")
        
        async with self.buff_client, self.youpin_client:
            # 计算需要的页数
            page_size = 100
            pages_needed = (count + page_size - 1) // page_size
            
            all_items = []
            for page_num in range(1, pages_needed + 1):
                items = await self._collect_page_data(asyncio.Semaphore(1), page_num)
                all_items.extend(items)
                
                if len(all_items) >= count:
                    break
            
            # 只返回所需数量
            return all_items[:count]

# 异步函数包装器
async def collect_all_api_data(max_pages: int = 10) -> List[SkinItem]:
    """收集所有API数据的便捷函数"""
    collector = APIDataCollector()
    return await collector.collect_all_items(max_pages=max_pages)

async def collect_sample_api_data(count: int = 100) -> List[SkinItem]:
    """收集样本API数据的便捷函数"""
    collector = APIDataCollector()
    return await collector.collect_sample_items(count=count) 