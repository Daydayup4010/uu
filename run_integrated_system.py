#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成真实悠悠有品API的启动脚本

使用真实的Buff API和悠悠有品API进行价差分析
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

async def generate_integrated_data(count: int = 10, max_items: int = 50):
    """生成集成API数据"""
    try:
        logger.info(f"开始使用真实API进行价差分析（最多{max_items}个商品）...")
        from integrated_price_system import IntegratedPriceAnalyzer, save_price_diff_data
        
        async with IntegratedPriceAnalyzer(price_diff_threshold=5.0) as analyzer:
            if count <= 10:
                # 快速测试模式
                diff_items = await analyzer.quick_analysis(count=count)
            else:
                # 完整分析模式
                diff_items = await analyzer.analyze_price_differences(max_items=max_items)
        
        if diff_items:
            # 保存数据到系统可识别的位置
            filename = save_price_diff_data(diff_items, "data/api_sample_data.json")
            logger.info(f"成功生成 {len(diff_items)} 个有价差的商品")
            
            # 同时保存为带时间戳的备份
            timestamp_filename = save_price_diff_data(diff_items)
            
            return True
        else:
            logger.warning("未发现有价差的商品")
            return False
            
    except Exception as e:
        logger.error(f"集成API数据生成失败: {e}")
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
        print("🎯 Buff vs 悠悠有品真实价差分析系统")
        print("="*60)
        print("🚀 系统特性:")
        print("   ✅ 使用Buff官方API获取真实价格")
        print("   ✅ 使用悠悠有品真实API获取真实价格")
        print("   ✅ 实时价差分析和利润率计算")
        print("   ✅ 自动跳转购买链接")
        print("   ✅ 现代化Web界面")
        print()
        print(f"🌐 访问地址: http://localhost:{port}")
        print("📊 查看真实的Buff vs 悠悠有品价差数据")
        print("🔗 点击商品链接直接跳转到购买页面")
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
    print("🎯 Buff vs 悠悠有品真实价差分析系统")
    print("="*60)
    
    if args.test:
        print("📡 模式: 快速测试（5个商品）")
    elif args.full:
        print(f"📡 模式: 完整分析（最多{args.max_items}个商品）")
        print("⚠️  注意: 这可能需要较长时间，因为每个商品都需要真实API查询")
    else:
        print(f"📡 模式: 标准分析（{args.count}个商品）")
    
    print("🔍 使用真实API:")
    print("   • Buff: 官方API获取真实最低价")
    print("   • 悠悠有品: 真实API获取真实最低价")
    print("="*60)
    
    # 1. 设置环境
    setup_environment()
    
    # 2. 生成数据
    if args.test:
        success = await generate_integrated_data(count=5, max_items=5)
    elif args.full:
        success = await generate_integrated_data(count=args.max_items, max_items=args.max_items)
    else:
        success = await generate_integrated_data(count=args.count, max_items=args.count)
    
    if not success:
        # 如果真实API数据生成失败，使用备用数据
        generate_backup_data()
    
    return success

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Buff vs 悠悠有品真实价差分析系统')
    parser.add_argument('--test', action='store_true', 
                       help='快速测试模式（5个商品）')
    parser.add_argument('--full', action='store_true', 
                       help='完整分析模式（需要较长时间）')
    parser.add_argument('--count', type=int, default=10,
                       help='标准模式下的商品数量（默认10）')
    parser.add_argument('--max-items', type=int, default=50,
                       help='完整模式下的最大商品数量（默认50）')
    
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