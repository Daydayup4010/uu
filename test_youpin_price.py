#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试悠悠有品价格估算算法
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api_scrapers import YoupinAPIClient

async def test_price_estimation():
    """测试价格估算算法"""
    print("🎯 测试悠悠有品价格估算算法")
    print("="*60)
    
    # 测试商品列表
    test_items = [
        # 刀具类
        "★ 蝴蝶刀 | 伽玛多普勒 (崭新出厂)",
        "★ M9刺刀 | 大马士革钢 (略有磨损)",
        "★ 折叠刀 | 蓝钢 (久经沙场)",
        
        # 步枪类
        "AK-47 | 火蛇 (崭新出厂)",
        "AK-47 | 红线 (略有磨损)",
        "M4A4 | 龙王 (崭新出厂)",
        "M4A1-S | 金属网格 (久经沙场)",
        "AWP | 二西莫夫 (略有磨损)",
        "AWP | 狩猎网格 (战痕累累)",
        
        # 手枪类
        "格洛克-18 | 水元素 (崭新出厂)",
        "USP-S | 守护者 (略有磨损)",
        "沙漠之鹰 | 印花集锦 (久经沙场)",
        
        # 冲锋枪类
        "MAC-10 | 霓虹骑士 (崭新出厂)",
        "MP9 | 特工 (略有磨损)",
    ]
    
    async with YoupinAPIClient() as client:
        print("📊 价格估算结果:")
        print("-" * 60)
        
        for item_name in test_items:
            price = await client.search_item(item_name)
            explanation = client.get_price_explanation(item_name, price)
            
            print(f"🔫 {item_name}")
            print(f"   💰 估算价格: ¥{price}")
            print(f"   📝 说明: {explanation}")
            print()
            
        print("="*60)
        print("📋 价格估算算法特点:")
        print("✅ 基于武器类型设定基础价格范围")
        print("✅ 考虑皮肤稀有度（龙王、传说、隐秘等）")
        print("✅ 根据磨损度调整价格（崭新 > 略有磨损 > 久经沙场等）")
        print("✅ 模拟市场波动（±20%随机变化）")
        print("✅ 价格范围合理（1-5000元）")
        print()
        print("⚠️  注意：这些价格是基于算法估算的，不是真实的悠悠有品价格")
        print("💡 真实价格请访问悠悠有品官网查询")

async def compare_price_strategies():
    """对比不同价格策略"""
    print("\n" + "="*60)
    print("🔄 对比不同价格策略")
    print("="*60)
    
    test_item = "AK-47 | 火蛇 (崭新出厂)"
    
    async with YoupinAPIClient() as client:
        # 多次估算看随机变化
        prices = []
        for i in range(5):
            price = await client.search_item(test_item)
            prices.append(price)
        
        print(f"🎯 测试商品: {test_item}")
        print(f"📊 5次估算结果: {prices}")
        print(f"💹 价格范围: ¥{min(prices):.2f} - ¥{max(prices):.2f}")
        print(f"📈 平均价格: ¥{sum(prices)/len(prices):.2f}")
        print(f"📉 价格波动: ±{((max(prices)-min(prices))/2/sum(prices)*len(prices)*100):.1f}%")

async def main():
    """主函数"""
    await test_price_estimation()
    await compare_price_strategies()

if __name__ == "__main__":
    asyncio.run(main()) 