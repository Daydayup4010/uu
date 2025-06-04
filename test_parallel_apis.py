#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真正并行的API获取
"""

import asyncio
import time
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient

async def test_serial_vs_parallel():
    """对比串行和并行获取的性能"""
    print("🚀 对比串行 vs 并行获取性能")
    print("="*60)
    
    # 测试小量数据避免频率限制
    test_pages = 3
    
    # 1. 串行获取（当前的实现）
    print(f"\n1️⃣ 串行获取测试 (测试{test_pages}页)...")
    serial_start = time.time()
    
    try:
        async with OptimizedBuffClient() as buff_client:
            buff_items = await buff_client.get_all_goods_safe(max_pages=test_pages)
        
        async with OptimizedYoupinClient() as youpin_client:
            youpin_items = await youpin_client.get_all_items_safe(max_pages=test_pages)
        
        serial_time = time.time() - serial_start
        print(f"   ✅ 串行完成: {serial_time:.2f}秒")
        print(f"   📊 Buff: {len(buff_items) if buff_items else 0} 个商品")
        print(f"   📊 悠悠有品: {len(youpin_items) if youpin_items else 0} 个商品")
        
    except Exception as e:
        print(f"   ❌ 串行获取失败: {e}")
        serial_time = float('inf')
    
    # 2. 并行获取（两个平台同时开始）
    print(f"\n2️⃣ 并行获取测试 (两个平台同时)...")
    parallel_start = time.time()
    
    try:
        # 创建并行任务
        buff_task = asyncio.create_task(get_buff_data_parallel(test_pages))
        youpin_task = asyncio.create_task(get_youpin_data_parallel(test_pages))
        
        # 同时等待两个任务完成
        buff_items, youpin_items = await asyncio.gather(
            buff_task, youpin_task, return_exceptions=True
        )
        
        parallel_time = time.time() - parallel_start
        print(f"   ✅ 并行完成: {parallel_time:.2f}秒")
        
        if isinstance(buff_items, Exception):
            print(f"   ❌ Buff获取失败: {buff_items}")
            buff_count = 0
        else:
            buff_count = len(buff_items) if buff_items else 0
        
        if isinstance(youpin_items, Exception):
            print(f"   ❌ 悠悠有品获取失败: {youpin_items}")
            youpin_count = 0
        else:
            youpin_count = len(youpin_items) if youpin_items else 0
        
        print(f"   📊 Buff: {buff_count} 个商品")
        print(f"   📊 悠悠有品: {youpin_count} 个商品")
        
    except Exception as e:
        print(f"   ❌ 并行获取失败: {e}")
        parallel_time = float('inf')
    
    # 3. 性能对比
    print(f"\n📊 性能对比:")
    print(f"   串行耗时: {serial_time:.2f} 秒")
    print(f"   并行耗时: {parallel_time:.2f} 秒")
    
    if serial_time != float('inf') and parallel_time != float('inf'):
        speedup = serial_time / parallel_time
        print(f"   🚀 性能提升: {speedup:.2f}x")
        print(f"   📈 时间节省: {serial_time - parallel_time:.2f} 秒 ({((serial_time - parallel_time) / serial_time) * 100:.1f}%)")
    
    return serial_time, parallel_time

async def get_buff_data_parallel(max_pages: int):
    """并行获取Buff数据"""
    async with OptimizedBuffClient() as client:
        return await client.get_all_goods_safe(max_pages=max_pages)

async def get_youpin_data_parallel(max_pages: int):
    """并行获取悠悠有品数据"""
    async with OptimizedYoupinClient() as client:
        return await client.get_all_items_safe(max_pages=max_pages)

async def test_true_parallel_pages():
    """测试真正的页面级别并行"""
    print(f"\n3️⃣ 页面级别并行测试...")
    print("   说明：让每个页面请求都并行进行")
    
    max_pages = 3
    start_time = time.time()
    
    try:
        # 创建所有页面的任务
        all_tasks = []
        
        # Buff页面任务
        async with OptimizedBuffClient() as buff_client:
            for page in range(1, max_pages + 1):
                task = asyncio.create_task(
                    buff_client.get_goods_list(page_num=page),
                    name=f"buff_page_{page}"
                )
                all_tasks.append(('buff', page, task))
        
        # 悠悠有品页面任务
        async with OptimizedYoupinClient() as youpin_client:
            for page in range(1, max_pages + 1):
                task = asyncio.create_task(
                    youpin_client.get_market_goods_safe(page_index=page),
                    name=f"youpin_page_{page}"
                )
                all_tasks.append(('youpin', page, task))
        
        print(f"   🚀 创建了 {len(all_tasks)} 个并行任务")
        
        # 分批执行避免过多并发
        batch_size = 4  # 每批4个请求
        all_results = []
        
        for i in range(0, len(all_tasks), batch_size):
            batch = all_tasks[i:i + batch_size]
            batch_tasks = [task for _, _, task in batch]
            
            print(f"   📦 执行第{i//batch_size + 1}批，包含{len(batch)}个任务...")
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 处理批次结果
            for (platform, page, _), result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    print(f"   ❌ {platform} 第{page}页失败: {result}")
                else:
                    if platform == 'buff' and result and 'data' in result:
                        count = len(result['data'].get('items', []))
                        print(f"   ✅ {platform} 第{page}页: {count}个商品")
                    elif platform == 'youpin' and result:
                        count = len(result) if isinstance(result, list) else 0
                        print(f"   ✅ {platform} 第{page}页: {count}个商品")
            
            all_results.extend(batch_results)
            
            # 批次间延迟
            if i + batch_size < len(all_tasks):
                await asyncio.sleep(1)
        
        total_time = time.time() - start_time
        print(f"   ⚡ 页面级并行完成: {total_time:.2f}秒")
        
        return total_time
        
    except Exception as e:
        print(f"   ❌ 页面级并行失败: {e}")
        return float('inf')

def explain_parallel_design():
    """解释并行设计的权衡"""
    print("\n💡 并行设计权衡说明:")
    print("="*50)
    
    print("🔧 当前设计 (串行页面获取):")
    print("   ✅ 优点:")
    print("      - 避免API频率限制 (429错误)")
    print("      - 减少服务器压力")
    print("      - 降低IP被封风险")
    print("      - 更稳定可靠")
    print("   ❌ 缺点:")
    print("      - 速度较慢")
    print("      - 不能充分利用网络带宽")
    
    print("\n🚀 完全并行设计:")
    print("   ✅ 优点:")
    print("      - 速度更快")
    print("      - 充分利用网络并发")
    print("      - 用户体验更好")
    print("   ❌ 缺点:")
    print("      - 容易触发频率限制")
    print("      - 可能被识别为爬虫")
    print("      - 成功率可能降低")
    
    print("\n⚖️ 推荐策略:")
    print("   1. 高层级并行：两个平台同时获取 ✅ (已实现)")
    print("   2. 页面级串行：每个平台内部串行 ✅ (当前策略)")
    print("   3. 可配置并行度：允许用户选择 💡 (可以添加)")

async def main():
    """主函数"""
    print("🎯 并行 vs 串行 API获取性能测试")
    print("="*60)
    
    # 解释设计
    explain_parallel_design()
    
    # 性能测试
    try:
        serial_time, parallel_time = await test_serial_vs_parallel()
        page_parallel_time = await test_true_parallel_pages()
        
        print(f"\n🏆 最终对比:")
        print(f"   串行获取: {serial_time:.2f}秒")
        print(f"   平台并行: {parallel_time:.2f}秒")
        print(f"   页面并行: {page_parallel_time:.2f}秒")
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
    
    print(f"\n💡 结论:")
    print(f"   当前系统已经实现了平台级别的并行获取")
    print(f"   页面级别采用串行是为了提高成功率")
    print(f"   如果需要更快速度，可以调整Config中的批次大小")

if __name__ == "__main__":
    asyncio.run(main()) 