#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大规模数据处理测试

验证增加商品数量限制后的系统性能
"""

import asyncio
import time
from config import Config
from integrated_price_system import IntegratedPriceAnalyzer

async def test_large_scale_processing():
    """测试大规模处理能力"""
    print("🎯 大规模数据处理测试")
    print("="*80)
    
    # 显示当前配置
    print(f"\n📊 当前处理配置:")
    limits = Config.get_processing_limits()
    for key, value in limits.items():
        print(f"   {key}: {value}")
    
    print(f"\n🚀 开始大规模价差分析...")
    start_time = time.time()
    
    async with IntegratedPriceAnalyzer(price_diff_threshold=5.0) as analyzer:
        # 使用默认配置进行分析
        diff_items = await analyzer.analyze_price_differences()
        
        analysis_time = time.time() - start_time
        
        print(f"\n✅ 大规模分析完成！")
        print(f"📈 处理结果:")
        print(f"   总耗时: {analysis_time:.2f} 秒")
        print(f"   发现价差商品: {len(diff_items)} 个")
        print(f"   处理效率: {len(diff_items)/analysis_time:.2f} 商品/秒")
        
        if diff_items:
            # 显示前5个最佳价差商品
            print(f"\n🏆 价差最高的5个商品:")
            sorted_items = sorted(diff_items, key=lambda x: x.profit_rate, reverse=True)
            for i, item in enumerate(sorted_items[:5], 1):
                print(f"   #{i}: {item.name}")
                print(f"      价差: ¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
                print(f"      Buff: ¥{item.buff_price} → 悠悠有品: ¥{item.youpin_price}")
        
        return diff_items

async def test_custom_limits():
    """测试自定义限制"""
    print(f"\n🔧 测试自定义限制...")
    
    # 测试更大的数量限制
    test_limits = [100, 200, 500]
    
    for limit in test_limits:
        print(f"\n📊 测试处理 {limit} 个商品...")
        start_time = time.time()
        
        async with IntegratedPriceAnalyzer(price_diff_threshold=10.0) as analyzer:
            diff_items = await analyzer.analyze_price_differences(max_items=limit)
            
            test_time = time.time() - start_time
            print(f"   耗时: {test_time:.2f} 秒")
            print(f"   发现: {len(diff_items)} 个价差商品")
            print(f"   效率: {len(diff_items)/test_time:.2f} 商品/秒")

def show_config_info():
    """显示配置信息"""
    print(f"\n⚙️ 系统配置说明:")
    print(f"   📦 最大处理商品数: {Config.MAX_ITEMS_TO_PROCESS}")
    print(f"   🔵 Buff最大页数: {Config.BUFF_MAX_PAGES} (每页{Config.BUFF_PAGE_SIZE}个)")
    print(f"   🟡 悠悠有品最大页数: {Config.YOUPIN_MAX_PAGES} (每页{Config.YOUPIN_PAGE_SIZE}个)")
    print(f"   ⚡ 并发控制: Buff={Config.BUFF_BATCH_SIZE}, 悠悠有品={Config.YOUPIN_BATCH_SIZE}")
    print(f"   ⏱️ 请求延迟: {Config.REQUEST_DELAY}秒")
    
    # 估算获取的商品总数
    estimated_buff = Config.BUFF_MAX_PAGES * Config.BUFF_PAGE_SIZE
    estimated_youpin = Config.YOUPIN_MAX_PAGES * Config.YOUPIN_PAGE_SIZE
    
    print(f"\n📈 估算获取数量:")
    print(f"   Buff: 约 {estimated_buff:,} 个商品")
    print(f"   悠悠有品: 约 {estimated_youpin:,} 个商品")
    print(f"   处理上限: {Config.MAX_ITEMS_TO_PROCESS} 个商品")

if __name__ == "__main__":
    print("🎯 CS:GO饰品价差系统 - 大规模处理测试")
    print("="*80)
    
    show_config_info()
    
    # 运行测试
    asyncio.run(test_large_scale_processing())
    asyncio.run(test_custom_limits()) 