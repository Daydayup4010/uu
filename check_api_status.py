#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查API接口状态和失败情况
"""

import asyncio
import time
from integrated_price_system import BuffAPIClient
from youpin_working_api import YoupinWorkingAPI

async def test_buff_api_stability():
    """测试Buff API的稳定性"""
    print("🔍 测试Buff API稳定性...")
    success_count = 0
    total_requests = 5
    
    async with BuffAPIClient() as buff_client:
        for i in range(1, total_requests + 1):
            try:
                print(f"   测试请求 {i}/{total_requests}...")
                start_time = time.time()
                
                result = await buff_client.get_goods_list(page_num=i, page_size=10)
                
                end_time = time.time()
                request_time = end_time - start_time
                
                if result and 'data' in result:
                    items_count = len(result['data'].get('items', []))
                    success_count += 1
                    print(f"   ✅ 请求{i} 成功 - {items_count}个商品 - 耗时{request_time:.2f}秒")
                else:
                    print(f"   ❌ 请求{i} 失败 - 无有效数据")
                
                # 请求间延迟
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ 请求{i} 异常: {e}")
    
    success_rate = (success_count / total_requests) * 100
    print(f"📊 Buff API成功率: {success_count}/{total_requests} ({success_rate:.1f}%)")
    return success_rate

async def test_youpin_api_stability():
    """测试悠悠有品API的稳定性"""
    print("\n🔍 测试悠悠有品API稳定性...")
    success_count = 0
    total_requests = 5
    
    async with YoupinWorkingAPI() as youpin_client:
        for i in range(1, total_requests + 1):
            try:
                print(f"   测试请求 {i}/{total_requests}...")
                start_time = time.time()
                
                result = await youpin_client.get_market_goods(page_index=i, page_size=10)
                
                end_time = time.time()
                request_time = end_time - start_time
                
                if result and len(result) > 0:
                    success_count += 1
                    print(f"   ✅ 请求{i} 成功 - {len(result)}个商品 - 耗时{request_time:.2f}秒")
                else:
                    print(f"   ❌ 请求{i} 失败 - 无有效数据")
                
                # 请求间延迟
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ 请求{i} 异常: {e}")
    
    success_rate = (success_count / total_requests) * 100
    print(f"📊 悠悠有品API成功率: {success_count}/{total_requests} ({success_rate:.1f}%)")
    return success_rate

async def check_configuration():
    """检查配置状态"""
    print("\n🔧 检查配置状态...")
    
    # 检查Buff配置
    try:
        from token_manager import token_manager
        buff_config = token_manager.get_buff_config()
        
        has_session = bool(buff_config.get("cookies", {}).get("session"))
        has_csrf = bool(buff_config.get("cookies", {}).get("csrf_token"))
        
        print(f"   Buff Session: {'✅' if has_session else '❌'}")
        print(f"   Buff CSRF: {'✅' if has_csrf else '❌'}")
        
    except Exception as e:
        print(f"   ❌ Buff配置检查失败: {e}")
    
    # 检查悠悠有品配置
    try:
        youpin_config = token_manager.get_youpin_config()
        
        has_device_id = bool(youpin_config.get("device_id"))
        has_uk = bool(youpin_config.get("uk"))
        
        print(f"   悠悠有品Device ID: {'✅' if has_device_id else '❌'}")
        print(f"   悠悠有品UK: {'✅' if has_uk else '❌'}")
        
    except Exception as e:
        print(f"   ❌ 悠悠有品配置检查失败: {e}")

async def diagnose_issues():
    """诊断常见问题"""
    print("\n🩺 问题诊断...")
    
    issues = []
    
    # 测试单个请求的详细信息
    print("   📋 详细错误分析:")
    
    try:
        async with BuffAPIClient() as buff_client:
            print("   🔄 测试Buff API详细响应...")
            result = await buff_client.get_goods_list(page_num=1, page_size=1)
            
            if not result:
                issues.append("Buff API返回空结果")
            elif 'error' in str(result).lower():
                issues.append("Buff API返回错误信息")
            elif 'data' not in result:
                issues.append("Buff API响应格式异常")
            else:
                print("   ✅ Buff API响应格式正常")
                
    except Exception as e:
        issues.append(f"Buff API连接异常: {str(e)[:100]}")
    
    try:
        async with YoupinWorkingAPI() as youpin_client:
            print("   🔄 测试悠悠有品API详细响应...")
            result = await youpin_client.get_market_goods(page_index=1, page_size=1)
            
            if not result:
                issues.append("悠悠有品API返回空结果")
            elif not isinstance(result, list):
                issues.append("悠悠有品API响应格式异常")
            else:
                print("   ✅ 悠悠有品API响应格式正常")
                
    except Exception as e:
        issues.append(f"悠悠有品API连接异常: {str(e)[:100]}")
    
    # 输出诊断结果
    if issues:
        print(f"\n❌ 发现以下问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print(f"\n✅ 未发现明显问题")
    
    return issues

async def suggest_solutions(issues):
    """建议解决方案"""
    print(f"\n💡 解决方案建议:")
    
    if not issues:
        print("   🎉 系统运行正常！")
        return
    
    solutions = []
    
    for issue in issues:
        if "buff" in issue.lower() and "异常" in issue:
            solutions.append("🔧 Buff API问题 - 建议更新Buff Token和Cookies")
        elif "buff" in issue.lower() and "空结果" in issue:
            solutions.append("🔧 Buff认证问题 - 检查session和csrf_token是否有效")
        elif "悠悠有品" in issue and "异常" in issue:
            solutions.append("🔧 悠悠有品API问题 - 建议更新device_id和uk参数")
        elif "悠悠有品" in issue and "空结果" in issue:
            solutions.append("🔧 悠悠有品认证问题 - 检查认证参数是否有效")
    
    # 通用解决方案
    solutions.extend([
        "🌐 检查网络连接是否稳定",
        "⏰ 降低请求频率，增加延迟时间",
        "🔄 重启应用程序清理连接池",
        "📝 更新API认证信息"
    ])
    
    for i, solution in enumerate(solutions, 1):
        print(f"   {i}. {solution}")

async def main():
    """主函数"""
    print("🚨 API接口失败率诊断工具")
    print("="*60)
    
    # 检查配置
    await check_configuration()
    
    # 测试API稳定性
    buff_success_rate = await test_buff_api_stability()
    youpin_success_rate = await test_youpin_api_stability()
    
    # 诊断问题
    issues = await diagnose_issues()
    
    # 总体评估
    print(f"\n📊 总体评估:")
    print(f"   Buff API成功率: {buff_success_rate:.1f}%")
    print(f"   悠悠有品API成功率: {youpin_success_rate:.1f}%")
    
    avg_success_rate = (buff_success_rate + youpin_success_rate) / 2
    if avg_success_rate >= 80:
        print(f"   🟢 整体状态: 良好 ({avg_success_rate:.1f}%)")
    elif avg_success_rate >= 50:
        print(f"   🟡 整体状态: 一般 ({avg_success_rate:.1f}%)")
    else:
        print(f"   🔴 整体状态: 较差 ({avg_success_rate:.1f}%)")
    
    # 建议解决方案
    await suggest_solutions(issues)

if __name__ == "__main__":
    asyncio.run(main()) 