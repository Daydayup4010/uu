#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API服务启动脚本 - 包含日志配置

使用方法：
python start_api.py
"""

import os
import sys

def main():
    print("🚀 启动Buff价差监控系统...")
    
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    print("📁 日志目录已创建")
    
    # 🔥 第一步：配置日志（在导入其他模块之前）
    try:
        from log_config import quick_setup
        logger = quick_setup('INFO')
        logger.info("🚀 系统启动 - 日志配置已启用")
        logger.info(f"📁 日志文件将保存到: {os.path.abspath('logs')} 目录")
        print("✅ 日志配置已启用，日志将保存到logs目录")
    except ImportError as e:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ 日志配置模块加载失败: {e}，使用默认配置")
        print(f"⚠️ 日志配置模块加载失败: {e}")
    
    try:
        # 导入API模块（这会触发日志配置）
        logger.info("🌐 导入API模块...")
        from api import app
        
        # 导入并启动更新管理器
        logger.info("🔄 启动更新管理器...")
        from update_manager import get_update_manager
        
        update_manager = get_update_manager()
        update_manager.start()
        logger.info("✅ 更新管理器已启动")
        
        # 启动Flask服务器
        print("🌐 启动API服务器在 http://localhost:5000")
        logger.info("🚀 API服务器启动在 http://localhost:5000")
        
        # 显示系统信息
        print("\n" + "="*60)
        print("🎯 Buff价差监控系统已启动")
        print("="*60)
        print("📊 功能特性:")
        print("   ✅ 自动价差分析")
        print("   ✅ 增量和全量更新")
        print("   ✅ 实时价格监控") 
        print("   ✅ 增强增量更新（价格同步）")
        print("   ✅ 完整日志记录")
        print()
        print(f"🌐 Web界面: http://localhost:5000")
        print(f"📁 日志目录: {os.path.abspath('logs')}")
        print("⌨️  按 Ctrl+C 停止服务")
        print("="*60 + "\n")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 系统被用户中断，正在关闭...")
        logger.info("👋 系统被用户中断，正在关闭...")
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
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
    main() 