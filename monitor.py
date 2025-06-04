#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import schedule
import time
import logging
import json
from datetime import datetime, timedelta
from threading import Thread
from typing import List
from concurrent.futures import ThreadPoolExecutor
import functools

# 使用集成价格分析器，实现批量获取+内存匹配
from integrated_price_system import IntegratedPriceAnalyzer, PriceDiffItem, save_price_diff_data, load_price_diff_data
from config import Config

# 导入全局分析管理器
from analysis_manager import get_analysis_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceMonitor:
    """价格监控服务"""
    
    def __init__(self):
        # 使用集成价格分析器（批量获取+内存匹配）
        self.integrated_analyzer = IntegratedPriceAnalyzer(price_diff_threshold=Config.PRICE_DIFF_THRESHOLD)
        self.is_running = False
        self.last_update = None
        self.current_diff_items = []
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        """设置定时任务"""
        # 每5分钟检查一次
        schedule.every(5).minutes.do(self._run_monitor_cycle)
        
        # 每小时的整点执行完整监控
        schedule.every().hour.at(":00").do(self._run_full_monitor)
        
        logger.info("定时任务已设置：每5分钟检查一次，每小时完整监控一次")
    
    def start(self):
        """启动监控服务"""
        self.is_running = True
        logger.info("价格监控服务已启动")
        
        # 启动时执行一次完整监控
        self._run_full_monitor()
        
        # 启动定时任务线程
        monitor_thread = Thread(target=self._run_scheduler, daemon=True)
        monitor_thread.start()
        
        return monitor_thread
    
    def stop(self):
        """停止监控服务"""
        self.is_running = False
        self.executor.shutdown(wait=False)
        logger.info("价格监控服务已停止")
    
    def _run_scheduler(self):
        """运行定时任务调度器"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(10)  # 每10秒检查一次
    
    def _run_monitor_cycle(self):
        """运行监控周期（轻量级检查）"""
        if not self.is_running:
            return
        
        try:
            logger.info("开始监控周期检查...")
            
            # 加载现有数据并检查是否需要更新
            diff_items = self.load_diff_data()
            
            # 如果数据较新（1小时内），直接使用
            if self.last_update and (datetime.now() - self.last_update) < timedelta(hours=1):
                self.current_diff_items = diff_items
                logger.info(f"使用缓存数据，共 {len(diff_items)} 个差价饰品")
                return
            
            # 否则执行完整监控
            self._run_full_monitor()
            
        except Exception as e:
            logger.error(f"监控周期检查失败: {e}")
    
    def _run_full_monitor(self):
        """执行完整监控（包含数据采集和分析）"""
        if not self.is_running:
            return
        
        # 在独立线程中执行异步任务
        future = self.executor.submit(self._async_full_monitor)
    
    def _async_full_monitor(self):
        """在独立线程中执行异步完整监控 - 集成全局并发控制"""
        try:
            logger.info("开始完整监控周期...")
            start_time = datetime.now()
            
            # 获取全局分析管理器
            manager = get_analysis_manager()
            analysis_id = f"monitor_{int(start_time.timestamp())}"
            
            # 尝试启动监控分析
            if not manager.start_analysis('monitor', analysis_id):
                logger.info(f"监控跳过：已有分析在运行 ({manager.current_analysis_type})")
                # 使用缓存数据
                cached_results = manager.get_cached_results()
                if cached_results:
                    # 转换为PriceDiffItem对象
                    self.current_diff_items = [
                        PriceDiffItem(**item) if isinstance(item, dict) else item 
                        for item in cached_results
                    ]
                    self.last_update = datetime.now()
                    logger.info(f"使用缓存数据：{len(self.current_diff_items)}个商品")
                return
            
            try:
                # 创建新的事件循环（在独立线程中）
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # 使用集成分析器进行批量分析（批量获取+内存匹配）
                    logger.info("使用集成分析器进行批量价差分析...")
                    
                    # 在事件循环中运行异步代码
                    diff_items = loop.run_until_complete(self._run_integrated_analysis())
                    
                    if not diff_items:
                        logger.warning("未获取到任何价差饰品数据")
                        manager.finish_analysis(analysis_id, [])
                        return
                    
                    logger.info(f"集成分析完成，获得 {len(diff_items)} 个价差饰品")
                    
                    # 更新当前数据
                    self.current_diff_items = diff_items
                    self.last_update = datetime.now()
                    
                    # 保存数据
                    self.save_diff_data(diff_items)
                    
                    # 更新管理器缓存
                    manager.finish_analysis(analysis_id, diff_items)
                    
                    # 记录统计信息
                    if diff_items:
                        avg_diff = sum(item.price_diff for item in diff_items) / len(diff_items)
                        max_diff = max(item.price_diff for item in diff_items)
                        
                        logger.info(
                            f"监控周期完成：共找到 {len(diff_items)} 个差价饰品，"
                            f"平均价差 {avg_diff:.2f} 元，"
                            f"最大价差 {max_diff:.2f} 元"
                        )
                    
                    # 发送通知（如果有高价差饰品）
                    self._check_alerts(diff_items)
                    
                finally:
                    loop.close()
                
            except Exception as e:
                # 分析失败，清理管理器状态
                manager.finish_analysis(analysis_id)
                raise e
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"完整监控周期耗时: {duration:.2f} 秒")
            
        except Exception as e:
            logger.error(f"完整监控失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _run_integrated_analysis(self):
        """运行集成价差分析"""
        async with self.integrated_analyzer:
            # 分析价差（使用配置中的最大商品数量）
            return await self.integrated_analyzer.analyze_price_differences(max_output_items=Config.MONITOR_MAX_ITEMS)
    
    def _check_alerts(self, diff_items: List[PriceDiffItem]):
        """检查并发送高价差提醒"""
        high_diff_items = [
            item for item in diff_items 
            if item.price_diff >= Config.PRICE_DIFF_THRESHOLD * 2  # 双倍阈值触发提醒
        ]
        
        if high_diff_items:
            logger.info(f"发现 {len(high_diff_items)} 个高价差饰品（≥{Config.PRICE_DIFF_THRESHOLD * 2}元）")
            
            # 这里可以集成邮件、微信等通知方式
            for item in high_diff_items[:5]:  # 只显示前5个
                logger.info(
                    f"高价差提醒: {item.name} - "
                    f"价差: {item.price_diff:.2f}元 "
                    f"({item.profit_rate:.1f}%) "
                    f"链接: {item.buff_url}"
                )
    
    def save_diff_data(self, diff_items: List[PriceDiffItem]):
        """保存价差数据"""
        try:
            save_price_diff_data(diff_items, "data/latest_price_diff.json")
            logger.info(f"已保存 {len(diff_items)} 个价差商品数据")
        except Exception as e:
            logger.error(f"保存价差数据失败: {e}")
    
    def load_diff_data(self) -> List[PriceDiffItem]:
        """加载价差数据"""
        try:
            return load_price_diff_data("data/latest_price_diff.json")
        except Exception as e:
            logger.warning(f"加载价差数据失败: {e}")
            return []
    
    def get_current_data(self) -> List[PriceDiffItem]:
        """获取当前监控数据"""
        return self.current_diff_items
    
    def get_status(self) -> dict:
        """获取监控服务状态"""
        return {
            'is_running': self.is_running,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'current_items_count': len(self.current_diff_items),
            'threshold': Config.PRICE_DIFF_THRESHOLD,
            'next_run': self._get_next_run_time()
        }
    
    def _get_next_run_time(self) -> str:
        """获取下次运行时间"""
        try:
            next_run = schedule.next_run()
            return next_run.isoformat() if next_run else "未知"
        except:
            return "未知"
    
    def force_update(self):
        """强制立即更新数据"""
        logger.info("收到强制更新请求")
        self._run_full_monitor()
    
    def update_threshold(self, threshold: float):
        """更新价差阈值"""
        # 更新集成分析器的阈值
        self.integrated_analyzer.price_diff_threshold = threshold
        logger.info(f"价差阈值已更新为: {threshold}")
        
        # 重新分析现有数据
        if self.current_diff_items:
            # 重新加载原始数据并分析
            self.force_update()

# 全局监控实例
_monitor_instance = None

def get_monitor() -> PriceMonitor:
    """获取监控实例（单例模式）"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PriceMonitor()
    return _monitor_instance

def start_monitor():
    """启动监控服务"""  
    return get_monitor().start()

def stop_monitor():
    """停止监控服务"""
    return get_monitor().stop() 