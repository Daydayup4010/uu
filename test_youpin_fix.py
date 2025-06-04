#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的悠悠有品API客户端
"""

import asyncio
from optimized_api_client import OptimizedYoupinClient

async def test_youpin_fix():
    """测试修复后的悠悠有品API"""
    print("🧪 测试修复后的悠悠有品API客户端")
    print("="*50)
    
    async with OptimizedYoupinClient() as client:
        # 测试获取5页数据
        items = await client.get_all_items_safe(max_pages=5)
        
        print(f"\n📊 最终结果:")
        print(f"   总计获取: {len(items)} 个商品")
        print(f"   平均每页: {len(items)/5:.1f} 个商品" if len(items) > 0 else "   平均每页: 0 个商品")
        
        # 显示前几个商品
        if items:
            print(f"\n🎯 前3个商品示例:")
            for i, item in enumerate(items[:3]):
                name = item.get('commodityName', '未知商品')
                price = item.get('price', '未知价格')
                print(f"   #{i+1}: {name} - ¥{price}")
        else:
            print("\n❌ 没有获取到任何商品")

if __name__ == "__main__":
    asyncio.run(test_youpin_fix()) 