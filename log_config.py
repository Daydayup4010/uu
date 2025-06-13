#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块 - 单例模式防止重复配置

配置日志同时输出到控制台和文件，全局只配置一次
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional

class LogConfig:
    """日志配置单例类"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not LogConfig._initialized:
            self.logger = None
            self.log_level = "INFO"
            self.log_dir = "logs"
            self.app_name = "buff_monitor"
            LogConfig._initialized = True
    
    def setup(
        self,
        log_level: str = "INFO",
        log_dir: str = "logs",
        app_name: str = "buff_monitor",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_output: bool = True
    ) -> logging.Logger:
        """
        配置日志系统（单例模式，只配置一次）
        """
        # 如果已经配置过，直接返回
        if self.logger is not None:
            return self.logger
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 🔥 彻底清除所有现有配置
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
        
        # 清除所有日志器的配置
        for name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()
        
        # 创建主日志器
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.propagate = False  # 重要：不向上传播
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 1. 文件处理器 - 轮转日志
        today = datetime.now().strftime('%Y%m%d')
        log_filename = os.path.join(log_dir, f"{app_name}_{today}.log")
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_filename,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 2. 错误日志单独文件
        error_log_filename = os.path.join(log_dir, f"{app_name}_error_{today}.log")
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_filename,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # 3. 控制台处理器（如果启用）
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 🔥 配置根日志器，让其他模块的日志也能正常输出
        root_logger.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)
        if console_output:
            root_logger.addHandler(console_handler)
        
        # 设置实例变量
        self.log_level = log_level
        self.log_dir = log_dir
        self.app_name = app_name
        
        self.logger.info(f"✅ 日志系统已配置")
        self.logger.info(f"   - 日志级别: {log_level}")
        self.logger.info(f"   - 日志文件: {log_filename}")
        self.logger.info(f"   - 错误日志: {error_log_filename}")
        self.logger.info(f"   - 控制台输出: {'启用' if console_output else '禁用'}")
        
        return self.logger
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """获取日志器"""
        if self.logger is None:
            # 如果还没有配置，先配置
            self.setup()
        
        if name is None or name == self.app_name:
            return self.logger
        
        # 为其他模块创建子日志器
        child_logger = logging.getLogger(name)
        child_logger.setLevel(getattr(logging, self.log_level.upper()))
        child_logger.propagate = True  # 让子日志器向父级传播
        
        return child_logger
    
    def is_configured(self) -> bool:
        """检查是否已经配置"""
        return self.logger is not None

# 全局实例
_log_config = LogConfig()

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "buff_monitor",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """配置日志系统（全局单例）"""
    return _log_config.setup(
        log_level=log_level,
        log_dir=log_dir,
        app_name=app_name,
        max_file_size=max_file_size,
        backup_count=backup_count,
        console_output=console_output
    )

def get_logger(name: str = None) -> logging.Logger:
    """获取日志器"""
    return _log_config.get_logger(name)

def quick_setup(level: str = "INFO") -> logging.Logger:
    """快速配置日志系统"""
    return _log_config.setup(log_level=level)

def is_logging_configured() -> bool:
    """检查日志系统是否已经配置"""
    return _log_config.is_configured()

if __name__ == "__main__":
    # 测试日志配置
    logger = quick_setup("DEBUG")
    
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")
    
    print("✅ 日志测试完成，请检查 logs 目录") 