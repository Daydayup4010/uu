#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整数据收集器
先收集较少页数验证功能是否正常
"""

import asyncio
from collect_full_data import FullDataCollector
from config import Config

async def test_collection():
    """测试数据收集"""
    print("🧪 测试完整数据收集器")
    print("=" * 60)
    
    collector = FullDataCollector()
    
    # 测试配置
    test_buff_pages = 50      # 测试50页 Buff 数据 (约4000个商品)
    test_youpin_pages = 30    # 测试30页悠悠有品数据 (约3000个商品)
    
    print(f"📋 测试配置:")
    print(f"   Buff测试页数: {test_buff_pages}")
    print(f"   悠悠有品测试页数: {test_youpin_pages}")
    print(f"   预计Buff商品数: {test_buff_pages * Config.BUFF_PAGE_SIZE}")
    print(f"   预计悠悠有品商品数: {test_youpin_pages * Config.YOUPIN_PAGE_SIZE}")
    print(f"   预计总时间: 约{(test_buff_pages * Config.BUFF_API_DELAY + test_youpin_pages * Config.YOUPIN_API_DELAY) / 60:.1f}分钟")
    
    # 开始收集测试数据
    print("\n🔍 开始收集测试数据")
    print("=" * 60)
    
    # 收集 Buff 测试数据
    await collector.collect_buff_data(max_pages=test_buff_pages)
    
    # 等待一段时间
    await asyncio.sleep(5)
    
    # 收集悠悠有品测试数据
    await collector.collect_youpin_data(max_pages=test_youpin_pages)
    
    print("\n✅ 测试数据收集完成！")
    print("\n💡 如果测试成功，可以运行 collect_full_data.py 收集完整数据")

if __name__ == "__main__":
    asyncio.run(test_collection()) 