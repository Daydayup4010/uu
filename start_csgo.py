#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CS饰品差价监控项目启动脚本 - 用于2333tv.top/csgo部署
"""

import os
import sys
from flask import Flask, Blueprint

def main():
    print("🚀 启动CS饰品差价监控系统（/csgo路径部署）...")
    
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    print("📁 日志目录已创建")
    
    # 🔥 第一步：配置日志
    try:
        from log_config import quick_setup
        logger = quick_setup('INFO')
        logger.info("🚀 CS饰品差价监控系统启动 - 日志配置已启用")
        logger.info(f"📁 日志文件将保存到: {os.path.abspath('logs')} 目录")
        print("✅ 日志配置已启用")
    except ImportError as e:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ 日志配置模块加载失败: {e}，使用默认配置")
    
    try:
        # 创建新的Flask应用
        app = Flask(__name__)
        
        # 🔥 导入原有的API模块
        import api
        
        # 创建蓝图，添加URL前缀
        csgo_bp = Blueprint('csgo', __name__, 
                           url_prefix='/csgo',
                           static_folder='static', 
                           static_url_path='/csgo/static',
                           template_folder='templates')
        
        # 🔥 将原有的路由注册到蓝图
        # 主页路由
        @csgo_bp.route('/')
        def index():
            return api.index()
        
        # API路由
        @csgo_bp.route('/api/status')
        def api_status():
            return api.api_status()
            
        @csgo_bp.route('/api/data')
        def api_data():
            return api.api_data()
            
        @csgo_bp.route('/api/items')
        def api_items():
            return api.api_items()
            
        @csgo_bp.route('/api/force_update', methods=['POST'])
        def api_force_update():
            return api.api_force_update()
            
        @csgo_bp.route('/api/validate_data', methods=['GET'])
        def api_validate_data():
            return api.api_validate_data()
            
        @csgo_bp.route('/api/settings', methods=['GET', 'POST'])
        def api_settings():
            return api.api_settings()
            
        @csgo_bp.route('/api/price_range', methods=['GET', 'POST'])
        def api_price_range():
            return api.api_price_range()
            
        @csgo_bp.route('/api/buff_price_range', methods=['GET', 'POST'])
        def api_buff_price_range():
            return api.api_buff_price_range()
            
        @csgo_bp.route('/api/buff_sell_num', methods=['GET', 'POST'])
        def api_buff_sell_num():
            return api.api_buff_sell_num()
            
        @csgo_bp.route('/api/force_incremental_update', methods=['POST'])
        def api_force_incremental_update():
            return api.api_force_incremental_update()
            
        @csgo_bp.route('/api/enhanced_incremental_update', methods=['POST'])
        def api_enhanced_incremental_update():
            return api.api_enhanced_incremental_update()
            
        @csgo_bp.route('/api/incremental_update_status', methods=['GET'])
        def api_incremental_update_status():
            return api.api_get_incremental_update_status()
            
        @csgo_bp.route('/api/clear_cache', methods=['POST'])
        def api_clear_cache():
            return api.api_clear_cache()
            
        @csgo_bp.route('/api/analyze', methods=['POST'])
        def api_analyze():
            return api.api_analyze()
            
        @csgo_bp.route('/api/tokens/status', methods=['GET'])
        def api_tokens_status():
            return api.get_tokens_status()
            
        @csgo_bp.route('/api/tokens/buff', methods=['GET', 'POST'])
        def api_tokens_buff():
            return api.manage_buff_token()
            
        @csgo_bp.route('/api/tokens/youpin', methods=['GET', 'POST'])
        def api_tokens_youpin():
            return api.manage_youpin_token()
            
        @csgo_bp.route('/api/test/buff', methods=['POST'])
        def api_test_buff():
            return api.test_buff_connection()
            
        @csgo_bp.route('/api/test/youpin', methods=['POST'])
        def api_test_youpin():
            return api.test_youpin_connection()
            
        @csgo_bp.route('/api/stream_analyze', methods=['POST'])
        def api_stream_analyze():
            return api.api_stream_analyze()
            
        @csgo_bp.route('/api/analyze_incremental', methods=['POST'])
        def api_analyze_incremental():
            return api.api_analyze_incremental()
            
        @csgo_bp.route('/api/reprocess_from_saved', methods=['POST'])
        def api_reprocess_from_saved():
            return api.api_reprocess_from_saved()
            
        @csgo_bp.route('/demo')
        def demo():
            return api.streaming_demo()
        
        # 🔥 添加缺少的Token验证API路由
        @csgo_bp.route('/api/tokens/validate', methods=['POST'])
        def api_tokens_validate():
            return api.validate_tokens()
            
        @csgo_bp.route('/api/tokens/validate/buff', methods=['POST'])
        def api_tokens_validate_buff():
            return api.validate_buff_token()
            
        @csgo_bp.route('/api/tokens/validate/youpin', methods=['POST'])
        def api_tokens_validate_youpin():
            return api.validate_youpin_token()
            
        @csgo_bp.route('/api/tokens/alerts', methods=['GET'])
        def api_tokens_alerts():
            return api.get_token_alerts()
            
        @csgo_bp.route('/api/tokens/alerts/clear', methods=['POST'])
        def api_tokens_alerts_clear():
            return api.clear_token_notifications()
            
        @csgo_bp.route('/api/tokens/validation-service', methods=['GET', 'POST'])
        def api_tokens_validation_service():
            return api.manage_validation_service()
            
        # 🔥 新增：Token配置重载API路由
        @csgo_bp.route('/api/tokens/reload', methods=['POST'])
        def api_tokens_reload():
            return api.reload_token_config()
        
        # 注册蓝图
        app.register_blueprint(csgo_bp)
        
        # 添加CORS支持
        @app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
        
        # 健康检查路由（不需要前缀）
        @app.route('/health')
        def health_check():
            from flask import jsonify
            return jsonify({'status': 'ok', 'service': 'csgo-monitor'})
        
        # 启动更新管理器
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
        print("🎯 CS饰品差价监控系统已启动")
        print("="*60)
        print("📊 功能特性:")
        print("   ✅ 自动价差分析")
        print("   ✅ 增量和全量更新")
        print("   ✅ 实时价格监控") 
        print("   ✅ 增强增量更新（价格同步）")
        print("   ✅ 完整日志记录")
        print()
        print(f"🌐 本地测试: http://localhost:5000/csgo")
        print(f"🌐 线上地址: https://www.2333tv.top/csgo")
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