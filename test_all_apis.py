#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的API测试脚本 - 测试所有接口
"""
import requests
import json
import time

def test_get_endpoint(url, description):
    """测试GET端点"""
    try:
        response = requests.get(url, timeout=10)
        print(f"\n📡 {description}")
        print(f"   URL: {url}")
        print(f"   方法: GET")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and 'success' in data:
                    status = "✅ 成功" if data['success'] else "⚠️ 业务失败"
                    print(f"   响应: {status}")
                    if 'message' in data:
                        print(f"   消息: {data['message']}")
                    if 'data' in data and isinstance(data['data'], dict):
                        print(f"   数据字段: {list(data['data'].keys())}")
                        if 'total_count' in data['data']:
                            print(f"   总数: {data['data']['total_count']}")
                else:
                    print(f"   响应: ✅ 成功 (非标准格式)")
                print(f"   详情: {json.dumps(data, ensure_ascii=False)[:150]}...")
            except:
                print(f"   响应: ✅ 成功 (HTML/文本格式)")
                print(f"   内容: {response.text[:100]}...")
        else:
            print(f"   响应: ❌ 失败")
            print(f"   错误: {response.text[:200]}")
            
    except Exception as e:
        print(f"\n📡 {description}")
        print(f"   URL: {url}")
        print(f"   方法: GET")
        print(f"   错误: {e}")
        print(f"   状态: ❌ 连接失败")

def test_post_endpoint(url, description, data=None):
    """测试POST端点"""
    try:
        headers = {'Content-Type': 'application/json'} if data else {}
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"\n📡 {description}")
        print(f"   URL: {url}")
        print(f"   方法: POST")
        if data:
            print(f"   数据: {json.dumps(data, ensure_ascii=False)}")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                resp_data = response.json()
                if isinstance(resp_data, dict) and 'success' in resp_data:
                    status = "✅ 成功" if resp_data['success'] else "⚠️ 业务失败"
                    print(f"   响应: {status}")
                    if 'message' in resp_data:
                        print(f"   消息: {resp_data['message']}")
                    if 'data' in resp_data and isinstance(resp_data['data'], dict):
                        print(f"   数据字段: {list(resp_data['data'].keys())}")
                else:
                    print(f"   响应: ✅ 成功 (非标准格式)")
                print(f"   详情: {json.dumps(resp_data, ensure_ascii=False)[:150]}...")
            except:
                print(f"   响应: ✅ 成功 (文本格式)")
                print(f"   内容: {response.text[:100]}...")
        else:
            print(f"   响应: ❌ 失败")
            print(f"   错误: {response.text[:200]}")
            
    except Exception as e:
        print(f"\n📡 {description}")
        print(f"   URL: {url}")
        print(f"   方法: POST")
        print(f"   错误: {e}")
        print(f"   状态: ❌ 连接失败")

if __name__ == "__main__":
    base_url = "http://127.0.0.1:5000"
    
    print("🔧 CS:GO价差分析系统 - 全面API测试")
    print("=" * 80)
    
    # 1. 基础GET接口测试
    print("\n🔵 === 基础接口测试 ===")
    get_endpoints = [
        ("/", "主页"),
        ("/api/status", "系统状态"),
        ("/api/data", "价差数据"),
        ("/api/items", "差价饰品列表"),
        ("/api/settings", "获取设置")
    ]
    
    for endpoint, description in get_endpoints:
        test_get_endpoint(f"{base_url}{endpoint}", description)
        time.sleep(0.5)
    
    # 2. Token管理接口测试
    print("\n🟡 === Token管理接口测试 ===")
    token_endpoints = [
        ("/api/tokens/status", "Token状态"),
        ("/api/tokens/buff", "Buff Token配置"),
        ("/api/tokens/youpin", "悠悠有品Token配置")
    ]
    
    for endpoint, description in token_endpoints:
        test_get_endpoint(f"{base_url}{endpoint}", description)
        time.sleep(0.5)
    
    # 3. POST接口测试
    print("\n🟢 === POST接口测试 ===")
    
    # 测试强制更新
    test_post_endpoint(f"{base_url}/api/force_update", "强制更新数据")
    time.sleep(1)
    
    # 测试设置更新
    test_post_endpoint(
        f"{base_url}/api/settings", 
        "更新价差阈值", 
        {"threshold": 25.0}
    )
    time.sleep(0.5)
    
    # 测试连接测试
    test_post_endpoint(f"{base_url}/api/test/buff", "测试Buff连接")
    time.sleep(1)
    
    test_post_endpoint(f"{base_url}/api/test/youpin", "测试悠悠有品连接")
    time.sleep(1)
    
    # 测试手动分析
    test_post_endpoint(
        f"{base_url}/api/analyze", 
        "触发手动分析", 
        {"max_items": 10}
    )
    time.sleep(2)
    
    # 4. 错误接口测试（确认404）
    print("\n🔴 === 错误接口测试 ===")
    error_endpoints = [
        ("/api/statistics", "统计信息（应该404）"),
        ("/api/nonexistent", "不存在的接口（应该404）"),
        ("/api/items/123", "单个饰品详情（应该404）")
    ]
    
    for endpoint, description in error_endpoints:
        test_get_endpoint(f"{base_url}{endpoint}", description)
        time.sleep(0.5)
    
    # 5. 参数测试
    print("\n🟣 === 参数接口测试 ===")
    
    # 测试带参数的items接口
    param_urls = [
        ("/api/items?limit=5", "限制5个饰品"),
        ("/api/items?limit=100&sort_by=price_diff", "排序和限制")
    ]
    
    for endpoint, description in param_urls:
        test_get_endpoint(f"{base_url}{endpoint}", description)
        time.sleep(0.5)
    
    # 6. 测试Token配置（POST）
    print("\n🟠 === Token配置测试 ===")
    
    # 测试Buff Token配置（示例数据）
    test_post_endpoint(
        f"{base_url}/api/tokens/buff",
        "更新Buff Token（测试数据）",
        {
            "session": "test_session_token",
            "csrf_token": "test_csrf_token",
            "user_agent": "test_user_agent"
        }
    )
    time.sleep(0.5)
    
    # 测试悠悠有品Token配置（示例数据）
    test_post_endpoint(
        f"{base_url}/api/tokens/youpin",
        "更新悠悠有品Token（测试数据）",
        {
            "device_id": "test_device_id",
            "device_uk": "test_device_uk", 
            "uk": "test_uk",
            "b3": "test_b3",
            "authorization": "test_authorization"
        }
    )
    
    print("\n" + "=" * 80)
    print("🎉 全面API测试完成！")
    print("\n📊 测试总结:")
    print("   ✅ 绿色: 接口正常工作")
    print("   ⚠️  黄色: 接口可访问但业务逻辑失败")
    print("   ❌ 红色: 接口无法访问或连接失败")
    print("   🔴 404错误是正常的（表示接口不存在）")
    print("\n💡 提示: 如果某些接口返回空数据，可能是因为:")
    print("   1. 系统刚启动，还没有收集到数据")
    print("   2. Token配置未设置或无效")
    print("   3. 数据正在后台处理中") 