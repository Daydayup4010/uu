#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的获取速度

验证并行获取、大page_size和重试机制的效果
"""

import asyncio
import time
from integrated_price_system import IntegratedPriceAnalyzer

async def test_optimization():
    """测试优化效果"""
    print("🚀 测试优化后的价差分析系统")
    print("="*80)
    
    print("\n📊 优化内容:")
    print("1. 悠悠有品 page_size: 20 → 100")
    print("2. 两平台数据获取: 串行 → 并行")
    print("3. 等待机制: 固定延迟 → 重试机制")
    print("4. Buff API: 添加重试机制")
    
    async with IntegratedPriceAnalyzer(price_diff_threshold=5.0) as analyzer:
        print(f"\n🎯 开始快速测试（20个商品）...")
        start_time = time.time()
        
        # 分析价差
        diff_items = await analyzer.analyze_price_differences(max_items=20)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n⚡ 测试完成！")
        print(f"📊 性能统计:")
        print(f"   总耗时: {total_time:.2f} 秒")
        print(f"   处理商品: 20 个")
        print(f"   平均每商品: {total_time/20:.2f} 秒")
        print(f"   发现价差商品: {len(diff_items)} 个")
        
        if diff_items:
            print(f"\n🎯 发现的价差商品:")
            for i, item in enumerate(diff_items[:5], 1):
                print(f"   #{i}: {item.name}")
                print(f"      价差: ¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
        
        # 性能评估
        if total_time < 30:
            print(f"\n✅ 性能评级: 优秀 (< 30秒)")
        elif total_time < 60:
            print(f"\n✅ 性能评级: 良好 (< 60秒)")
        elif total_time < 120:
            print(f"\n⚠️ 性能评级: 一般 (< 120秒)")
        else:
            print(f"\n❌ 性能评级: 需要进一步优化 (> 120秒)")

async def test_parallel_vs_serial():
    """对比并行vs串行获取速度"""
    print("\n🏁 对比并行 vs 串行获取速度")
    print("="*50)
    
    async with IntegratedPriceAnalyzer() as analyzer:
        # 测试并行获取
        print("📊 测试并行获取...")
        start_time = time.time()
        
        buff_task = asyncio.create_task(analyzer.buff_client.get_all_goods())
        youpin_task = asyncio.create_task(analyzer.youpin_client.get_all_items())
        
        buff_data, youpin_items = await asyncio.gather(buff_task, youpin_task, return_exceptions=True)
        
        parallel_time = time.time() - start_time
        
        # 获取基本统计
        buff_count = len(buff_data) if buff_data and not isinstance(buff_data, Exception) else 0
        youpin_count = len(youpin_items) if youpin_items and not isinstance(youpin_items, Exception) else 0
        
        print(f"⚡ 并行获取结果:")
        print(f"   耗时: {parallel_time:.2f} 秒")
        print(f"   Buff商品: {buff_count} 个")
        print(f"   悠悠有品商品: {youpin_count} 个")
        print(f"   总商品: {buff_count + youpin_count} 个")
        
        if buff_count + youpin_count > 0:
            efficiency = (buff_count + youpin_count) / parallel_time
            print(f"   获取效率: {efficiency:.1f} 商品/秒")

async def main():
    """主函数"""
    try:
        # 基本优化测试
        await test_optimization()
        
        # 并行vs串行对比
        await test_parallel_vs_serial()
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 启动优化测试...")
    asyncio.run(main()) 