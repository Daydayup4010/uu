#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CS:GO价差分析工具 - 主入口
支持命令行模式和Web服务模式
"""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 确保导入路径正确
sys.path.append(str(Path(__file__).parent))

# 导入主要模块
from integrated_price_system import IntegratedPriceAnalyzer, save_price_diff_data
from update_manager import get_update_manager
from api import app
from config import Config

def print_banner():
    """打印程序横幅"""
    print("=" * 80)
    print("          CS:GO 饰品价差分析系统 v2.0")
    print("          Buff vs 悠悠有品 价格对比")
    print("=" * 80)
    print()

async def run_analysis():
    """运行价差分析"""
    print_banner()
    print("🎯 开始价差分析...")
    
    async with IntegratedPriceAnalyzer(price_diff_threshold=Config.PRICE_DIFF_THRESHOLD) as analyzer:
        # 分析价差
        diff_items = await analyzer.analyze_price_differences(max_items=50)
        
        if diff_items:
            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/price_diff_analysis_{timestamp}.json"
            save_price_diff_data(diff_items, filename)
            
            # 显示结果摘要
            print(f"\n✅ 分析完成！发现 {len(diff_items)} 个有价差的商品")
            print(f"📁 结果已保存到: {filename}")
            
            if diff_items:
                avg_diff = sum(item.price_diff for item in diff_items) / len(diff_items)
                max_diff = max(item.price_diff for item in diff_items)
                print(f"📊 平均价差: ¥{avg_diff:.2f}")
                print(f"📊 最高价差: ¥{max_diff:.2f}")
                
                print(f"\n🔥 前5个最佳价差商品:")
                for i, item in enumerate(diff_items[:5], 1):
                    print(f"  {i}. {item.name}")
                    print(f"     Buff: ¥{item.buff_price} → 悠悠有品: ¥{item.youpin_price}")
                    print(f"     价差: ¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
                    print()
        else:
            print("❌ 未发现有价差的商品")

def run_web():
    """运行Web服务"""
    print_banner()
    print("🌐 启动Web服务...")
    
    # 启动更新管理器
    print("📊 启动数据更新管理器...")
    update_manager = get_update_manager()
    update_manager.start()
    
    # 启动Flask应用
    print("🚀 启动Web应用...")
    print(f"💻 访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        update_manager.stop()
        print("✅ 服务已停止")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py analyze  # 运行价差分析")
        print("  python main.py web      # 启动Web服务")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == 'analyze':
        asyncio.run(run_analysis())
    elif mode == 'web':
        run_web()
    else:
        print(f"❌ 未知模式: {mode}")
        print("支持的模式: analyze, web")

if __name__ == "__main__":
    main() 