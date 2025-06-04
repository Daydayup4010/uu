#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端与后端价格区间功能集成
"""

import requests
import json
import time

def test_api_endpoints():
    """测试API端点"""
    base_url = "http://localhost:5000"  # 假设API服务器运行在5000端口
    
    print("🧪 测试前端与后端集成功能")
    print("="*50)
    
    # 测试获取当前价格区间
    print("\n1️⃣ 测试获取价格区间")
    try:
        response = requests.get(f"{base_url}/api/price_range")
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 获取价格区间失败: {e}")
    
    # 测试设置价格区间
    print("\n2️⃣ 测试设置价格区间")
    try:
        data = {"min": 3.0, "max": 5.0}
        response = requests.post(
            f"{base_url}/api/price_range",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 设置价格区间失败: {e}")
    
    # 测试获取设置
    print("\n3️⃣ 测试获取设置")
    try:
        response = requests.get(f"{base_url}/api/settings")
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 获取设置失败: {e}")
    
    # 测试更新设置
    print("\n4️⃣ 测试更新设置")
    try:
        data = {
            "price_min": 5.0,
            "price_max": 10.0,
            "max_output_items": 500,
            "threshold": 15.0
        }
        response = requests.post(
            f"{base_url}/api/settings",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 更新设置失败: {e}")
    
    # 测试获取数据
    print("\n5️⃣ 测试获取数据")
    try:
        response = requests.get(f"{base_url}/api/data")
        result = response.json()
        print(f"状态码: {response.status_code}")
        if result.get('success'):
            items_count = len(result.get('data', {}).get('items', []))
            print(f"成功获取 {items_count} 个商品")
        else:
            print(f"获取数据失败: {result.get('error', '未知错误')}")
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")

def generate_frontend_test_html():
    """生成前端测试页面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>价格区间功能测试</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007cba; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        button:hover { background: #005a87; }
        input, select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
        .result { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px; font-family: monospace; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>🎯 价格区间功能测试</h1>
    
    <div class="test-section">
        <h3>1. 价格区间设置</h3>
        <label>最小价差:</label>
        <input type="number" id="minPrice" value="3" step="0.1">
        <label>最大价差:</label>
        <input type="number" id="maxPrice" value="5" step="0.1">
        <button onclick="setPriceRange()">设置价格区间</button>
        <button onclick="getCurrentRange()">获取当前区间</button>
        <div id="rangeResult" class="result"></div>
    </div>
    
    <div class="test-section">
        <h3>2. 系统设置</h3>
        <label>价差阈值:</label>
        <input type="number" id="threshold" value="20" step="0.1">
        <label>最大输出数量:</label>
        <input type="number" id="maxItems" value="300">
        <button onclick="updateSettings()">更新设置</button>
        <button onclick="getSettings()">获取设置</button>
        <div id="settingsResult" class="result"></div>
    </div>
    
    <div class="test-section">
        <h3>3. 数据获取测试</h3>
        <button onclick="getData()">获取商品数据</button>
        <button onclick="forceUpdate()">强制更新</button>
        <div id="dataResult" class="result"></div>
    </div>

    <script>
        const apiBase = 'http://localhost:5000/api';
        
        async function setPriceRange() {
            const min = parseFloat(document.getElementById('minPrice').value);
            const max = parseFloat(document.getElementById('maxPrice').value);
            
            try {
                const response = await fetch(`${apiBase}/price_range`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ min, max })
                });
                const result = await response.json();
                displayResult('rangeResult', result, response.ok);
            } catch (error) {
                displayResult('rangeResult', { error: error.message }, false);
            }
        }
        
        async function getCurrentRange() {
            try {
                const response = await fetch(`${apiBase}/price_range`);
                const result = await response.json();
                displayResult('rangeResult', result, response.ok);
            } catch (error) {
                displayResult('rangeResult', { error: error.message }, false);
            }
        }
        
        async function updateSettings() {
            const threshold = parseFloat(document.getElementById('threshold').value);
            const maxItems = parseInt(document.getElementById('maxItems').value);
            const min = parseFloat(document.getElementById('minPrice').value);
            const max = parseFloat(document.getElementById('maxPrice').value);
            
            try {
                const response = await fetch(`${apiBase}/settings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        threshold, 
                        max_output_items: maxItems,
                        price_min: min,
                        price_max: max
                    })
                });
                const result = await response.json();
                displayResult('settingsResult', result, response.ok);
            } catch (error) {
                displayResult('settingsResult', { error: error.message }, false);
            }
        }
        
        async function getSettings() {
            try {
                const response = await fetch(`${apiBase}/settings`);
                const result = await response.json();
                displayResult('settingsResult', result, response.ok);
            } catch (error) {
                displayResult('settingsResult', { error: error.message }, false);
            }
        }
        
        async function getData() {
            try {
                const response = await fetch(`${apiBase}/data`);
                const result = await response.json();
                if (result.success && result.data.items) {
                    result.data.items = `[${result.data.items.length} items] - 显示前3个`;
                }
                displayResult('dataResult', result, response.ok);
            } catch (error) {
                displayResult('dataResult', { error: error.message }, false);
            }
        }
        
        async function forceUpdate() {
            try {
                const response = await fetch(`${apiBase}/force_update`, { method: 'POST' });
                const result = await response.json();
                displayResult('dataResult', result, response.ok);
            } catch (error) {
                displayResult('dataResult', { error: error.message }, false);
            }
        }
        
        function displayResult(elementId, result, isSuccess) {
            const element = document.getElementById(elementId);
            element.className = `result ${isSuccess ? 'success' : 'error'}`;
            element.textContent = JSON.stringify(result, null, 2);
        }
        
        // 页面加载时获取当前设置
        window.onload = () => {
            getCurrentRange();
            getSettings();
        };
    </script>
</body>
</html>
    """
    
    with open('frontend_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("📄 已生成前端测试页面: frontend_test.html")
    print("💡 启动API服务器后，在浏览器中打开此文件进行测试")

def main():
    print("🔧 前端后端集成测试工具")
    print("="*40)
    
    # 生成测试页面
    generate_frontend_test_html()
    
    # 提示用户
    print("\n📋 测试步骤:")
    print("1. 启动API服务器: python api.py")
    print("2. 在浏览器中打开 frontend_test.html")
    print("3. 测试各项功能")
    print("4. 检查前端与后端的数据交互")
    
    # 如果API服务器在运行，可以直接测试
    print("\n🚀 如果API服务器已启动，可以直接测试...")
    try:
        test_api_endpoints()
    except Exception as e:
        print(f"⚠️ API服务器可能未启动: {e}")

if __name__ == "__main__":
    main() 