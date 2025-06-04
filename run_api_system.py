#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终启动脚本 - 使用API数据收集器

集成了基于API的数据收集功能，能够遍历所有Buff饰品
"""

import os
import sys
import logging
import socket
import asyncio
import argparse
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

async def generate_api_data(count: int = 100, get_all: bool = False, max_pages: int = None):
    """生成API数据"""
    try:
        if get_all:
            logger.info("开始获取所有Buff饰品数据（可能需要较长时间）...")
            from api_demo_data import generate_large_dataset
            # 获取所有数据，不限制页数
            diff_items = await generate_large_dataset(max_pages=None)
        elif max_pages:
            logger.info(f"开始获取前{max_pages}页的Buff饰品数据...")
            from api_demo_data import generate_large_dataset
            diff_items = await generate_large_dataset(max_pages=max_pages)
        else:
            logger.info(f"开始生成基于API的样本数据（{count}个商品）...")
            from api_demo_data import generate_api_demo_data
            diff_items = await generate_api_demo_data(count=count)
        
        if diff_items:
            logger.info(f"成功生成 {len(diff_items)} 个有价差的商品")
            return True
        else:
            logger.warning("API数据生成失败，将使用备用数据")
            return False
            
    except Exception as e:
        logger.error(f"生成API数据失败: {e}")
        return False

def generate_backup_data():
    """生成备用数据"""
    try:
        logger.info("生成备用演示数据...")
        from demo_data import save_demo_data
        save_demo_data()
        logger.info("备用数据生成完成")
        return True
    except Exception as e:
        logger.error(f"生成备用数据失败: {e}")
        return False

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
        
        print("\n" + "="*60)
        print("🎯 Buff差价饰品自动监控与跳转系统")
        print("="*60)
        print("🚀 系统特性:")
        print("   ✅ 基于API的真实数据收集")
        print("   ✅ 能够遍历所有Buff饰品")
        print("   ✅ 实时价差分析")
        print("   ✅ 自动跳转购买链接")
        print("   ✅ 现代化Web界面")
        print()
        print(f"🌐 访问地址: http://localhost:{port}")
        print("📊 查看真实的价差分析数据")
        print("🔗 点击商品链接直接跳转到Buff购买页面")
        print("⌨️  按 Ctrl+C 停止服务")
        print("="*60 + "\n")
        
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

async def prepare_data(args):
    """准备数据"""
    print("🎯 Buff差价饰品自动监控与跳转系统 - API版本")
    print("="*60)
    
    if args.all:
        print("📡 模式: 获取全部饰品数据（约24,000+个商品）")
        print("⚠️  注意: 这可能需要很长时间（30分钟到几小时）")
        print("💡 建议: 首次使用可以先用 --pages 10 获取前10页测试")
    elif args.pages:
        print(f"📡 模式: 获取前{args.pages}页数据（约{args.pages*100}个商品）")
    else:
        print(f"📡 模式: 样本数据（{args.count}个商品）")
    
    print("="*60)
    
    # 1. 设置环境
    setup_environment()
    
    # 2. 生成数据
    success = await generate_api_data(
        count=args.count, 
        get_all=args.all, 
        max_pages=args.pages
    )
    if not success:
        # 如果API数据生成失败，使用备用数据
        generate_backup_data()
    
    return success

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Buff差价饰品监控系统')
    parser.add_argument('--all', action='store_true', 
                       help='获取所有饰品数据（约24,000+个，需要很长时间）')
    parser.add_argument('--pages', type=int, 
                       help='获取指定页数的数据（每页约100个商品）')
    parser.add_argument('--count', type=int, default=100,
                       help='样本模式下的商品数量（默认100）')
    
    args = parser.parse_args()
    
    try:
        # 先在异步环境中准备数据
        asyncio.run(prepare_data(args))
        
        # 然后在同步环境中启动Web服务器
        start_web_server()
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}")

if __name__ == "__main__":
    main() 