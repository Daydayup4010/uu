#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版演示启动脚本

避免复杂的异步和监控问题，直接启动Web服务并生成演示数据
"""

import os
import sys
import logging
import socket
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_free_port():
    """查找一个空闲端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def setup_environment():
    """设置环境"""
    logger.info("设置项目环境...")
    
    # 创建必要目录
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 创建环境配置文件
    env_path = '.env'
    if not os.path.exists(env_path):
        env_content = """# Buff差价监控系统配置
PRICE_DIFF_THRESHOLD=10.0
MONITOR_INTERVAL=300
BUFF_BASE_URL=https://buff.163.com
YOUPIN_BASE_URL=https://www.youpin898.com
MAX_RETRIES=3
DEBUG=true
"""
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        logger.info("已创建 .env 配置文件")

def generate_demo_data():
    """生成演示数据"""
    try:
        logger.info("生成演示数据...")
        from demo_data import save_demo_data
        save_demo_data()
        logger.info("演示数据生成完成")
    except Exception as e:
        logger.error(f"生成演示数据失败: {e}")

def start_web_server():
    """启动Web服务器"""
    logger.info("启动Web服务器...")
    
    try:
        import uvicorn
        from api_simple import app
        
        # 首先尝试默认端口8000，如果被占用则使用动态端口
        port = 8000
        try:
            # 测试端口是否可用
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind(('127.0.0.1', port))
            test_socket.close()
        except OSError:
            # 端口被占用，查找空闲端口
            port = find_free_port()
            logger.info(f"端口8000被占用，使用端口 {port}")
        
        print("\n" + "="*50)
        print("🚀 Buff差价饰品监控系统已启动！")
        print(f"🌐 访问地址: http://localhost:{port}")
        print("📊 查看演示数据和价差分析")
        print("⌨️  按 Ctrl+C 停止服务")
        print("="*50 + "\n")
        
        # 启动服务器
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 系统已停止，感谢使用！")
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")

def main():
    """主函数"""
    try:
        # 1. 设置环境
        setup_environment()
        
        # 2. 生成演示数据
        generate_demo_data()
        
        # 3. 启动Web服务器
        start_web_server()
        
    except Exception as e:
        logger.error(f"启动失败: {e}")

if __name__ == "__main__":
    main() 