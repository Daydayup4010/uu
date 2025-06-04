#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的API接口
"""

import asyncio
import time
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient

async def test_fixed_buff_api():
    """测试修复后的Buff API"""
    print("🔧 测试修复后的Buff API...")
    
    try:
        async with OptimizedBuffClient() as buff_client:
            # 测试获取第一页
            result = await buff_client.get_goods_list(page_num=1)
            
            if result and 'data' in result:
                items = result['data'].get('items', [])
                page_size = len(items)
                print(f"   ✅ Buff API成功: 获取了 {page_size} 个商品")
                print(f"   📊 页面大小符合预期: {page_size >= 80}")
                return True
            else:
                print(f"   ❌ Buff API失败: 无有效数据")
                return False
                
    except Exception as e:
        print(f"   ❌ Buff API异常: {e}")
        return False

async def test_fixed_youpin_api():
    """测试修复后的悠悠有品API"""
    print("\n🔧 测试修复后的悠悠有品API...")
    
    try:
        async with OptimizedYoupinClient() as youpin_client:
            # 测试获取第一页
            result = await youpin_client.get_market_goods_safe(page_index=1, page_size=10)
            
            if result and len(result) > 0:
                print(f"   ✅ 悠悠有品API成功: 获取了 {len(result)} 个商品")
                
                # 显示商品数据格式
                if result:
                    sample_item = result[0]
                    print(f"   📋 商品数据样本: {list(sample_item.keys())}")
                    if 'commodityName' in sample_item:
                        print(f"   📝 商品名称: {sample_item['commodityName']}")
                    if 'price' in sample_item:
                        print(f"   💰 价格: {sample_item['price']}")
                
                return True
            else:
                print(f"   ❌ 悠悠有品API失败: 无有效数据")
                return False
                
    except Exception as e:
        print(f"   ❌ 悠悠有品API异常: {e}")
        return False

async def test_page_size_consistency():
    """测试页面大小一致性"""
    print("\n📏 测试页面大小一致性...")
    
    try:
        async with OptimizedBuffClient() as buff_client:
            # 测试不同页面大小
            test_sizes = [80, 100]
            
            for size in test_sizes:
                result = await buff_client.get_goods_list(page_num=1, page_size=size)
                if result and 'data' in result:
                    actual_size = len(result['data'].get('items', []))
                    print(f"   📊 请求 {size} 个商品，实际获取 {actual_size} 个")
                else:
                    print(f"   ❌ 请求 {size} 个商品失败")
                
                await asyncio.sleep(1)  # 避免频率限制
        
        return True
        
    except Exception as e:
        print(f"   ❌ 页面大小测试异常: {e}")
        return False

def show_fix_summary():
    """显示修复总结"""
    print("\n🔧 修复总结:")
    print("="*50)
    print("✅ Buff API修复:")
    print("   - 使用Config.BUFF_PAGE_SIZE作为默认值")
    print("   - 明确设置page_size参数")
    print("   - 移除了条件判断逻辑")
    
    print("\n✅ 悠悠有品API修复:")
    print("   - 更正API端点到正确的URL")
    print("   - 使用POST请求替代GET")
    print("   - 修正请求参数格式")
    print("   - 更新认证头格式")
    print("   - 正确处理响应数据结构")
    
    print("\n🎯 预期改进:")
    print("   - Buff API页面大小现在正确为80个商品")
    print("   - 悠悠有品API不再返回404错误")
    print("   - 两个API都应该正常工作")

async def main():
    """主函数"""
    print("🚀 测试修复后的API接口")
    print("="*50)
    
    show_fix_summary()
    
    # 测试修复后的API
    buff_ok = await test_fixed_buff_api()
    youpin_ok = await test_fixed_youpin_api()
    
    # 测试页面大小
    size_ok = await test_page_size_consistency()
    
    print(f"\n📊 测试结果汇总:")
    print(f"   Buff API: {'✅ 正常' if buff_ok else '❌ 异常'}")
    print(f"   悠悠有品API: {'✅ 正常' if youpin_ok else '❌ 异常'}")
    print(f"   页面大小: {'✅ 正常' if size_ok else '❌ 异常'}")
    
    if buff_ok and youpin_ok:
        print(f"\n🎉 所有API修复成功！")
        print(f"💡 现在可以正常使用系统了")
    else:
        print(f"\n⚠️ 仍有API问题需要解决")
        if not youpin_ok:
            print("   🔧 悠悠有品问题可能的原因:")
            print("      - 认证信息过期或不正确")
            print("      - 需要更新device_id、uk等参数")
            print("      - API端点可能有变化")

if __name__ == "__main__":
    asyncio.run(main()) 