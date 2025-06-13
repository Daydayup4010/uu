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
from asyncio_utils import SafeEventLoop, safe_close_loop

# 🔥 使用增强的日志配置
try:
    from log_config import setup_logging
    logger = setup_logging(log_level='INFO', app_name='update_manager')
except ImportError:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HashNameCache:
    """HashName缓存管理器"""
    
    def __init__(self, cache_file: str = "data/hashname_cache.pkl"):
        self.cache_file = cache_file
        # 🔥 修改：存储hash_name -> 利润率的映射
        self.hashname_profits: Dict[str, float] = {}
        self.last_full_update = None
        self.load_cache()
    
    def save_cache(self):
        """保存缓存到文件"""
        try:
            cache_data = {
                'hashname_profits': self.hashname_profits,
                'last_full_update': self.last_full_update.isoformat() if self.last_full_update else None
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
            logger.info(f"HashName缓存已保存: {len(self.hashname_profits)}个（含利润率信息）")
            
        except Exception as e:
            logger.error(f"保存HashName缓存失败: {e}")
    
    def load_cache(self):
        """从文件加载缓存"""
        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 🔥 兼容旧格式和新格式
            if 'hashname_profits' in cache_data:
                # 新格式：包含利润率信息
                self.hashname_profits = cache_data.get('hashname_profits', {})
                logger.info(f"HashName缓存已加载: {len(self.hashname_profits)}个（含利润率信息）")
            else:
                # 旧格式：只有hashnames列表，转换为新格式
                old_hashnames = cache_data.get('hashnames', [])
                self.hashname_profits = {name: 0.0 for name in old_hashnames}
                logger.info(f"HashName缓存已加载（旧格式转换）: {len(self.hashname_profits)}个")
            
            last_update_str = cache_data.get('last_full_update')
            if last_update_str:
                self.last_full_update = datetime.fromisoformat(last_update_str)
            
        except FileNotFoundError:
            logger.info("HashName缓存文件不存在，将创建新缓存")
        except Exception as e:
            logger.error(f"加载HashName缓存失败: {e}")
    
    @property
    def hashnames(self) -> Set[str]:
        """向后兼容：返回所有hash_name的集合"""
        return set(self.hashname_profits.keys())
    
    def update_from_full_analysis(self, diff_items: List[PriceDiffItem]):
        """从全量分析结果更新缓存"""
        new_hashname_profits = {}
        
        for item in diff_items:
            # 🔥 修复：正确处理两种不同的PriceDiffItem类型
            hash_name = None
            profit_rate = 0.0
            
            # 方式1: integrated_price_system.py的PriceDiffItem (直接hash_name属性)
            if hasattr(item, 'hash_name') and item.hash_name:
                hash_name = item.hash_name
                profit_rate = getattr(item, 'profit_rate', 0.0)
                logger.debug(f"   缓存hash_name (直接): {hash_name}, 利润率: {profit_rate:.2%}")
            
            # 方式2: models.py的PriceDiffItem (通过skin_item.hash_name)
            elif hasattr(item, 'skin_item') and hasattr(item.skin_item, 'hash_name') and item.skin_item.hash_name:
                hash_name = item.skin_item.hash_name
                profit_rate = getattr(item, 'profit_rate', 0.0)
                logger.debug(f"   缓存hash_name (skin_item): {hash_name}, 利润率: {profit_rate:.2%}")
            
            # 如果找到了有效的hash_name，使用它
            if hash_name:
                new_hashname_profits[hash_name] = profit_rate
            else:
                # 备选：如果没有hash_name，使用name（但会影响搜索效果）
                item_name = getattr(item, 'name', None) or (getattr(item, 'skin_item', None) and getattr(item.skin_item, 'name', None))
                if item_name:
                    new_hashname_profits[item_name] = profit_rate
                    logger.warning(f"   ⚠️ 使用name作为缓存关键词: {item_name}, 利润率: {profit_rate:.2%}")
        
        # 限制缓存大小，保留利润率最高的商品
        if len(new_hashname_profits) > Config.INCREMENTAL_CACHE_SIZE:
            # 按利润率排序，保留前N个
            sorted_items = sorted(new_hashname_profits.items(), key=lambda x: x[1], reverse=True)
            new_hashname_profits = dict(sorted_items[:Config.INCREMENTAL_CACHE_SIZE])
            logger.info(f"   限制缓存大小到 {Config.INCREMENTAL_CACHE_SIZE}个，保留利润率最高的商品")
        
        self.hashname_profits = new_hashname_profits
        self.last_full_update = datetime.now()
        self.save_cache()
        
        # 🔥 统计信息
        if new_hashname_profits:
            max_profit = max(new_hashname_profits.values())
            min_profit = min(new_hashname_profits.values())
            avg_profit = sum(new_hashname_profits.values()) / len(new_hashname_profits)
            
            logger.info(f"HashName缓存已更新: {len(new_hashname_profits)}个关键词")
            logger.info(f"   📈 利润率范围: {min_profit:.2%} ~ {max_profit:.2%}")
            logger.info(f"   📊 平均利润率: {avg_profit:.2%}")
        else:
            logger.warning("HashName缓存更新后为空")
    
    def get_hashnames_for_search(self) -> List[str]:
        """获取用于搜索的hashname列表，同时返回利润率前25和差价前25的商品"""
        if not self.hashname_profits:
            logger.warning("没有缓存的hashname可供搜索")
            return []
        
        # 🔥 修改：同时获取利润率前25和差价前25的商品
        # 1. 按利润率排序
        profit_sorted = sorted(self.hashname_profits.items(), key=lambda x: x[1], reverse=True)
        top_profit = profit_sorted[:25]
        
        # 2. 按差价排序（从全量数据中获取）
        try:
            from saved_data_processor import get_saved_data_processor
            processor = get_saved_data_processor()
            if processor.has_valid_full_data():
                diff_items, _ = processor.reprocess_with_current_filters()
                if diff_items:
                    # 创建hash_name到差价的映射
                    price_diff_map = {}
                    for item in diff_items:
                        hash_name = getattr(item, 'hash_name', None) or (getattr(item, 'skin_item', None) and getattr(item.skin_item, 'hash_name', None))
                        if hash_name:
                            price_diff_map[hash_name] = getattr(item, 'price_diff', 0.0)
                    
                    # 按差价排序
                    diff_sorted = sorted(price_diff_map.items(), key=lambda x: x[1], reverse=True)
                    top_diff = diff_sorted[:25]
                else:
                    top_diff = []
            else:
                top_diff = []
        except Exception as e:
            logger.error(f"获取差价排序失败: {e}")
            top_diff = []
        
        # 合并两个列表，去重
        all_hashnames = set()
        for hash_name, _ in top_profit:
            all_hashnames.add(hash_name)
        for hash_name, _ in top_diff:
            all_hashnames.add(hash_name)
        
        hashnames_list = list(all_hashnames)
        
        logger.info(f"🎯 增量搜索关键词（利润率前25 + 差价前25）:")
        logger.info(f"   📊 从{len(self.hashname_profits)}个中选择{len(hashnames_list)}个")
        
        if top_profit:
            logger.info(f"   📈 利润率范围: {top_profit[-1][1]:.2%} ~ {top_profit[0][1]:.2%}")
            
            # 显示前5个商品
            logger.info(f"   🔝 利润率前5个商品:")
            for i, (hash_name, profit_rate) in enumerate(top_profit[:5]):
                logger.info(f"      {i+1}. {hash_name} ({profit_rate:.2%})")
        
        if top_diff:
            logger.info(f"   💰 差价前5个商品:")
            for i, (hash_name, price_diff) in enumerate(top_diff[:5]):
                logger.info(f"      {i+1}. {hash_name} (差价: ¥{price_diff:.2f})")
        
        return hashnames_list
    
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
        
        # 🔥 新增：优先检查full data文件并重新生成缓存
        if self._regenerate_cache_from_full_data():
            logger.info("✅ 从full data文件重新生成缓存成功")
            self.initial_full_update_completed = True
        else:
            # 🔥 原有逻辑：检查是否需要初始全量更新
            needs_initial_update = self.hashname_cache.should_full_update()
            if needs_initial_update:
                logger.info("📊 需要初始全量更新，将等待完成后再启动增量更新")
                self.initial_full_update_completed = False
            else:
                logger.info("📊 有缓存数据，可直接启动增量更新")
                self.initial_full_update_completed = True
                    
                # 🔥 尝试加载已有的价差数据
                try:
                    self._load_latest_data()
                    if self.current_diff_items:
                        logger.info(f"✅ 成功加载缓存数据: {len(self.current_diff_items)}个商品")
                    else:
                        logger.warning("⚠️ 缓存数据为空，将强制执行全量更新")
                        self.initial_full_update_completed = False
                        self.hashname_cache.hashname_profits.clear()
                        self.hashname_cache.last_full_update = None
                except Exception as e:
                    logger.error(f"❌ 加载缓存数据失败: {e}，将强制执行全量更新")
                    self.initial_full_update_completed = False
                    self.hashname_cache.hashname_profits.clear()
                    self.hashname_cache.last_full_update = None
        
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
        
        # 尝试启动全量分析（强制模式）
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
                    # 运行全量分析
                    updated_items = loop.run_until_complete(self._run_full_analysis())
                    
                    if updated_items:
                        # 更新当前数据
                        self.current_diff_items = updated_items
                        
                        # 保存当前数据到文件
                        self._save_current_data()
                        
                        # 更新全局缓存
                        manager.finish_analysis(analysis_id, updated_items)
                        
                        logger.info(f"✅ 全量更新完成: 分析出 {len(updated_items)} 个符合条件的商品")
                    else:
                        logger.info("📭 全量更新未发现符合条件的商品")
                        manager.finish_analysis(analysis_id, [])
                    
                    self.last_full_update = datetime.now()
                    
                    # 如果是初始全量更新，标记为完成
                    if is_initial:
                        self.initial_full_update_completed = True
                        logger.info("✅ 初始全量更新完成，可以开始增量更新")
                        
                finally:
                    # 确保所有异步资源都被清理
                    try:
                        # 等待所有挂起的任务完成
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            logger.debug(f"等待 {len(pending)} 个挂起的任务完成...")
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception as e:
                        logger.debug(f"清理挂起任务时出错: {e}")
                    finally:
                        loop.close()
                    
            except Exception as e:
                logger.error(f"全量更新失败: {e}")
                manager.finish_analysis(analysis_id)
        
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
                    # 🔥 新的增量更新逻辑：搜索->更新文件->重新分析
                    updated_items = loop.run_until_complete(self._run_incremental_analysis())
                    
                    if updated_items:
                        # 🔥 直接使用重新分析的结果，不需要合并
                        self.current_diff_items = updated_items
                        
                        # 保存当前数据到文件
                        self._save_current_data()
                        
                        # 更新全局缓存
                        manager.finish_analysis(analysis_id, updated_items)
                        
                        logger.info(f"✅ 增量更新完成: 基于最新数据分析出 {len(updated_items)} 个符合条件的商品")
                    else:
                        logger.info("📭 增量更新未发现符合条件的商品")
                        manager.finish_analysis(analysis_id, [])
                    
                    self.last_incremental_update = datetime.now()
                        
                finally:
                    # 🔥 优化：确保所有异步资源都被清理
                    try:
                        # 等待所有挂起的任务完成
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            logger.debug(f"等待 {len(pending)} 个挂起的任务完成...")
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception as e:
                        logger.debug(f"清理挂起任务时出错: {e}")
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
        """运行真正的增量分析：根据HashName缓存搜索最新数据并更新全量文件"""
        hashnames = self.hashname_cache.get_hashnames_for_search()
        if not hashnames:
            logger.warning("📭 HashName缓存为空，无法进行增量更新")
            return []
        
        logger.info(f"🔍 开始增量更新: 搜索 {len(hashnames)} 个商品的最新价格")
        
        # 🔥 第一步：根据HashName缓存搜索最新数据
        updated_items = []
        search_results = {'buff': [], 'youpin': []}
        
        async with SearchManager() as search_manager:
            # 限制并发搜索数量
            semaphore = asyncio.Semaphore(3)  # 降低并发数，避免API限制
            
            async def search_and_collect(keyword):
                async with semaphore:
                    try:
                        # 搜索两个平台获取最新数据
                        logger.info(f"🔍 开始搜索关键词: {keyword}")
                        results = await search_manager.search_both_platforms(keyword)
                        
                        # 🔥 修改：显示价格而不是数量
                        buff_results = results.get('buff', [])
                        youpin_results = results.get('youpin', [])
                        
                        # 获取最低价格
                        buff_price = f"¥{min(item.price for item in buff_results):.2f}" if buff_results else "无"
                        youpin_price = f"¥{min(item.price for item in youpin_results):.2f}" if youpin_results else "无"
                        
                        logger.info(f"🔍 搜索结果 '{keyword}': Buff={buff_price}, 悠悠有品={youpin_price}")
                        
                        # 🔥 如果悠悠有品搜索无结果，输出更详细的调试信息
                        if not youpin_results:
                            logger.warning(f"⚠️ 悠悠有品搜索无结果: {keyword}")
                            logger.info(f"   📊 悠悠有品原始响应数据: {results.get('youpin', [])}")
                            
                            # 检查是否是API错误还是真的没有数据
                            if isinstance(results.get('youpin'), list):
                                logger.info(f"   ✅ 悠悠有品API调用成功，但商品列表为空")
                            else:
                                logger.error(f"   ❌ 悠悠有品API调用可能失败")
                        
                        # 如果某个平台搜索结果为0，记录警告
                        if not buff_results:
                            logger.warning(f"⚠️ Buff搜索无结果: {keyword}")
                            logger.info(f"   📊 Buff原始响应数据: {results.get('buff', [])}")
                        
                        return keyword, results
                        
                    except Exception as e:
                        logger.error(f"🔍 增量搜索失败 {keyword}: {e}")
                        return keyword, {'buff': [], 'youpin': []}
            
            # 批量处理，避免过多并发
            batch_size = 5  # 减小批次大小
            total_updated = 0
            
            for i in range(0, len(hashnames), batch_size):
                batch_keywords = hashnames[i:i + batch_size]
                
                tasks = [search_and_collect(keyword) for keyword in batch_keywords]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 收集搜索结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"批量搜索异常: {result}")
                        continue
                        
                    keyword, results = result
                    if results:
                        # 合并搜索结果
                        search_results['buff'].extend(results.get('buff', []))
                        search_results['youpin'].extend(results.get('youpin', []))
                        total_updated += len(results.get('buff', [])) + len(results.get('youpin', []))
                
                # 进度报告
                logger.info(f"🔄 增量搜索进度: {min(i + batch_size, len(hashnames))}/{len(hashnames)}")
                
                # 批次间延迟，避免API限制
                await asyncio.sleep(2)
        
        logger.info(f"📊 增量搜索完成: 获取到 {len(search_results['buff'])} 个Buff商品, {len(search_results['youpin'])} 个悠悠有品商品")
        
        # 🔥 第二步：更新全量数据文件
        if search_results['buff'] or search_results['youpin']:
            updated_count = await self._update_full_data_files(search_results)
            logger.info(f"📁 全量数据文件更新完成: {updated_count} 个商品已更新")
        
        # 🔥 第三步：重新分析价差
        from saved_data_processor import get_saved_data_processor
        processor = get_saved_data_processor()
        
        if processor.has_valid_full_data():
            logger.info("🔄 基于更新后的全量数据重新分析价差...")
            diff_items, stats = processor.reprocess_with_current_filters()
            
            if diff_items:
                # 🔥 第四步：更新HashName缓存
                self.hashname_cache.update_from_full_analysis(diff_items)
                logger.info(f"🎯 增量更新完成: 分析出 {len(diff_items)} 个符合条件的商品")
                return diff_items
            else:
                logger.warning("⚠️ 重新分析后未发现符合条件的商品")
        else:
            logger.error("❌ 全量数据文件无效，无法重新分析")
        
        return []
        
    async def _update_full_data_files(self, search_results: Dict) -> int:
        """更新全量数据文件中对应商品的最新数据"""
        import os
        import json
        from typing import Dict, List
        
        updated_count = 0
        
        # 更新Buff数据文件
        buff_file = "data/buff_full.json"
        if os.path.exists(buff_file) and search_results.get('buff'):
            try:
                # 读取现有数据
                with open(buff_file, 'r', encoding='utf-8') as f:
                    buff_data = json.load(f)
                
                # 🔥 修复：创建新数据的索引，确保处理SearchResult对象
                new_buff_data = {}
                for item in search_results['buff']:
                    if hasattr(item, 'id') and item.id:
                        # 🔥 调试：尝试多种ID格式
                        item_id = str(item.id)
                        new_buff_data[item_id] = item
                        # 也添加数字格式的ID（如果可能）
                        try:
                            numeric_id = int(item_id)
                            new_buff_data[str(numeric_id)] = item
                        except ValueError:
                            pass
                
                logger.info(f"🔍 准备更新Buff数据: {len(search_results['buff'])} 个搜索结果")
                logger.debug(f"   搜索结果ID样例: {list(new_buff_data.keys())[:5]}")
                
                # 🔥 调试：检查全量数据结构
                if isinstance(buff_data, dict) and 'items' in buff_data:
                    items_to_check = buff_data['items']
                    logger.debug(f"   全量数据结构: dict with 'items' key, {len(items_to_check)} 个商品")
                elif isinstance(buff_data, list):
                    items_to_check = buff_data
                    logger.debug(f"   全量数据结构: list, {len(items_to_check)} 个商品")
                else:
                    logger.error(f"   ❌ 未知的全量数据结构: {type(buff_data)}")
                    items_to_check = []
                
                # 显示几个全量数据ID样例
                sample_ids = []
                for i, item in enumerate(items_to_check[:5]):
                    if isinstance(item, dict) and 'id' in item:
                        sample_ids.append(str(item['id']))
                logger.debug(f"   全量数据ID样例: {sample_ids}")
                
                # 更新现有数据
                items_updated = 0
                checked_count = 0
                for i, item in enumerate(items_to_check):
                    if isinstance(item, dict):  # 确保item是字典
                        item_id = str(item.get('id', ''))  # 转换为字符串进行匹配
                        checked_count += 1
                        
                        if item_id in new_buff_data:
                            new_item = new_buff_data[item_id]
                            # 更新关键字段
                            old_price = item.get('sell_min_price', item.get('price', 0))
                            item['sell_min_price'] = float(new_item.price)  # 🔥 使用正确的字段名
                            if hasattr(new_item, 'sell_num') and new_item.sell_num is not None:
                                item['sell_num'] = int(new_item.sell_num)
                            item['last_updated'] = datetime.now().isoformat()
                            items_updated += 1
                            logger.debug(f"✅ 更新商品ID {item_id}: {item.get('name', 'Unknown')} - 价格: {old_price} -> {new_item.price}")
                        elif checked_count <= 10:  # 只显示前10个未匹配的ID
                            logger.debug(f"❌ ID {item_id} 未在搜索结果中找到匹配")
                
                logger.info(f"🔍 ID匹配统计: 检查了 {checked_count} 个全量商品, 匹配到 {items_updated} 个")
                
                # 保存更新后的数据
                with open(buff_file, 'w', encoding='utf-8') as f:
                    json.dump(buff_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"📁 Buff数据文件已更新: {items_updated} 个商品")
                updated_count += items_updated
                
            except Exception as e:
                logger.error(f"❌ 更新Buff数据文件失败: {e}")
                logger.exception("详细错误信息:")
        
        # 更新悠悠有品数据文件
        youpin_file = "data/youpin_full.json"
        if os.path.exists(youpin_file) and search_results.get('youpin'):
            try:
                # 读取现有数据
                with open(youpin_file, 'r', encoding='utf-8') as f:
                    youpin_data = json.load(f)
                
                # 🔥 修复：创建新数据的索引 (使用name作为键，因为悠悠有品可能没有id)
                new_youpin_data = {}
                for item in search_results['youpin']:
                    if hasattr(item, 'id') and item.id:
                        key = str(item.id)
                        new_youpin_data[key] = item
                    if hasattr(item, 'name') and item.name:
                        # 也用name作为键
                        new_youpin_data[item.name] = item
                
                logger.info(f"🔍 准备更新悠悠有品数据: {len(search_results['youpin'])} 个搜索结果")
                logger.debug(f"   悠悠有品搜索结果键样例: {list(new_youpin_data.keys())[:5]}")
                
                # 🔥 调试：检查全量数据结构
                if isinstance(youpin_data, dict) and 'items' in youpin_data:
                    items_to_check = youpin_data['items']
                elif isinstance(youpin_data, list):
                    items_to_check = youpin_data
                else:
                    logger.error(f"   ❌ 未知的悠悠有品数据结构: {type(youpin_data)}")
                    items_to_check = []
                
                # 更新现有数据
                items_updated = 0
                checked_count = 0
                for i, item in enumerate(items_to_check):
                    if isinstance(item, dict):  # 确保item是字典
                        checked_count += 1
                        # 尝试用id匹配，如果没有id则用name匹配
                        item_key = str(item.get('id', '')) if item.get('id') else item.get('name', '')
                        if item_key and item_key in new_youpin_data:
                            new_item = new_youpin_data[item_key]
                            # 更新关键字段
                            old_price = item.get('price', 0)
                            item['price'] = float(new_item.price)
                            item['last_updated'] = datetime.now().isoformat()
                            items_updated += 1
                            logger.debug(f"✅ 更新悠悠有品商品 {item_key}: {item.get('name', 'Unknown')} - 价格: {old_price} -> {new_item.price}")
                        elif checked_count <= 10:  # 只显示前10个未匹配的
                            logger.debug(f"❌ 悠悠有品键 {item_key} 未找到匹配")
                
                logger.info(f"🔍 悠悠有品匹配统计: 检查了 {checked_count} 个全量商品, 匹配到 {items_updated} 个")
                
                # 保存更新后的数据
                with open(youpin_file, 'w', encoding='utf-8') as f:
                    json.dump(youpin_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"📁 悠悠有品数据文件已更新: {items_updated} 个商品")
                updated_count += items_updated
                
            except Exception as e:
                logger.error(f"❌ 更新悠悠有品数据文件失败: {e}")
                logger.exception("详细错误信息:")
        
        return updated_count
    
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
                    
                    # 🔥 修复：提取hash_name，优先从buff_item获取
                    hash_name = getattr(buff_item, 'hash_name', None) or getattr(buff_item, 'market_hash_name', None) or buff_item.name
                    
                    diff_item = PriceDiffItem(
                        id=buff_item.id,
                        name=buff_item.name,
                        hash_name=hash_name,  # 🔥 新增hash_name字段
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
            'cached_hashnames_count': len(self.hashname_cache.hashname_profits),
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
                            hash_name=item_data.get('hash_name', item_data.get('name', '')),  # 🔥 新增hash_name字段，兼容旧数据
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
                    'hash_name': getattr(item, 'hash_name', item.name),  # 🔥 新增hash_name字段，兼容旧数据
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

    def _regenerate_cache_from_full_data(self) -> bool:
        """
        从full data文件重新生成hash name缓存
        
        Returns:
            bool: 是否成功重新生成缓存
        """
        try:
            import os
            import json
            
            buff_file = "data/buff_full.json"
            youpin_file = "data/youpin_full.json"
            
            # 检查文件是否存在
            if not os.path.exists(buff_file) or not os.path.exists(youpin_file):
                logger.info("🔍 未找到full data文件，跳过缓存重新生成")
                return False
            
            logger.info("🔍 发现full data文件，开始重新生成hash name缓存...")
            
            # 读取数据文件
            with open(buff_file, 'r', encoding='utf-8') as f:
                buff_data = json.load(f)
            
            with open(youpin_file, 'r', encoding='utf-8') as f:
                youpin_data = json.load(f)
            
            buff_items = buff_data.get('items', [])
            youpin_items = youpin_data.get('items', [])
            
            logger.info(f"📂 加载数据: Buff {len(buff_items)}个商品, 悠悠有品 {len(youpin_items)}个商品")
            
            # 使用saved_data_processor进行快速分析
            from saved_data_processor import get_saved_data_processor
            processor = get_saved_data_processor()
            
            # 分析并筛选有价差的商品
            diff_items, stats = processor._analyze_with_current_filters(buff_items, youpin_items)
            
            if diff_items:
                logger.info(f"🎯 分析完成: 发现 {len(diff_items)} 个有价差的商品")
                
                # 更新缓存和当前数据
                self.hashname_cache.update_from_full_analysis(diff_items)
                self.current_diff_items = diff_items
                self._save_current_data()
                
                # 更新时间戳
                self.last_full_update = datetime.now()
                
                logger.info("✅ HashName缓存已从full data文件重新生成")
                return True
            else:
                logger.warning("⚠️ 未发现有价差的商品，无法生成缓存")
                return False
                
        except Exception as e:
            logger.error(f"❌ 从full data文件重新生成缓存失败: {e}")
            import traceback
            traceback.print_exc()
            return False

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