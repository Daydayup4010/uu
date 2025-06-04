#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的全量和增量更新系统
"""

import asyncio
import time
from update_manager import get_update_manager
from search_api_client import SearchManager
from config import Config

async def test_search_api():
    """测试搜索API"""
    print("🔍 测试搜索API客户端")
    print("="*50)
    
    try:
        async with SearchManager() as search_manager:
            # 测试搜索
            keyword = "AK-47"
            print(f"搜索关键词: {keyword}")
            
            results = await search_manager.search_both_platforms(keyword)
            
            print(f"悠悠有品结果: {len(results['youpin'])}个")
            if results['youpin']:
                for i, item in enumerate(results['youpin'][:3], 1):
                    print(f"  {i}. {item.name}: ¥{item.price}")
            
            print(f"Buff结果: {len(results['buff'])}个")
            if results['buff']:
                for i, item in enumerate(results['buff'][:3], 1):
                    print(f"  {i}. {item.name}: ¥{item.price}")
                    
    except Exception as e:
        print(f"搜索API测试失败: {e}")

def test_update_manager():
    """测试更新管理器"""
    print("\n🧪 测试更新管理器")
    print("="*50)
    
    manager = get_update_manager()
    
    # 显示状态
    status = manager.get_status()
    print(f"更新管理器状态:")
    print(f"  运行中: {status['is_running']}")
    print(f"  上次全量更新: {status['last_full_update']}")
    print(f"  上次增量更新: {status['last_incremental_update']}")
    print(f"  当前商品数: {status['current_items_count']}")
    print(f"  缓存关键词数: {status['cached_hashnames_count']}")
    print(f"  需要全量更新: {status['should_full_update']}")
    
    # 启动管理器
    print("\n启动更新管理器...")
    manager.start()
    
    # 等待一段时间
    print("等待10秒观察运行情况...")
    time.sleep(10)
    
    # 显示更新后的状态
    updated_status = manager.get_status()
    print(f"\n10秒后的状态:")
    print(f"  运行中: {updated_status['is_running']}")
    print(f"  当前商品数: {updated_status['current_items_count']}")
    
    # 获取当前数据
    current_data = manager.get_current_data()
    print(f"  实际数据量: {len(current_data)}")
    
    if current_data:
        print("\n前3个价差商品:")
        for i, item in enumerate(current_data[:3], 1):
            print(f"  {i}. {item.name}: 价差¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
    
    # 停止管理器
    print("\n停止更新管理器...")
    manager.stop()

def test_config():
    """测试配置"""
    print("\n⚙️ 测试配置设置")
    print("="*50)
    
    print(f"价格差异区间: {Config.get_price_range()}")
    print(f"Buff价格筛选区间: {Config.get_buff_price_range()}")
    print(f"全量更新间隔: {Config.FULL_UPDATE_INTERVAL_HOURS}小时")
    print(f"增量更新间隔: {Config.INCREMENTAL_UPDATE_INTERVAL_MINUTES}分钟")
    print(f"增量缓存大小: {Config.INCREMENTAL_CACHE_SIZE}")
    
    # 测试区间检查
    test_prices = [5.0, 15.0, 50.0, 500.0, 1500.0]
    print(f"\nBuff价格筛选测试:")
    for price in test_prices:
        in_range = Config.is_buff_price_in_range(price)
        print(f"  ¥{price}: {'✓' if in_range else '✗'}")
    
    test_diffs = [1.0, 3.5, 4.0, 6.0, 10.0]
    print(f"\n价差区间测试:")
    for diff in test_diffs:
        in_range = Config.is_price_diff_in_range(diff)
        print(f"  ¥{diff}: {'✓' if in_range else '✗'}")

async def main():
    """主测试函数"""
    print("🚀 新系统综合测试")
    print("="*80)
    
    # 测试配置
    test_config()
    
    # 测试搜索API
    await test_search_api()
    
    # 测试更新管理器
    test_update_manager()
    
    print("\n✅ 测试完成！")
    print("\n📝 总结:")
    print("1. 全量更新：每1小时获取所有Buff和悠悠有品数据")
    print("2. 增量更新：每1分钟搜索缓存的hashname")
    print("3. Buff价格筛选：只分析指定价格区间的商品")
    print("4. 全局并发控制：防止多个分析同时运行")
    print("5. 前端实时更新：支持强制全量/增量更新")

if __name__ == "__main__":
    asyncio.run(main()) 