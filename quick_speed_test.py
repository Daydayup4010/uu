#!/usr/bin/env python3
"""
快速API速度测试
验证悠悠有品优化后的性能改善
"""
import asyncio
import time
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient
from config import Config
import logging

# 简化日志
logging.basicConfig(level=logging.WARNING)

async def test_single_page_speed():
    """测试单页获取速度"""
    print("🧪 单页速度测试 (测试1页)")
    print("="*50)
    
    # 显示当前配置
    print(f"📊 当前延迟配置:")
    print(f"   Buff API延迟: {Config.BUFF_API_DELAY}秒")
    print(f"   悠悠有品API延迟: {Config.YOUPIN_API_DELAY}秒")
    print()
    
    # 测试Buff
    print("🔥 测试Buff API (第1页)...")
    buff_start = time.time()
    try:
        async with OptimizedBuffClient() as client:
            buff_data = await client.get_goods_list(page_num=1)
            buff_time = time.time() - buff_start
            buff_count = len(buff_data['data']['items']) if buff_data and 'data' in buff_data and 'items' in buff_data['data'] else 0
            print(f"   ✅ Buff: {buff_count}个商品, 耗时{buff_time:.2f}秒")
    except Exception as e:
        print(f"   ❌ Buff失败: {e}")
        buff_time = 999
        buff_count = 0
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试悠悠有品
    print("🛍️ 测试悠悠有品API (第1页)...")
    youpin_start = time.time()
    try:
        async with OptimizedYoupinClient() as client:
            youpin_data = await client.get_market_goods_safe(page_index=1)
            youpin_time = time.time() - youpin_start
            youpin_count = len(youpin_data) if youpin_data else 0
            print(f"   ✅ 悠悠有品: {youpin_count}个商品, 耗时{youpin_time:.2f}秒")
    except Exception as e:
        print(f"   ❌ 悠悠有品失败: {e}")
        youpin_time = 999
        youpin_count = 0
    
    # 结果对比
    print("\n📈 速度对比:")
    if buff_time < 999 and youpin_time < 999:
        speed_ratio = youpin_time / buff_time if buff_time > 0 else 0
        print(f"   悠悠有品比Buff慢 {speed_ratio:.1f}倍")
        print(f"   速度差异: {youpin_time - buff_time:.2f}秒")
        
        if speed_ratio < 3:
            print("   🎉 悠悠有品速度已明显改善！")
        elif speed_ratio < 5:
            print("   📈 悠悠有品速度有所改善")
        else:
            print("   ⚠️ 悠悠有品仍然较慢")
    
    print("\n" + "="*50)

async def test_config_adjustment():
    """测试不同配置的效果"""
    print("\n🔧 测试不同延迟配置的效果")
    print("="*50)
    
    original_delay = Config.YOUPIN_API_DELAY
    
    # 测试更快的配置
    test_delays = [1.5, 2.0, 3.0]
    
    for delay in test_delays:
        print(f"\n📊 测试悠悠有品延迟={delay}秒:")
        Config.YOUPIN_API_DELAY = delay
        
        start_time = time.time()
        try:
            async with OptimizedYoupinClient() as client:
                data = await client.get_market_goods_safe(page_index=1)
                elapsed = time.time() - start_time
                count = len(data) if data else 0
                print(f"   结果: {count}个商品, 总耗时{elapsed:.2f}秒")
        except Exception as e:
            print(f"   失败: {e}")
        
        await asyncio.sleep(1)  # 避免请求过快
    
    # 恢复原始配置
    Config.YOUPIN_API_DELAY = original_delay
    print(f"\n🔄 已恢复原始配置: {original_delay}秒")

async def main():
    """主测试函数"""
    print("⚡ 快速API速度测试")
    print("验证悠悠有品优化后的性能")
    
    # 基本速度测试
    await test_single_page_speed()
    
    # 配置调整测试
    await test_config_adjustment()
    
    print("\n✅ 测试完成!")
    print("\n💡 优化建议:")
    print("   1. 如果悠悠有品速度仍然很慢，可以减少 YOUPIN_API_DELAY")
    print("   2. 如果出现429错误，需要增加延迟")
    print("   3. 可以在 config.py 中调整 YOUPIN_API_DELAY 参数")

if __name__ == "__main__":
    asyncio.run(main()) 