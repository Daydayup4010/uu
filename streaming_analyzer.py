#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式价差分析器 - 边获取边分析，实时返回结果
支持增量更新，提升用户体验，集成全局并发控制
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, AsyncGenerator, Callable, Any
from dataclasses import asdict
import logging

from integrated_price_system import PriceDiffItem, BuffAPIClient
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient
from config import Config
from analysis_manager import get_analysis_manager

logger = logging.getLogger(__name__)

class StreamingAnalyzer:
    """流式价差分析器 - 集成全局并发控制"""
    
    def __init__(self, 
                 progress_callback: Optional[Callable] = None,
                 result_callback: Optional[Callable] = None):
        """
        初始化流式分析器
        
        Args:
            progress_callback: 进度回调函数
            result_callback: 结果回调函数
        """
        self.progress_callback = progress_callback
        self.result_callback = result_callback
        
        # 缓存
        self.result_cache: List[PriceDiffItem] = []
        self.buff_cache: Dict[str, Any] = {}
        self.youpin_cache: Dict[str, float] = {}  # hash_name -> price
        self.youpin_name_cache: Dict[str, float] = {}  # name -> price
        
        # 状态追踪
        self.is_running = False
        self.total_processed = 0
        self.total_found = 0
        
    async def start_streaming_analysis(self) -> AsyncGenerator[Dict, None]:
        """启动流式分析 - 集成并发控制"""
        manager = get_analysis_manager()
        analysis_id = f"streaming_{int(time.time())}"
        
        # 尝试启动分析
        if not manager.start_analysis('streaming', analysis_id):
            yield {
                'type': 'error',
                'error': '已有分析在运行，请稍后再试',
                'message': f'当前正在运行: {manager.current_analysis_type}'
            }
            return
        
        try:
            self.is_running = True
            self.total_processed = 0
            self.total_found = 0
            
            # 1. 首先返回缓存数据（如果有）
            cached_results = manager.get_cached_results()
            if cached_results:
                yield {
                    'type': 'cached_data',
                    'data': cached_results,
                    'message': f'返回缓存数据: {len(cached_results)}个商品',
                    'cached': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # 检查是否应该停止
            if manager.should_stop():
                yield {
                    'type': 'cancelled',
                    'message': '分析被取消'
                }
                return
            
            # 2. 开始并行获取数据
            yield {
                'type': 'progress',
                'message': '开始并行获取Buff和悠悠有品数据...',
                'stage': 'data_fetching',
                'progress': 0
            }
            
            # 🔥 修复：首先获取悠悠有品数据构建映射表
            async for progress_info in self._stream_youpin_data():
                # 定期检查是否应该停止
                if manager.should_stop():
                    yield {
                        'type': 'cancelled',
                        'message': '分析被取消'
                    }
                    return
                    
                yield progress_info
                if progress_info.get('type') == 'mapping_ready':
                    break
            
            # 3. 开始流式分析Buff数据
            yield {
                'type': 'progress',
                'message': '开始流式分析Buff商品...',
                'stage': 'analyzing',
                'progress': 0
            }
            
            # 🔥 修复：流式处理Buff数据
            batch_results = []
            async for progress_info in self._stream_buff_data():
                # 定期检查是否应该停止
                if manager.should_stop():
                    yield {
                        'type': 'cancelled',
                        'message': '分析被取消'
                    }
                    return
                    
                if progress_info.get('type') == 'data_batch':
                    # 分析这批数据
                    buff_items = progress_info['data']
                    batch_diff_items = await self._analyze_batch(buff_items)
                    
                    if batch_diff_items:
                        batch_results.extend(batch_diff_items)
                        self.result_cache.extend(batch_diff_items)
                        
                        # 实时返回分析结果
                        yield {
                            'type': 'incremental_results',
                            'data': [asdict(item) for item in batch_diff_items],
                            'batch_size': len(batch_diff_items),
                            'total_found': len(self.result_cache),
                            'total_processed': self.total_processed,
                            'message': f'新发现 {len(batch_diff_items)} 个价差商品'
                        }
                
                elif progress_info.get('type') == 'progress':
                    yield progress_info
            
            # 4. 最终结果
            final_results = [asdict(item) for item in self.result_cache]
            yield {
                'type': 'completed',
                'data': final_results,
                'total_found': len(self.result_cache),
                'total_processed': self.total_processed,
                'message': f'分析完成！共发现 {len(self.result_cache)} 个价差商品',
                'timestamp': datetime.now().isoformat()
            }
            
            # 更新管理器缓存
            manager.finish_analysis(analysis_id, final_results)
            
        except Exception as e:
            logger.error(f"流式分析出错: {e}")
            yield {
                'type': 'error',
                'error': str(e),
                'message': '分析过程出现错误'
            }
            manager.finish_analysis(analysis_id)
        finally:
            self.is_running = False
    
    async def _stream_buff_data(self) -> AsyncGenerator[Dict, None]:
        """流式获取Buff数据"""
        manager = get_analysis_manager()
        
        try:
            async with OptimizedBuffClient() as client:
                # 🔥 如果分析被取消，立即取消客户端
                if manager.should_stop():
                    client.cancel()
                    return
                # 获取第一页确定总数
                first_page = await client.get_goods_list(page_num=1)
                if not first_page or 'data' not in first_page:
                    raise Exception("无法获取Buff第一页数据")
                
                first_data = first_page['data']
                total_pages = min(first_data.get('total_page', 0), Config.BUFF_MAX_PAGES)
                
                yield {
                    'type': 'progress',
                    'message': f'Buff总共{total_pages}页，开始逐页获取...',
                    'stage': 'buff_fetching',
                    'total_pages': total_pages,
                    'current_page': 1
                }
                
                # 处理第一页
                first_items = first_data.get('items', [])
                if first_items:
                    yield {
                        'type': 'data_batch',
                        'data': first_items,
                        'page': 1,
                        'total_pages': total_pages
                    }
                
                # 获取剩余页面
                for page_num in range(2, total_pages + 1):
                    # 检查是否应该停止
                    if not self.is_running or manager.should_stop():
                        logger.info(f"Buff数据获取被停止，已处理{page_num-1}页")
                        client.cancel()  # 🔥 取消客户端
                        break
                        
                    page_data = await client.get_goods_list(page_num=page_num)
                    
                    if page_data and 'data' in page_data:
                        items = page_data['data'].get('items', [])
                        if items:
                            yield {
                                'type': 'data_batch',
                                'data': items,
                                'page': page_num,
                                'total_pages': total_pages
                            }
                    
                    # 报告进度
                    if page_num % 10 == 0:
                        yield {
                            'type': 'progress',
                            'message': f'Buff数据获取进度: {page_num}/{total_pages}页',
                            'stage': 'buff_fetching',
                            'progress': (page_num / total_pages) * 100,
                            'current_page': page_num,
                            'total_pages': total_pages
                        }
                        
        except Exception as e:
            logger.error(f"Buff数据获取出错: {e}")
            yield {
                'type': 'error',
                'error': f'Buff数据获取失败: {str(e)}'
            }
    
    async def _stream_youpin_data(self) -> AsyncGenerator[Dict, None]:
        """流式获取悠悠有品数据并构建映射表"""
        manager = get_analysis_manager()
        
        try:
            async with OptimizedYoupinClient() as client:
                max_pages = Config.YOUPIN_MAX_PAGES
                
                yield {
                    'type': 'progress',
                    'message': f'开始获取悠悠有品数据，最大{max_pages}页...',
                    'stage': 'youpin_fetching',
                    'progress': 0
                }
                
                # 逐页获取并构建映射
                for page_index in range(1, max_pages + 1):
                    # 检查是否应该停止
                    if not self.is_running or manager.should_stop():
                        logger.info(f"悠悠有品数据获取被停止，已处理{page_index-1}页")
                        client.cancel()  # 🔥 取消客户端
                        break
                        
                    items = await client.get_market_goods_safe(page_index=page_index)
                    
                    if items:
                        # 构建映射表
                        for item in items:
                            hash_name = item.get('commodityHashName', '')
                            commodity_name = item.get('commodityName', '')
                            price = item.get('price', 0)
                            
                            try:
                                price_float = float(price) if price else None
                                if price_float:
                                    if hash_name:
                                        self.youpin_cache[hash_name] = price_float
                                    if commodity_name:
                                        self.youpin_name_cache[commodity_name] = price_float
                            except (ValueError, TypeError):
                                continue
                        
                        # 报告进度
                        if page_index % 10 == 0:
                            yield {
                                'type': 'progress',
                                'message': f'悠悠有品映射构建: {page_index}页，累计{len(self.youpin_cache)}个Hash映射',
                                'stage': 'youpin_mapping',
                                'progress': (page_index / max_pages) * 100,
                                'hash_count': len(self.youpin_cache),
                                'name_count': len(self.youpin_name_cache)
                            }
                    else:
                        # 如果获取失败或无数据，结束获取
                        break
                
                # 映射表构建完成
                yield {
                    'type': 'mapping_ready',
                    'message': f'悠悠有品映射表构建完成: {len(self.youpin_cache)}个Hash映射, {len(self.youpin_name_cache)}个名称映射',
                    'hash_count': len(self.youpin_cache),
                    'name_count': len(self.youpin_name_cache)
                }
                
        except Exception as e:
            logger.error(f"悠悠有品数据获取出错: {e}")
            yield {
                'type': 'error',
                'error': f'悠悠有品数据获取失败: {str(e)}'
            }
    
    async def _analyze_batch(self, buff_items: List[Dict]) -> List[PriceDiffItem]:
        """分析一批Buff商品"""
        diff_items = []
        
        # 创建临时BuffAPIClient用于解析
        buff_client = BuffAPIClient()
        
        for item_data in buff_items:
            self.total_processed += 1
            
            # 解析Buff商品
            buff_item = buff_client.parse_goods_item(item_data)
            if not buff_item:
                continue

            # 🔥 检查Buff价格是否在筛选范围内
            if not Config.is_buff_price_in_range(buff_item.buff_price):
                continue

            # 查找悠悠有品价格
            youpin_price = None
            matched_by = None
            
            # 1. Hash精确匹配
            if buff_item.hash_name and buff_item.hash_name in self.youpin_cache:
                youpin_price = self.youpin_cache[buff_item.hash_name]
                matched_by = "Hash精确匹配"
            
            # 2. 名称精确匹配（备用）
            elif buff_item.name in self.youpin_name_cache:
                youpin_price = self.youpin_name_cache[buff_item.name]
                matched_by = "名称精确匹配"
            
            if not youpin_price:
                continue
            
            # 计算价差
            price_diff = youpin_price - buff_item.buff_price
            if buff_item.buff_price > 0:
                profit_rate = (price_diff / buff_item.buff_price) * 100
            else:
                profit_rate = 0
            
            # 检查是否符合价差区间
            if Config.is_price_diff_in_range(price_diff):
                self.total_found += 1
                
                diff_item = PriceDiffItem(
                    id=buff_item.id,
                    name=buff_item.name,
                    buff_price=buff_item.buff_price,
                    youpin_price=youpin_price,
                    price_diff=price_diff,
                    profit_rate=profit_rate,
                    buff_url=buff_item.buff_url,
                    youpin_url=f"https://www.youpin898.com/search?keyword={buff_item.name}",
                    image_url=buff_item.image_url,
                    category=buff_item.category,
                    last_updated=datetime.now()
                )
                
                diff_items.append(diff_item)
        
        return diff_items
    
    def get_current_results(self) -> List[PriceDiffItem]:
        """获取当前分析结果"""
        return self.result_cache.copy()
    
    def clear_cache(self):
        """清除缓存"""
        self.result_cache.clear()
        self.buff_cache.clear()
        self.youpin_cache.clear()
        self.youpin_name_cache.clear()
        self.total_processed = 0
        self.total_found = 0
    
    def stop_analysis(self):
        """停止分析"""
        self.is_running = False

# 使用示例
async def test_streaming_analyzer():
    """测试流式分析器"""
    print("🎯 测试流式价差分析器")
    print("="*50)
    
    def progress_callback(info):
        print(f"📊 进度: {info.get('message', '')}")
    
    def result_callback(diff_items):
        print(f"🎯 发现价差商品: {len(diff_items)}个")
    
    analyzer = StreamingAnalyzer(
        progress_callback=progress_callback,
        result_callback=result_callback
    )
    
    async for update in analyzer.start_streaming_analysis():
        update_type = update.get('type')
        message = update.get('message', '')
        
        if update_type == 'cached_data':
            print(f"💾 缓存数据: {len(update['data'])}个商品")
        elif update_type == 'progress':
            progress = update.get('progress', 0)
            print(f"📈 {message} ({progress:.1f}%)")
        elif update_type == 'incremental_results':
            batch_size = update.get('batch_size', 0)
            total_found = update.get('total_found', 0)
            print(f"✅ 增量结果: +{batch_size}个, 总计: {total_found}个")
        elif update_type == 'completed':
            total_found = update.get('total_found', 0)
            print(f"🎉 分析完成: 共发现{total_found}个价差商品")
            break
        elif update_type == 'error':
            print(f"❌ 错误: {update.get('error', '')}")
            break

if __name__ == "__main__":
    asyncio.run(test_streaming_analyzer()) 