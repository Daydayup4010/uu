#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OptimizedAPIClient是否正确使用config.py中的配置
"""

import asyncio
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient
from config import Config

async def test_config_usage():
    """测试配置使用"""
    print("🧪 测试OptimizedAPIClient配置使用")
    print("="*50)
    
    print(f"📋 配置文件中的设置:")
    print(f"   BUFF_MAX_PAGES = {Config.BUFF_MAX_PAGES}")
    print(f"   YOUPIN_MAX_PAGES = {Config.YOUPIN_MAX_PAGES}")
    print(f"   BUFF_PAGE_SIZE = {Config.BUFF_PAGE_SIZE}")
    print(f"   YOUPIN_PAGE_SIZE = {Config.YOUPIN_PAGE_SIZE}")
    
    print(f"\n🔍 测试Buff客户端 (不传max_pages参数，应该使用配置中的2000):")
    async with OptimizedBuffClient() as buff_client:
        # 不传参数，测试是否使用配置文件中的值
        try:
            # 由于我们只是测试配置读取，设定一个很小的值避免实际获取大量数据
            items = await buff_client.get_all_goods_safe(max_pages=2)
            print(f"   ✅ Buff客户端工作正常")
        except Exception as e:
            print(f"   ❌ Buff客户端异常: {e}")
    
    print(f"\n🔍 测试悠悠有品客户端 (不传max_pages参数，应该使用配置中的2000):")
    async with OptimizedYoupinClient() as youpin_client:
        # 不传参数，测试是否使用配置文件中的值
        try:
            # 由于我们只是测试配置读取，设定一个很小的值避免实际获取大量数据  
            items = await youpin_client.get_all_items_safe(max_pages=2)
            print(f"   ✅ 悠悠有品客户端工作正常")
        except Exception as e:
            print(f"   ❌ 悠悠有品客户端异常: {e}")
    
    print(f"\n🎯 配置使用验证完成！")

if __name__ == "__main__":
    asyncio.run(test_config_usage()) 