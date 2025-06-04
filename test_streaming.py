#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式分析器测试脚本
演示边获取边分析的增量更新功能
"""

import asyncio
from streaming_analyzer import StreamingAnalyzer

async def main():
    """测试流式分析器"""
    print("🎯 流式价差分析器测试")
    print("="*50)
    print("📝 功能特点:")
    print("   ✅ 立即返回缓存数据（如果有）")
    print("   ✅ 边获取边分析，实时推送结果")
    print("   ✅ 提升用户体验，无需长时间等待")
    print("   ✅ 支持进度追踪和错误处理")
    print()
    
    # 创建分析器
    analyzer = StreamingAnalyzer()
    
    # 统计信息
    total_updates = 0
    cached_items = 0
    incremental_items = 0
    total_found = 0
    
    print("🚀 开始流式分析...")
    print("-" * 50)
    
    try:
        async for update in analyzer.start_streaming_analysis():
            update_type = update.get('type')
            message = update.get('message', '')
            
            total_updates += 1
            
            if update_type == 'cached_data':
                cached_items = len(update.get('data', []))
                print(f"💾 缓存数据: {cached_items}个商品")
                
            elif update_type == 'progress':
                stage = update.get('stage', '')
                progress = update.get('progress', 0)
                if progress > 0:
                    print(f"📈 {message} ({progress:.1f}%)")
                else:
                    print(f"📊 {message}")
                    
            elif update_type == 'mapping_ready':
                hash_count = update.get('hash_count', 0)
                name_count = update.get('name_count', 0)
                print(f"🗺️  映射表构建完成: {hash_count}个Hash映射, {name_count}个名称映射")
                
            elif update_type == 'incremental_results':
                batch_size = update.get('batch_size', 0)
                total_found = update.get('total_found', 0)
                total_processed = update.get('total_processed', 0)
                incremental_items += batch_size
                
                print(f"✨ 增量结果: +{batch_size}个商品")
                print(f"   📊 累计发现: {total_found}个价差商品")
                print(f"   🔄 已处理: {total_processed}个商品")
                
                # 显示前几个商品的详细信息
                items = update.get('data', [])
                if items:
                    print(f"   💎 最新商品样本:")
                    for i, item in enumerate(items[:2], 1):
                        name = item.get('name', '')[:30] + '...' if len(item.get('name', '')) > 30 else item.get('name', '')
                        buff_price = item.get('buff_price', 0)
                        youpin_price = item.get('youpin_price', 0)
                        price_diff = item.get('price_diff', 0)
                        profit_rate = item.get('profit_rate', 0)
                        print(f"      #{i}: {name}")
                        print(f"          价差: ¥{price_diff:.2f} ({profit_rate:.1f}%)")
                        print(f"          Buff: ¥{buff_price:.2f} → 悠悠有品: ¥{youpin_price:.2f}")
                print()
                
            elif update_type == 'completed':
                total_found = update.get('total_found', 0)
                total_processed = update.get('total_processed', 0)
                print(f"🎉 分析完成!")
                print(f"   📊 最终统计:")
                print(f"      处理商品数: {total_processed:,}个")
                print(f"      发现价差商品: {total_found:,}个")
                print(f"      覆盖率: {(total_found/total_processed)*100:.2f}%")
                break
                
            elif update_type == 'error':
                error = update.get('error', '')
                print(f"❌ 错误: {error}")
                break
    
    except KeyboardInterrupt:
        print(f"\n⏹️  用户中断分析")
        analyzer.stop_analysis()
    
    except Exception as e:
        print(f"\n❌ 分析过程出错: {e}")
    
    finally:
        print("\n" + "="*50)
        print("📈 测试完成统计:")
        print(f"   总更新次数: {total_updates}")
        print(f"   缓存数据: {cached_items}个商品")
        print(f"   增量数据: {incremental_items}个商品")
        print(f"   最终结果: {total_found}个价差商品")
        
        print(f"\n💡 用户体验对比:")
        print(f"   传统方式: 需要等待10-15分钟才能看到结果")
        print(f"   流式方式: 立即显示缓存 + 实时更新增量")
        print(f"   体验提升: 🚀🚀🚀 显著改善！")

if __name__ == "__main__":
    asyncio.run(main()) 