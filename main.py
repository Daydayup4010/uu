#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主启动文件 - 确保日志配置正确应用

这个文件负责：
1. 初始化日志配置
2. 启动API服务器
3. 启动更新管理器
"""

import os
import sys

# 确保日志目录存在
os.makedirs('logs', exist_ok=True)

# 🔥 第一步：配置日志（在导入其他模块之前）
try:
    from log_config import quick_setup
    logger = quick_setup('INFO')
    logger.info("🚀 系统启动 - 日志配置已启用")
    logger.info(f"📁 日志文件将保存到: {os.path.abspath('logs')} 目录")
except ImportError as e:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ 日志配置模块加载失败: {e}，使用默认配置")

def start_system():
    """启动系统"""
    logger.info("🎯 启动Buff价差监控系统")
    
    try:
        # 导入并启动更新管理器
        logger.info("🔄 启动更新管理器...")
        from update_manager import get_update_manager
        
        update_manager = get_update_manager()
        update_manager.start()
        logger.info("✅ 更新管理器已启动")
        
        # 导入并启动API服务器
        logger.info("🌐 启动API服务器...")
        from api import app
        
        # 启动Flask服务器
        logger.info("🚀 API服务器启动在 http://localhost:5000")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("👋 系统被用户中断，正在关闭...")
    except Exception as e:
        logger.error(f"❌ 系统启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # 清理资源
        try:
            if 'update_manager' in locals():
                update_manager.stop()
                logger.info("✅ 更新管理器已停止")
        except Exception as e:
            logger.error(f"⚠️ 清理资源时出错: {e}")

if __name__ == "__main__":
    start_system() 