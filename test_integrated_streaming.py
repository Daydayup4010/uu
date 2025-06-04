#!/usr/bin/env python3
"""
测试集成后的流式分析功能
"""

import requests
import json
import time

def test_incremental_analysis():
    """测试增量分析接口"""
    print("🚀 测试增量分析接口...")
    
    url = "http://localhost:5000/api/analyze_incremental"
    
    # 测试立即返回缓存数据
    response = requests.post(url, json={"force_refresh": False})
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print(f"✅ 增量分析成功！")
            print(f"   缓存数据: {result['data']['cached']}")
            print(f"   商品数量: {len(result['data']['items'])}")
            print(f"   后台更新: {result.get('background_update', False)}")
        else:
            print(f"❌ 增量分析失败: {result.get('error', '未知错误')}")
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")

def test_streaming_analysis():
    """测试流式分析接口"""
    print("\n🌊 测试流式分析接口...")
    
    url = "http://localhost:5000/api/stream_analyze"
    
    try:
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            print("✅ 流式连接成功，开始接收数据...")
            
            count = 0
            for line in response.iter_lines():
                if line:
                    try:
                        # 解析SSE格式
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # 移除 'data: ' 前缀
                            data = json.loads(data_str)
                            
                            print(f"📦 收到数据: {data.get('type', 'unknown')} - {data.get('message', '')}")
                            
                            if data.get('type') == 'completed':
                                print("🎉 流式分析完成!")
                                break
                                
                            count += 1
                            if count > 10:  # 限制输出数量
                                print("⏸️  停止测试（收到足够数据）")
                                break
                                
                    except json.JSONDecodeError:
                        continue
                        
        else:
            print(f"❌ 流式请求失败，状态码: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接错误: {e}")

def test_main_page():
    """测试主页面可访问性"""
    print("\n🏠 测试主页面...")
    
    try:
        response = requests.get("http://localhost:5000/")
        
        if response.status_code == 200:
            # 检查是否包含流式分析相关代码
            content = response.text
            
            if "startStreamingUpdate" in content:
                print("✅ 主页面包含流式分析功能")
            else:
                print("⚠️  主页面未包含流式分析功能")
                
            if "流式分析" in content or "streaming" in content.lower():
                print("✅ 页面包含流式分析相关内容")
            else:
                print("⚠️  页面未包含流式分析UI")
                
        else:
            print(f"❌ 主页面访问失败，状态码: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接错误: {e}")

if __name__ == "__main__":
    print("🔍 开始测试集成后的流式分析功能...")
    print("=" * 50)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(3)
    
    # 执行测试
    test_main_page()
    test_incremental_analysis()
    # test_streaming_analysis()  # 注释掉，避免长时间运行
    
    print("\n" + "=" * 50)
    print("✨ 测试完成！请访问 http://localhost:5000 查看集成后的功能")
    print("💡 点击'刷新数据'按钮将启动流式分析") 