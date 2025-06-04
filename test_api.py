#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的API测试脚本
"""
import requests
import json

def test_api_endpoint(url, description):
    """测试API端点"""
    try:
        response = requests.get(url, timeout=10)
        print(f"\n{description}")
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
                print("✅ 成功")
            except:
                print(f"响应文本: {response.text[:200]}...")
                print("✅ 响应成功但不是JSON")
        else:
            print(f"错误: {response.text}")
            print("❌ 失败")
            
    except Exception as e:
        print(f"\n{description}")
        print(f"URL: {url}")
        print(f"错误: {e}")
        print("❌ 连接失败")

if __name__ == "__main__":
    base_url = "http://127.0.0.1:5000"
    
    print("🔧 CS:GO价差分析系统 API 测试")
    print("=" * 50)
    
    # 测试各个端点
    endpoints = [
        ("/", "主页"),
        ("/api/status", "系统状态"),
        ("/api/data", "价差数据"),
        ("/api/items", "差价饰品列表"),
        ("/api/tokens/status", "Token状态")
    ]
    
    for endpoint, description in endpoints:
        test_api_endpoint(f"{base_url}{endpoint}", description)
    
    print("\n" + "=" * 50)
    print("测试完成！") 