#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局分析管理器 - 防止多个分析进程同时运行
"""

import asyncio
import threading
import time
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AnalysisManager:
    """全局分析管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.is_running = False
        self.current_analysis_type = None
        self.current_analysis_id = None
        self.start_time = None
        self.stop_requested = False
        
        # 线程锁，确保状态操作的原子性
        self.state_lock = threading.Lock()
        
        # 分析结果缓存
        self.last_results = []
        self.last_update_time = None
        
    def start_analysis(self, analysis_type: str, analysis_id: str = None, force: bool = True) -> bool:
        """
        启动分析，如果已有分析在运行则根据force参数决定是否继续
        
        Args:
            analysis_type: 分析类型 ('streaming', 'integrated', 'monitor')
            analysis_id: 分析ID（可选）
            force: 是否强制启动，True=阻塞式启动，False=非阻塞式启动
            
        Returns:
            bool: 是否成功启动
        """
        with self.state_lock:
            if self.is_running:
                if force:
                    logger.warning(f"强制停止当前分析: {self.current_analysis_type} (ID: {self.current_analysis_id})")
                    # 强制停止当前分析
                    self.stop_requested = True
                    self.is_running = False
                else:
                    logger.debug(f"已有分析在运行，跳过非阻塞启动: {self.current_analysis_type} (ID: {self.current_analysis_id})")
                    return False
            
            self.is_running = True
            self.current_analysis_type = analysis_type
            self.current_analysis_id = analysis_id or f"{analysis_type}_{int(time.time())}"
            self.start_time = datetime.now()
            self.stop_requested = False
            
            logger.info(f"🚀 启动分析: {analysis_type} (ID: {self.current_analysis_id})")
            return True
    
    def stop_analysis(self, analysis_id: str = None) -> bool:
        """
        停止分析
        
        Args:
            analysis_id: 分析ID，如果提供且不匹配当前分析则不停止
            
        Returns:
            bool: 是否成功停止
        """
        with self.state_lock:
            if not self.is_running:
                return False
                
            if analysis_id and analysis_id != self.current_analysis_id:
                logger.warning(f"分析ID不匹配: 请求停止 {analysis_id}, 当前运行 {self.current_analysis_id}")
                return False
            
            logger.info(f"⏹️ 停止分析: {self.current_analysis_type} (ID: {self.current_analysis_id})")
            
            self.stop_requested = True
            return True
    
    def finish_analysis(self, analysis_id: str = None, results: list = None):
        """
        完成分析
        
        Args:
            analysis_id: 分析ID
            results: 分析结果
        """
        with self.state_lock:
            if analysis_id and analysis_id != self.current_analysis_id:
                logger.warning(f"分析ID不匹配: 完成 {analysis_id}, 当前运行 {self.current_analysis_id}")
                return
            
            duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            
            logger.info(f"✅ 完成分析: {self.current_analysis_type} (ID: {self.current_analysis_id}), 耗时: {duration:.1f}秒")
            
            # 更新结果缓存
            if results:
                self.last_results = results
                self.last_update_time = datetime.now()
            
            # 重置状态
            self.is_running = False
            self.current_analysis_type = None
            self.current_analysis_id = None
            self.start_time = None
            self.stop_requested = False
    
    def should_stop(self) -> bool:
        """检查是否应该停止当前分析"""
        with self.state_lock:
            return self.stop_requested
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        with self.state_lock:
            return {
                'is_running': self.is_running,
                'analysis_type': self.current_analysis_type,
                'analysis_id': self.current_analysis_id,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'duration': (datetime.now() - self.start_time).total_seconds() if self.start_time else None,
                'last_results_count': len(self.last_results) if self.last_results else 0,
                'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None
            }
    
    def get_cached_results(self) -> list:
        """获取缓存的分析结果"""
        with self.state_lock:
            return self.last_results.copy() if self.last_results else []
    
    def force_stop_all(self):
        """强制停止所有分析"""
        with self.state_lock:
            if self.is_running:
                logger.warning(f"🛑 强制停止分析: {self.current_analysis_type} (ID: {self.current_analysis_id})")
                
            self.is_running = False
            self.current_analysis_type = None
            self.current_analysis_id = None
            self.start_time = None
            self.stop_requested = True

# 全局分析管理器实例
analysis_manager = AnalysisManager()

def get_analysis_manager() -> AnalysisManager:
    """获取全局分析管理器实例"""
    return analysis_manager 