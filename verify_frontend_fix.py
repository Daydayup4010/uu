#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证前端配置获取修复
"""

import json
import webbrowser
import threading
import time
from config import Config
from api import app

def start_test_server():
    """启动测试服务器"""
    print("🚀 启动测试服务器...")
    app.run(host='0.0.0.0', port=8000, debug=False)

def test_apis():
    """测试API接口"""
    print("🔍 测试API接口...")
    
    import requests
    
    try:
        # 测试/api/settings接口
        response = requests.get('http://localhost:8000/api/settings')
        if response.status_code == 200:
            data = response.json()
            print("✅ /api/settings 正常工作")
            if 'data' in data and 'buff_price_range' in data['data']:
                buff_range = data['data']['buff_price_range']
                print(f"   Buff价格区间: {buff_range['min']}元 - {buff_range['max']}元")
            else:
                print("❌ 缺少buff_price_range字段")
        else:
            print(f"❌ /api/settings 返回错误: {response.status_code}")
            
        # 测试/api/buff_price_range接口
        response = requests.get('http://localhost:8000/api/buff_price_range')
        if response.status_code == 200:
            data = response.json()
            print("✅ /api/buff_price_range 正常工作")
            print(f"   当前区间: {data['data']['current_range']}")
        else:
            print(f"❌ /api/buff_price_range 返回错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试API时出错: {e}")

def main():
    print("🧪 验证前端配置获取修复")
    print("=" * 50)
    
    # 显示当前配置
    print(f"📋 当前配置:")
    print(f"  - Buff价格区间: {Config.BUFF_PRICE_MIN}元 - {Config.BUFF_PRICE_MAX}元")
    print(f"  - 价差区间: {Config.PRICE_DIFF_MIN}元 - {Config.PRICE_DIFF_MAX}元")
    print()
    
    # 启动服务器（在后台线程）
    server_thread = threading.Thread(target=start_test_server)
    server_thread.daemon = True
    server_thread.start()
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(3)
    
    # 测试API
    test_apis()
    
    # 打开前端页面
    print("\n🌐 打开前端页面进行测试...")
    webbrowser.open('http://localhost:8000')
    
    print("\n📝 测试步骤:")
    print("1. 打开浏览器页面")
    print("2. 点击右上角的'设置'按钮")
    print("3. 查看'Buff价格筛选区间'是否正确显示当前值")
    print("4. 尝试修改Buff价格区间并保存")
    print("5. 确认修改后的值是否正确显示")
    
    print("\n🔍 如果Buff价格区间输入框为空，说明前端获取配置有问题")
    print("如果能正确显示当前值，说明修复成功！")
    
    print("\n按Enter键退出...")
    input()

if __name__ == "__main__":
    main() 