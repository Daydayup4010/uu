#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的系统性能
"""

import asyncio
import time
from integrated_price_system import IntegratedPriceAnalyzer

async def test_optimized_performance():
    """测试优化后的性能"""
    print("🚀 测试优化后的系统性能")
    print("="*60)
    
    print("🔧 优化措施:")
    print("   ✅ 降低并发数量（避免频率限制）")
    print("   ✅ 增加请求间延迟（2秒间隔）")
    print("   ✅ 增强重试机制（5次重试）")
    print("   ✅ 指数退避延迟")
    print("   ✅ 更保守的连接配置")
    print("   ✅ 优化超时设置")
    print("-"*60)
    
    try:
        start_time = time.time()
        
        async with IntegratedPriceAnalyzer() as analyzer:
            print("\n🎯 开始测试优化版本...")
            
            # 测试小规模数据获取
            diff_items = await analyzer.analyze_price_differences(max_output_items=10)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"\n📊 测试结果:")
            print(f"   耗时: {total_time:.2f} 秒")
            print(f"   找到商品: {len(diff_items)} 个")
            
            if diff_items:
                print(f"\n🎯 找到的价差商品:")
                for i, item in enumerate(diff_items[:5], 1):
                    print(f"   #{i}: {item.name}")
                    print(f"      价差: ¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
                
                # 计算性能指标
                items_per_minute = (len(diff_items) / total_time) * 60
                print(f"\n⚡ 性能指标:")
                print(f"   平均处理速度: {items_per_minute:.1f} 个商品/分钟")
                
                if total_time < 120:  # 2分钟内完成
                    print(f"   🟢 性能: 优秀")
                elif total_time < 300:  # 5分钟内完成
                    print(f"   🟡 性能: 良好")
                else:
                    print(f"   🟠 性能: 一般")
            else:
                print("   ⚠️ 未找到符合条件的商品")
                print("   💡 建议调整价格区间获得更多结果")
                
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

async def test_api_stability():
    """测试API稳定性"""
    print("\n🔍 API稳定性测试")
    print("="*40)
    
    try:
        from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient
        
        # 测试Buff API
        print("📊 测试Buff API稳定性...")
        async with OptimizedBuffClient() as buff_client:
            success_count = 0
            total_attempts = 3
            
            for i in range(1, total_attempts + 1):
                try:
                    result = await buff_client.get_goods_list(page_num=i)
                    if result and 'data' in result:
                        items_count = len(result['data'].get('items', []))
                        print(f"   ✅ 第{i}页成功: {items_count}个商品")
                        success_count += 1
                    else:
                        print(f"   ❌ 第{i}页失败: 无有效数据")
                except Exception as e:
                    print(f"   ❌ 第{i}页异常: {e}")
            
            buff_success_rate = (success_count / total_attempts) * 100
            print(f"   📈 Buff成功率: {success_count}/{total_attempts} ({buff_success_rate:.1f}%)")
        
        # 测试悠悠有品API
        print("\n📊 测试悠悠有品API稳定性...")
        async with OptimizedYoupinClient() as youpin_client:
            success_count = 0
            total_attempts = 3
            
            for i in range(1, total_attempts + 1):
                try:
                    result = await youpin_client.get_market_goods_safe(page_index=i)
                    if result and len(result) > 0:
                        print(f"   ✅ 第{i}页成功: {len(result)}个商品")
                        success_count += 1
                    else:
                        print(f"   ❌ 第{i}页失败: 无有效数据")
                except Exception as e:
                    print(f"   ❌ 第{i}页异常: {e}")
            
            youpin_success_rate = (success_count / total_attempts) * 100
            print(f"   📈 悠悠有品成功率: {success_count}/{total_attempts} ({youpin_success_rate:.1f}%)")
        
        # 总体评估
        avg_success_rate = (buff_success_rate + youpin_success_rate) / 2
        print(f"\n📊 总体稳定性: {avg_success_rate:.1f}%")
        
        if avg_success_rate >= 80:
            print(f"   🟢 状态: 稳定")
        elif avg_success_rate >= 60:
            print(f"   🟡 状态: 一般")
        else:
            print(f"   🔴 状态: 不稳定")
            
    except Exception as e:
        print(f"❌ 稳定性测试失败: {e}")

def show_optimization_summary():
    """显示优化措施总结"""
    print("\n💡 优化措施总结")
    print("="*60)
    
    print("🔧 已实施的优化:")
    print("   1. 🚦 降低请求频率: 2秒间隔")
    print("   2. 🔄 增强重试机制: 5次重试 + 指数退避")
    print("   3. 🌐 优化连接配置: 更保守的连接池设置")
    print("   4. ⏰ 调整超时设置: 30秒总超时，10秒连接超时")
    print("   5. 📊 添加请求监控: 详细的日志和错误处理")
    print("   6. 🛡️ 双重保障: 优化客户端 + 原客户端回退")
    print("   7. 🎯 Hash精确匹配: 移除模糊匹配减少处理时间")
    
    print("\n📈 预期改进:")
    print("   ✅ 接口成功率: 从50-70% 提升到 80-95%")
    print("   ✅ 系统稳定性: 显著提升")
    print("   ✅ 错误恢复: 自动重试和回退机制")
    print("   ✅ 性能监控: 详细的成功率统计")
    
    print("\n🔮 如果仍有问题:")
    print("   🔧 进一步降低请求频率 (3-5秒间隔)")
    print("   🔧 减少并发页数 (单页串行处理)")
    print("   🔧 增加随机延迟 (模拟人工操作)")
    print("   🔧 更新API认证信息")

async def main():
    """主函数"""
    print("🧪 系统性能优化验证")
    print("="*60)
    
    show_optimization_summary()
    await test_api_stability()
    await test_optimized_performance()
    
    print(f"\n🎉 优化验证完成！")
    print(f"💡 如果仍有失败率问题，请检查API认证信息是否需要更新")

if __name__ == "__main__":
    asyncio.run(main()) 