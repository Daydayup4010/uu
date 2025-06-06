#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新管理器 - 实现全量更新和增量更新
全量更新：1小时获取一次全部数据
增量更新：1分钟搜索指定hashname的数据
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from dataclasses import asdict
import threading
import pickle

from integrated_price_system import PriceDiffItem, IntegratedPriceAnalyzer
from search_api_client import SearchManager, SearchResult
from analysis_manager import get_analysis_manager
from config import Config
from data_storage import DataStorage

logger = logging.getLogger(__name__)

class HashNameCache:
    """HashName缓存管理器"""
    
    def __init__(self, cache_file: str = "data/hashname_cache.pkl"):
        self.cache_file = cache_file
        self.hashnames: Set[str] = set()
        self.last_full_update = None
        self.load_cache()
    
    def save_cache(self):
        """保存缓存到文件"""
        try:
            cache_data = {
                'hashnames': list(self.hashnames),
                'last_full_update': self.last_full_update.isoformat() if self.last_full_update else None
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
            logger.info(f"HashName缓存已保存: {len(self.hashnames)}个")
            
        except Exception as e:
            logger.error(f"保存HashName缓存失败: {e}")
    
    def load_cache(self):
        """从文件加载缓存"""
        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.hashnames = set(cache_data.get('hashnames', []))
            last_update_str = cache_data.get('last_full_update')
            
            if last_update_str:
                self.last_full_update = datetime.fromisoformat(last_update_str)
            
            logger.info(f"HashName缓存已加载: {len(self.hashnames)}个")
            
        except FileNotFoundError:
            logger.info("HashName缓存文件不存在，将创建新缓存")
        except Exception as e:
            logger.error(f"加载HashName缓存失败: {e}")
    
    def update_from_full_analysis(self, diff_items: List[PriceDiffItem]):
        """从全量分析结果更新缓存"""
        new_hashnames = set()
        
        for item in diff_items:
            # 提取hashname（从name或URL中）
            if hasattr(item, 'hash_name') and item.hash_name:
                new_hashnames.add(item.hash_name)
            elif item.name:
                # 如果没有hash_name，使用name作为搜索关键词
                new_hashnames.add(item.name)
        
        # 限制缓存大小
        if len(new_hashnames) > Config.INCREMENTAL_CACHE_SIZE:
            # 按某种优先级排序（例如价差大小）
            sorted_items = sorted(diff_items, key=lambda x: x.price_diff, reverse=True)
            new_hashnames = set()
            for item in sorted_items[:Config.INCREMENTAL_CACHE_SIZE]:
                if hasattr(item, 'hash_name') and item.hash_name:
                    new_hashnames.add(item.hash_name)
                elif item.name:
                    new_hashnames.add(item.name)
        
        self.hashnames = new_hashnames
        self.last_full_update = datetime.now()
        self.save_cache()
        
        logger.info(f"HashName缓存已更新: {len(self.hashnames)}个关键词")
    
    def get_hashnames_for_search(self) -> List[str]:
        """获取用于搜索的hashname列表"""
        return list(self.hashnames)
    
    def should_full_update(self) -> bool:
        """检查是否需要全量更新"""
        if not self.last_full_update:
            return True
        
        time_since_update = datetime.now() - self.last_full_update
        return time_since_update >= timedelta(hours=Config.FULL_UPDATE_INTERVAL_HOURS)

class UpdateManager:
    """更新管理器 - 协调全量和增量更新"""
    
    def __init__(self):
        self.is_running = False
        self.hashname_cache = HashNameCache()
        self.current_diff_items: List[PriceDiffItem] = []
        self.last_full_update = None
        self.last_incremental_update = None
        
        # 🔥 新增：数据存储管理器
        try:
            from data_storage import DataStorage
            self.data_storage = DataStorage()
        except ImportError:
            self.data_storage = None
        
        # 🔥 新增：初始全量更新完成标志
        self.initial_full_update_completed = False
        
        # 线程控制
        self.full_update_thread = None
        self.incremental_update_thread = None
        self.stop_event = threading.Event()
    
    def start(self):
        """启动更新管理器"""
        if self.is_running:
            logger.warning("更新管理器已在运行")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        logger.info("🚀 启动更新管理器")
        
        # 🔥 修改：检查是否需要初始全量更新
        needs_initial_update = self.hashname_cache.should_full_update()
        if needs_initial_update:
            logger.info("📊 需要初始全量更新，将等待完成后再启动增量更新")
            self.initial_full_update_completed = False
        else:
            logger.info("📊 有缓存数据，可直接启动增量更新")
            self.initial_full_update_completed = True
        
        # 启动全量更新线程
        self.full_update_thread = threading.Thread(
            target=self._full_update_loop, 
            daemon=True, 
            name="FullUpdateLoop"
        )
        self.full_update_thread.start()
        
        # 启动增量更新线程
        self.incremental_update_thread = threading.Thread(
            target=self._incremental_update_loop, 
            daemon=True, 
            name="IncrementalUpdateLoop"
        )
        self.incremental_update_thread.start()
        
        # 🔥 修复：无论是否需要初始更新，都不在这里立即执行
        # 让定时循环来处理，避免重复执行
        if not needs_initial_update:
            # 🔥 优先尝试从保存的full data文件重新筛选
            try:
                from saved_data_processor import get_saved_data_processor
                processor = get_saved_data_processor()
                
                if processor.has_valid_full_data():
                    logger.info("📂 发现已保存的全量数据文件，从文件重新筛选...")
                    diff_items, stats = processor.reprocess_with_current_filters()
                    
                    if diff_items is not None:
                        self.current_diff_items = diff_items
                        self._save_current_data()
                        self.initial_full_update_completed = True
                        logger.info(f"✅ 从保存数据重新筛选成功: {len(diff_items)}个商品")
                        logger.info(f"📂 使用文件: {stats.get('buff_file')}, {stats.get('youpin_file')}")
                    else:
                        raise Exception("从保存数据重新筛选失败")
                else:
                    raise Exception("没有找到有效的全量数据文件")
                    
            except Exception as e:
                logger.warning(f"⚠️ 从保存数据重新筛选失败: {e}")
                logger.info("🔄 尝试加载缓存数据...")
                
                # 回退到原来的加载缓存数据逻辑
                try:
                    self._load_latest_data()
                    if self.current_diff_items:
                        self.initial_full_update_completed = True
                        logger.info(f"✅ 成功加载缓存数据: {len(self.current_diff_items)}个商品")
                    else:
                        logger.warning("⚠️ 缓存数据为空，将强制执行全量更新")
                        self.initial_full_update_completed = False
                        self.hashname_cache.hashnames.clear()
                        self.hashname_cache.last_full_update = None
                except Exception as e2:
                    logger.error(f"❌ 加载缓存数据失败: {e2}，将强制执行全量更新")
                    self.initial_full_update_completed = False
                    self.hashname_cache.hashnames.clear()
                    self.hashname_cache.last_full_update = None
        
        logger.info("🎯 启动完成，定时循环将处理更新任务")
    
    def stop(self):
        """停止更新管理器"""
        if not self.is_running:
            return
        
        logger.info("🛑 停止更新管理器")
        self.is_running = False
        self.stop_event.set()
        
        # 等待线程结束
        if self.full_update_thread and self.full_update_thread.is_alive():
            self.full_update_thread.join(timeout=5)
        
        if self.incremental_update_thread and self.incremental_update_thread.is_alive():
            self.incremental_update_thread.join(timeout=5)
    
    def _full_update_loop(self):
        """全量更新循环"""
        # 🔥 修复死锁：如果需要初始更新，立即执行一次
        if not self.initial_full_update_completed and self.hashname_cache.should_full_update():
            logger.info("🔄 立即执行初始全量更新...")
            self._trigger_full_update(is_initial=True)
            
            # 等待初始更新完成
            logger.info("⏳ 等待初始全量更新完成...")
            while self.is_running and not self.stop_event.is_set():
                if self.initial_full_update_completed:
                    break
                # 每5秒检查一次
                if self.stop_event.wait(timeout=5):
                    return
        
        logger.info("✅ 开始全量更新定时循环")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 检查是否需要定时全量更新
                if self.hashname_cache.should_full_update():
                    logger.info("⏰ 开始定时全量更新")
                    self._trigger_full_update()
                
                # 等待1小时或直到停止
                if self.stop_event.wait(timeout=3600):  # 1小时 = 3600秒
                    break
                    
            except Exception as e:
                logger.error(f"全量更新循环出错: {e}")
                # 出错后等待5分钟再重试
                if self.stop_event.wait(timeout=300):
                    break
    
    def _incremental_update_loop(self):
        """增量更新循环"""
        # 🔥 新增：等待初始全量更新完成
        if not self.initial_full_update_completed:
            logger.info("⏳ 增量更新等待初始全量更新完成...")
            while self.is_running and not self.stop_event.is_set():
                if self.initial_full_update_completed:
                    logger.info("✅ 初始全量更新已完成，开始增量更新循环")
                    break
                # 每5秒检查一次
                if self.stop_event.wait(timeout=5):
                    return
        
        # 🔥 开始正常的增量更新循环
        while self.is_running and not self.stop_event.is_set():
            try:
                # 检查是否有hashname可以搜索
                if self.hashname_cache.hashnames:
                    logger.info("🔄 开始增量更新")
                    self._trigger_incremental_update()
                else:
                    logger.debug("没有缓存的hashname，跳过增量更新")
                
                # 使用配置的增量更新间隔
                interval_seconds = Config.INCREMENTAL_UPDATE_INTERVAL_MINUTES * 60
                if self.stop_event.wait(timeout=interval_seconds):
                    break
                    
            except Exception as e:
                logger.error(f"增量更新循环出错: {e}")
                # 出错后等待30秒再重试
                if self.stop_event.wait(timeout=30):
                    break
    
    def _trigger_full_update(self, is_initial=False):
        """触发全量更新"""
        manager = get_analysis_manager()
        analysis_id = f"full_update_{int(time.time())}"
        
        # 🔥 修复：使用强制模式，避免多个分析同时运行
        if not manager.start_analysis('full_update', analysis_id, force=True):
            logger.warning("全量更新跳过：无法启动分析")
            return
        
        def run_async_analysis():
            """在新线程中运行异步分析"""
            try:
                # 在新的事件循环中运行异步全量分析
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    diff_items = loop.run_until_complete(self._run_full_analysis())
                    
                    if diff_items:
                        # 更新当前数据
                        self.current_diff_items = diff_items
                        self.last_full_update = datetime.now()
                        
                        # 🔥 保存当前数据到文件
                        self._save_current_data()
                        
                        # 更新hashname缓存
                        self.hashname_cache.update_from_full_analysis(diff_items)
                        
                        # 完成分析
                        manager.finish_analysis(analysis_id, diff_items)
                        
                        logger.info(f"✅ 全量更新完成: {len(diff_items)}个商品")
                        
                        # 🔥 新增：如果是初始更新，设置完成标志
                        if is_initial:
                            self.initial_full_update_completed = True
                            logger.info("🎯 初始全量更新已完成，增量更新可以开始了")
                    else:
                        logger.warning("全量更新未获取到数据")
                        manager.finish_analysis(analysis_id, [])
                        
                        # 🔥 即使没有数据，也标记初始更新完成（避免卡住）
                        if is_initial:
                            self.initial_full_update_completed = True
                            logger.info("⚠️ 初始全量更新无数据，但标记为完成以启动增量更新")
                        
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"全量更新失败: {e}")
                manager.finish_analysis(analysis_id)
                
                # 🔥 新增：即使出错，也标记初始更新完成（避免系统卡住）
                if is_initial:
                    self.initial_full_update_completed = True
                    logger.error("❌ 初始全量更新失败，但标记为完成以启动增量更新")
        
        # 在新线程中运行异步任务
        thread = threading.Thread(target=run_async_analysis, daemon=True)
        thread.start()
    
    def _trigger_incremental_update(self):
        """触发增量更新"""
        manager = get_analysis_manager()
        analysis_id = f"incremental_update_{int(time.time())}"
        
        # 尝试启动增量分析（非阻塞）
        if not manager.start_analysis('incremental_update', analysis_id, force=False):
            logger.debug("增量更新跳过：已有分析在运行")
            return
        
        def run_async_analysis():
            """在新线程中运行异步分析"""
            try:
                # 在新的事件循环中运行异步增量分析
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    incremental_items = loop.run_until_complete(self._run_incremental_analysis())
                    
                    if incremental_items:
                        # 合并到当前数据中（去重）
                        self._merge_incremental_data(incremental_items)
                        
                        # 🔥 保存合并后的数据到文件
                        self._save_current_data()
                        
                        # 更新全局缓存
                        manager.finish_analysis(analysis_id, self.current_diff_items)
                        
                        logger.info(f"✅ 增量更新完成: 新增/更新 {len(incremental_items)}个商品")
                    else:
                        logger.debug("增量更新无新数据")
                        manager.finish_analysis(analysis_id, [])
                    
                    self.last_incremental_update = datetime.now()
                        
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"增量更新失败: {e}")
                manager.finish_analysis(analysis_id)
        
        # 在新线程中运行异步任务
        thread = threading.Thread(target=run_async_analysis, daemon=True)
        thread.start()
    
    async def _run_full_analysis(self) -> List[PriceDiffItem]:
        """运行全量分析"""
        async with IntegratedPriceAnalyzer() as analyzer:
            return await analyzer.analyze_price_differences(
                max_output_items=Config.MAX_OUTPUT_ITEMS
            )
    
    async def _run_incremental_analysis(self) -> List[PriceDiffItem]:
        """运行增量分析"""
        hashnames = self.hashname_cache.get_hashnames_for_search()
        if not hashnames:
            return []
        
        incremental_items = []
        
        async with SearchManager() as search_manager:
            # 逐个搜索hashname（限制并发）
            semaphore = asyncio.Semaphore(5)  # 最多5个并发搜索
            
            async def search_and_analyze(keyword):
                async with semaphore:
                    try:
                        # 搜索两个平台
                        results = await search_manager.search_both_platforms(keyword)
                        
                        # 分析价差
                        diff_items = self._analyze_search_results(results)
                        return diff_items
                        
                    except Exception as e:
                        logger.error(f"增量搜索失败 {keyword}: {e}")
                        return []
            
            # 批量处理（避免过多并发）
            batch_size = 10
            for i in range(0, len(hashnames), batch_size):
                batch_keywords = hashnames[i:i + batch_size]
                
                tasks = [search_and_analyze(keyword) for keyword in batch_keywords]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"批量搜索异常: {result}")
                    elif result:
                        incremental_items.extend(result)
                
                # 批次间延迟
                await asyncio.sleep(1)
        
        return incremental_items
    
    def _analyze_search_results(self, search_results: Dict) -> List[PriceDiffItem]:
        """分析搜索结果，计算价差"""
        diff_items = []
        
        youpin_results = search_results.get('youpin', [])
        buff_results = search_results.get('buff', [])
        
        # 按hash_name匹配价格
        youpin_prices = {item.hash_name: item for item in youpin_results if item.hash_name}
        buff_prices = {item.hash_name: item for item in buff_results if item.hash_name}
        
        # 如果没有hash_name，使用name匹配
        if not youpin_prices:
            youpin_prices = {item.name: item for item in youpin_results}
        if not buff_prices:
            buff_prices = {item.name: item for item in buff_results}
        
        # 匹配并计算价差
        for hash_name, buff_item in buff_prices.items():
            youpin_item = youpin_prices.get(hash_name)
            
            if youpin_item and buff_item.price > 0 and youpin_item.price > 0:
                # 检查Buff价格是否在筛选范围内
                if not Config.is_buff_price_in_range(buff_item.price):
                    continue
                
                # 🔥 新增：检查Buff在售数量是否符合条件
                if hasattr(buff_item, 'sell_num') and buff_item.sell_num is not None:
                    if not Config.is_buff_sell_num_valid(buff_item.sell_num):
                        continue
                
                price_diff = youpin_item.price - buff_item.price
                
                # 检查价差是否符合要求
                if Config.is_price_diff_in_range(price_diff):
                    profit_rate = (price_diff / buff_item.price) * 100 if buff_item.price > 0 else 0
                    
                    diff_item = PriceDiffItem(
                        id=buff_item.id,
                        name=buff_item.name,
                        buff_price=buff_item.price,
                        youpin_price=youpin_item.price,
                        price_diff=price_diff,
                        profit_rate=profit_rate,
                        buff_url=buff_item.market_url,
                        youpin_url=youpin_item.market_url,
                        image_url=buff_item.image_url,
                        category="搜索结果",
                        last_updated=datetime.now()
                    )
                    
                    diff_items.append(diff_item)
        
        return diff_items
    
    def _merge_incremental_data(self, incremental_items: List[PriceDiffItem]):
        """合并增量数据到当前数据中"""
        # 创建当前数据的索引（按name或id）
        current_index = {}
        for i, item in enumerate(self.current_diff_items):
            key = f"{item.name}_{item.id}" if item.id else item.name
            current_index[key] = i
        
        # 合并新数据
        for new_item in incremental_items:
            key = f"{new_item.name}_{new_item.id}" if new_item.id else new_item.name
            
            if key in current_index:
                # 更新现有商品
                self.current_diff_items[current_index[key]] = new_item
            else:
                # 添加新商品
                self.current_diff_items.append(new_item)
        
        # 按价差排序
        self.current_diff_items.sort(key=lambda x: x.price_diff, reverse=True)
        
        # 限制数量
        if len(self.current_diff_items) > Config.MAX_OUTPUT_ITEMS:
            self.current_diff_items = self.current_diff_items[:Config.MAX_OUTPUT_ITEMS]
    
    def get_current_data(self) -> List[PriceDiffItem]:
        """获取当前数据"""
        return self.current_diff_items.copy()
    
    def get_status(self) -> Dict:
        """获取更新状态"""
        return {
            'is_running': self.is_running,
            'initial_full_update_completed': self.initial_full_update_completed,
            'last_full_update': self.last_full_update.isoformat() if self.last_full_update else None,
            'last_incremental_update': self.last_incremental_update.isoformat() if self.last_incremental_update else None,
            'current_items_count': len(self.current_diff_items),
            'cached_hashnames_count': len(self.hashname_cache.hashnames),
            'should_full_update': self.hashname_cache.should_full_update(),
            'full_update_interval_hours': Config.FULL_UPDATE_INTERVAL_HOURS,
            'incremental_update_interval_minutes': Config.INCREMENTAL_UPDATE_INTERVAL_MINUTES
        }
    
    def force_full_update(self):
        """强制全量更新"""
        logger.info("🔄 强制执行全量更新")
        # 🔥 修复：直接调用而不是创建新线程，避免多个线程同时运行
        self._trigger_full_update()
    
    def force_incremental_update(self):
        """强制增量更新"""
        logger.info("🔄 强制执行增量更新")
        threading.Thread(target=self._trigger_incremental_update, daemon=True).start()
    
    def _load_latest_data(self):
        """加载最新的价差数据"""
        try:
            import os  # 🔥 确保os模块可用
            # 尝试加载保存的价差数据
            if os.path.exists(Config.LATEST_DATA_FILE):
                with open(Config.LATEST_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换为PriceDiffItem对象
                loaded_items = []
                for item_data in data.get('items', []):
                    try:
                        item = PriceDiffItem(
                            id=item_data.get('id', ''),
                            name=item_data.get('name', ''),
                            buff_price=float(item_data.get('buff_price', 0)),
                            youpin_price=float(item_data.get('youpin_price', 0)),
                            price_diff=float(item_data.get('price_diff', 0)),
                            profit_rate=float(item_data.get('profit_rate', 0)),
                            buff_url=item_data.get('buff_url', ''),
                            youpin_url=item_data.get('youpin_url', ''),
                            image_url=item_data.get('image_url', ''),
                            category=item_data.get('category', ''),
                            last_updated=datetime.fromisoformat(item_data['last_updated']) if item_data.get('last_updated') else datetime.now()
                        )
                        loaded_items.append(item)
                    except Exception as e:
                        logger.warning(f"解析保存的商品数据失败: {e}")
                        continue
                
                if loaded_items:
                    self.current_diff_items = loaded_items
                    # 从文件元数据获取更新时间
                    metadata = data.get('metadata', {})
                    if metadata.get('last_full_update'):
                        self.last_full_update = datetime.fromisoformat(metadata['last_full_update'])
                    
                    logger.info(f"📊 已加载缓存数据: {len(loaded_items)}个商品")
                else:
                    logger.warning("缓存数据文件为空")
            else:
                logger.info("未找到缓存数据文件")
                
        except Exception as e:
            logger.error(f"加载最新数据失败: {e}")
    
    def _save_current_data(self):
        """保存当前数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(Config.LATEST_DATA_FILE), exist_ok=True)
            
            # 转换为可序列化的格式
            items_data = []
            for item in self.current_diff_items:
                items_data.append({
                    'id': item.id,
                    'name': item.name,
                    'buff_price': item.buff_price,
                    'youpin_price': item.youpin_price,
                    'price_diff': item.price_diff,
                    'profit_rate': item.profit_rate,
                    'buff_url': item.buff_url,
                    'youpin_url': item.youpin_url,
                    'image_url': item.image_url,
                    'category': item.category,
                    'last_updated': item.last_updated.isoformat() if item.last_updated else None
                })
            
            data = {
                'metadata': {
                    'last_full_update': self.last_full_update.isoformat() if self.last_full_update else None,
                    'last_incremental_update': self.last_incremental_update.isoformat() if self.last_incremental_update else None,
                    'total_count': len(items_data),
                    'generated_at': datetime.now().isoformat()
                },
                'items': items_data
            }
            
            # 保存到文件
            with open(Config.LATEST_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"💾 已保存 {len(items_data)} 个商品到缓存文件")
            
        except Exception as e:
            logger.error(f"保存当前数据失败: {e}")

# 全局更新管理器实例
_update_manager_instance = None

def get_update_manager() -> UpdateManager:
    """获取更新管理器实例（单例模式）"""
    global _update_manager_instance
    if _update_manager_instance is None:
        _update_manager_instance = UpdateManager()
    return _update_manager_instance

# 测试功能
async def test_update_manager():
    """测试更新管理器"""
    print("🧪 测试更新管理器")
    print("="*50)
    
    manager = get_update_manager()
    
    # 显示状态
    status = manager.get_status()
    print(f"状态: {status}")
    
    # 强制执行一次全量更新
    print("\n🔄 执行全量更新测试...")
    manager.force_full_update()
    
    # 等待一段时间
    await asyncio.sleep(30)
    
    # 显示结果
    data = manager.get_current_data()
    print(f"当前数据: {len(data)}个商品")
    
    if data:
        print("前3个商品:")
        for i, item in enumerate(data[:3], 1):
            print(f"  {i}. {item.name}: 价差¥{item.price_diff:.2f}")

if __name__ == "__main__":
    asyncio.run(test_update_manager()) 