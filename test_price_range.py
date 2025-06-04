#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试价格区间筛选功能
"""

import asyncio
from config import Config
from integrated_price_system import IntegratedPriceAnalyzer

async def test_price_range_filtering():
    """测试价格区间筛选功能"""
    
    print("🧪 测试价格区间筛选功能")
    print("="*60)
    
    # 显示当前配置
    print(f"📊 当前配置:")
    print(f"   价格差异区间: {Config.PRICE_DIFF_MIN}元 - {Config.PRICE_DIFF_MAX}元")
    print(f"   最大输出数量: {Config.MAX_OUTPUT_ITEMS}个")
    print(f"   Buff最大页数: {Config.BUFF_MAX_PAGES}")
    print(f"   悠悠有品最大页数: {Config.YOUPIN_MAX_PAGES}")
    
    # 测试不同的价格区间设置
    test_ranges = [
        (3.0, 5.0),   # 3-5元区间
        (5.0, 10.0),  # 5-10元区间
        (10.0, 20.0), # 10-20元区间
        (1.0, 3.0),   # 1-3元区间
    ]
    
    for min_diff, max_diff in test_ranges:
        print(f"\n🔄 测试价格区间: {min_diff}元 - {max_diff}元")
        print("-" * 40)
        
        # 更新价格区间
        Config.update_price_range(min_diff, max_diff)
        
        # 验证区间筛选逻辑
        test_prices = [0.5, 1.5, 2.5, 3.5, 4.5, 6.0, 8.0, 12.0, 15.0, 25.0]
        
        print(f"   测试价差值筛选:")
        for price in test_prices:
            in_range = Config.is_price_diff_in_range(price)
            status = "✅ 符合" if in_range else "❌ 不符合"
            print(f"     {price}元: {status}")
        
        # 运行小规模分析测试
        try:
            async with IntegratedPriceAnalyzer() as analyzer:
                print(f"\n   🚀 运行小规模分析测试...")
                diff_items = await analyzer.analyze_price_differences(max_output_items=10)
                
                if diff_items:
                    print(f"   ✅ 找到 {len(diff_items)} 个符合区间的商品")
                    for i, item in enumerate(diff_items[:3], 1):
                        print(f"     #{i}: {item.name}")
                        print(f"         价差: ¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
                else:
                    print(f"   ⚠️ 在该价格区间内未找到符合条件的商品")
                    
        except Exception as e:
            print(f"   ❌ 分析测试失败: {e}")
    
    # 恢复默认设置
    print(f"\n🔄 恢复默认设置...")
    Config.update_price_range(3.0, 5.0)
    print(f"✅ 已恢复默认价格区间: {Config.PRICE_DIFF_MIN}元 - {Config.PRICE_DIFF_MAX}元")

async def test_config_methods():
    """测试配置方法"""
    print(f"\n🧪 测试配置方法")
    print("="*40)
    
    # 测试获取价格区间
    price_range = Config.get_price_range()
    print(f"📊 当前价格区间: {price_range}")
    
    # 测试获取处理限制
    limits = Config.get_processing_limits()
    print(f"📋 处理限制配置:")
    for key, value in limits.items():
        print(f"   {key}: {value}")
    
    # 测试价差检查
    test_values = [2.0, 3.5, 4.0, 5.5, 10.0]
    print(f"\n🔍 价差检查测试:")
    for value in test_values:
        in_range = Config.is_price_diff_in_range(value)
        status = "✅ 在区间内" if in_range else "❌ 超出区间"
        print(f"   {value}元: {status}")

def test_workflow_explanation():
    """解释正确的工作流程"""
    print(f"\n📋 正确的工作流程说明")
    print("="*50)
    
    print(f"✅ 正确流程:")
    print(f"   1. 获取所有Buff商品数据 (最多 {Config.BUFF_MAX_PAGES} 页)")
    print(f"   2. 获取所有悠悠有品商品数据 (最多 {Config.YOUPIN_MAX_PAGES} 页)")
    print(f"   3. 对所有商品进行价格匹配")
    print(f"   4. 根据价格差异区间筛选 ({Config.PRICE_DIFF_MIN}-{Config.PRICE_DIFF_MAX}元)")
    print(f"   5. 按利润率排序")
    print(f"   6. 限制输出数量 (最多 {Config.MAX_OUTPUT_ITEMS} 个)")
    
    print(f"\n❌ 之前的错误流程:")
    print(f"   1. 获取所有商品数据")
    print(f"   2. 只分析前N个商品 ← 这里有问题")
    print(f"   3. 输出结果")
    
    print(f"\n🔥 关键改进:")
    print(f"   • 处理所有商品，不限制分析数量")
    print(f"   • 使用价格差异区间筛选，而非单一阈值")
    print(f"   • 最后才限制输出数量")
    print(f"   • 提高了发现优质商品的概率")

async def main():
    """主函数"""
    print("🎯 价格区间筛选功能测试")
    print("="*60)
    
    # 测试配置方法
    await test_config_methods()
    
    # 解释工作流程
    test_workflow_explanation()
    
    # 测试价格区间筛选
    await test_price_range_filtering()
    
    print(f"\n✅ 所有测试完成！")
    print(f"🎉 价格区间筛选功能已就绪，可以开始使用")

if __name__ == "__main__":
    asyncio.run(main()) 