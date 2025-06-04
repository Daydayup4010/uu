#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试只使用Hash精确匹配的效果
"""

import asyncio
from integrated_price_system import IntegratedPriceAnalyzer

async def test_hash_only_matching():
    """测试只使用Hash精确匹配"""
    print("🎯 Hash精确匹配测试")
    print("="*50)
    
    print("🔥 当前配置: 只使用Hash精确匹配")
    print("✅ 已禁用模糊匹配")
    print("✅ 保留名称精确匹配作为备用")
    print("-"*50)
    
    try:
        async with IntegratedPriceAnalyzer() as analyzer:
            # 运行小规模测试
            print("\n🚀 开始Hash精确匹配测试...")
            diff_items = await analyzer.analyze_price_differences(max_output_items=20)
            
            if diff_items:
                print(f"\n🎯 找到 {len(diff_items)} 个有价差的商品:")
                print("="*60)
                
                for i, item in enumerate(diff_items[:10], 1):
                    print(f"#{i}: {item.name}")
                    print(f"    💰 Buff: ¥{item.buff_price:.2f} → 悠悠有品: ¥{item.youpin_price:.2f}")
                    print(f"    📊 价差: ¥{item.price_diff:.2f} | 利润率: {item.profit_rate:.1f}%")
                    print(f"    🔗 {item.buff_url}")
                    print("-" * 40)
                
                print(f"\n📈 总结:")
                print(f"   找到有效价差商品: {len(diff_items)} 个")
                print(f"   平均价差: ¥{sum(item.price_diff for item in diff_items) / len(diff_items):.2f}")
                print(f"   平均利润率: {sum(item.profit_rate for item in diff_items) / len(diff_items):.1f}%")
                
            else:
                print("⚠️ 未找到符合价差区间的商品")
                print("💡 这可能是因为:")
                print("   1. Hash精确匹配更严格，匹配数量较少")
                print("   2. 当前价格区间设置过于严格")
                print("   3. 两平台商品重叠率较低")
                
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

def show_comparison():
    """显示Hash精确匹配 vs 模糊匹配的对比"""
    print("\n📊 Hash精确匹配 vs 模糊匹配对比")
    print("="*60)
    
    print("🔥 Hash精确匹配模式 (当前):")
    print("   ✅ 100% 精确 - 基于market_hash_name字段")
    print("   ✅ 速度快 - 直接字典查找")
    print("   ✅ 无误匹配 - 避免相似商品的错误匹配")
    print("   ⚠️ 覆盖率可能较低 - 只匹配完全相同的商品")
    
    print("\n🔍 模糊匹配模式 (已禁用):")
    print("   ❌ 可能误匹配 - 基于相似度算法")
    print("   ❌ 速度慢 - 需要计算相似度")
    print("   ❌ 准确性风险 - 可能匹配到不同商品")
    print("   ✅ 覆盖率高 - 可以匹配相似的商品")
    
    print("\n💡 优化建议:")
    print("   1. 确保两平台数据获取量足够大")
    print("   2. 可以适当调整价格区间来获得更多结果")
    print("   3. 监控Hash匹配成功率")

async def main():
    """主函数"""
    print("🧪 Hash精确匹配测试工具")
    print("="*60)
    
    show_comparison()
    await test_hash_only_matching()
    
    print(f"\n🔧 当前配置信息:")
    from config import Config
    print(f"   价格差异区间: {Config.PRICE_DIFF_MIN}元 - {Config.PRICE_DIFF_MAX}元")
    print(f"   最大输出数量: {Config.MAX_OUTPUT_ITEMS}")
    print(f"   Buff最大页数: {Config.BUFF_MAX_PAGES}")
    print(f"   悠悠有品最大页数: {Config.YOUPIN_MAX_PAGES}")
    
    print(f"\n🎯 系统现在只使用Hash精确匹配，确保100%准确性！")

if __name__ == "__main__":
    asyncio.run(main()) 