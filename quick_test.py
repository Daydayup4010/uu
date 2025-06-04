#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速API测试 - 核心接口
"""
import requests
import json

def test_api(url, method="GET", data=None, description=""):
    """快速测试API"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data, timeout=5)
            
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {description} ({response.status_code})")
        
        if response.status_code == 200:
            try:
                resp_data = response.json()
                if 'success' in resp_data:
                    if resp_data['success']:
                        if 'data' in resp_data and isinstance(resp_data['data'], dict):
                            if 'total_count' in resp_data['data']:
                                print(f"   数据总数: {resp_data['data']['total_count']}")
                            if 'items' in resp_data['data']:
                                print(f"   项目数量: {len(resp_data['data']['items'])}")
                        if 'message' in resp_data:
                            print(f"   消息: {resp_data['message']}")
                    else:
                        print(f"   业务失败: {resp_data.get('error', '未知错误')}")
            except:
                print("   返回非JSON数据")
        else:
            print(f"   错误: {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ {description} - 连接失败: {e}")

if __name__ == "__main__":
    base = "http://127.0.0.1:5000"
    
    print("🚀 CS:GO价差分析系统 - 快速接口测试")
    print("=" * 60)
    
    # 核心GET接口
    print("\n📋 基础接口:")
    test_api(f"{base}/", description="主页")
    test_api(f"{base}/api/status", description="系统状态")
    test_api(f"{base}/api/data", description="价差数据")
    test_api(f"{base}/api/items", description="差价饰品列表")
    test_api(f"{base}/api/settings", description="获取设置")
    
    # Token管理
    print("\n🔑 Token管理:")
    test_api(f"{base}/api/tokens/status", description="Token状态")
    
    # POST接口（简单测试）
    print("\n🔧 功能接口:")
    test_api(f"{base}/api/force_update", "POST", description="强制更新")
    test_api(f"{base}/api/settings", "POST", {"threshold": 20.0}, "设置阈值")
    
    # 错误接口（预期404）
    print("\n❌ 错误测试:")
    test_api(f"{base}/api/statistics", description="不存在的接口（预期404）")
    test_api(f"{base}/api/nonexistent", description="无效接口（预期404）")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！绿色表示正常，红色表示有问题")
    
    # 显示当前系统状态
    print("\n📊 当前系统状态:")
    try:
        response = requests.get(f"{base}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                status_info = data['data']
                print(f"   监控状态: {'运行中' if status_info['is_running'] else '已停止'}")
                print(f"   价差阈值: {status_info['threshold']} 元")
                print(f"   饰品数量: {status_info['current_items_count']} 个")
                print(f"   最后更新: {status_info['last_update'] or '无'}")
    except:
        print("   无法获取状态信息") 