#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口分析工具

分析Buff和悠悠有品的API接口，用于直接获取数据
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuffAPIAnalyzer:
    """Buff API分析器"""
    
    def __init__(self):
        self.base_url = "https://buff.163.com"
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """设置请求会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'{self.base_url}/market/csgo',
            'X-Requested-With': 'XMLHttpRequest',
        })
    
    def discover_api_endpoints(self):
        """发现API端点"""
        print("🔍 分析Buff的API接口...")
        
        # 常见的API端点模式
        api_patterns = [
            "/api/market/goods",
            "/api/market/csgo",
            "/api/goods/list",
            "/api/market/search",
            "/market/goods",
            "/goods",
        ]
        
        for pattern in api_patterns:
            try:
                url = f"{self.base_url}{pattern}"
                response = self.session.get(url, timeout=5)
                
                print(f"   {pattern}: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"      ✅ JSON响应，包含 {len(data)} 个字段")
                        if 'data' in data:
                            print(f"      📊 data字段类型: {type(data['data'])}")
                    except:
                        print(f"      📄 HTML响应，长度: {len(response.content)}")
                        
            except Exception as e:
                print(f"   {pattern}: ❌ {e}")
    
    def test_goods_api(self, page: int = 1, limit: int = 20):
        """测试商品API"""
        print(f"\n🔍 测试Buff商品API（第{page}页，每页{limit}条）...")
        
        # 尝试几种可能的API格式
        api_urls = [
            f"{self.base_url}/api/market/goods?game=csgo&page_num={page}&page_size={limit}",
            f"{self.base_url}/market/goods?game=csgo&page_num={page}&page_size={limit}",
            f"{self.base_url}/api/market/csgo/goods?page={page}&limit={limit}",
            f"{self.base_url}/api/goods?game=csgo&page={page}&limit={limit}",
        ]
        
        for url in api_urls:
            try:
                print(f"   尝试: {url}")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ 成功！响应结构:")
                        print(f"      状态码: {data.get('code', 'N/A')}")
                        print(f"      消息: {data.get('msg', data.get('message', 'N/A'))}")
                        
                        if 'data' in data:
                            items = data['data']
                            if isinstance(items, dict) and 'items' in items:
                                items = items['items']
                            elif isinstance(items, dict) and 'goods' in items:
                                items = items['goods']
                            
                            if isinstance(items, list) and len(items) > 0:
                                print(f"      📦 找到 {len(items)} 个商品")
                                
                                # 显示第一个商品的结构
                                first_item = items[0]
                                print(f"      📋 商品字段: {list(first_item.keys())}")
                                
                                return url, data
                        
                    except json.JSONDecodeError:
                        print(f"   ❌ 非JSON响应")
                else:
                    print(f"   ❌ 状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 错误: {e}")
        
        return None, None
    
    def search_specific_item(self, keyword: str = "AK-47"):
        """搜索特定商品"""
        print(f"\n🔍 搜索商品: {keyword}")
        
        search_urls = [
            f"{self.base_url}/api/market/search?game=csgo&keyword={keyword}",
            f"{self.base_url}/market/search?game=csgo&keyword={keyword}",
            f"{self.base_url}/api/search?keyword={keyword}&game=csgo",
        ]
        
        for url in search_urls:
            try:
                print(f"   尝试: {url}")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ 搜索成功！")
                        return url, data
                    except:
                        print(f"   ❌ 非JSON响应")
                        
            except Exception as e:
                print(f"   ❌ 错误: {e}")
        
        return None, None

def analyze_network_requests():
    """分析网络请求"""
    print("📡 API接口分析建议:")
    print("1. 打开Chrome浏览器，访问 https://buff.163.com/market/csgo")
    print("2. 打开开发者工具（F12）-> Network标签")
    print("3. 刷新页面，查看XHR/Fetch请求")
    print("4. 查找包含商品数据的API请求")
    print("5. 复制请求URL和参数")
    print()
    print("🔍 常见的API特征:")
    print("- URL包含 /api/ 路径")
    print("- 响应类型为 application/json")
    print("- 请求参数包含 page、limit、game等")
    print("- 响应数据包含商品列表")

def main():
    """主函数"""
    print("🎯 Buff API接口分析工具")
    print("="*50)
    
    analyzer = BuffAPIAnalyzer()
    
    # 1. 发现API端点
    analyzer.discover_api_endpoints()
    
    # 2. 测试商品API
    api_url, data = analyzer.test_goods_api()
    
    if api_url:
        print(f"\n🎉 找到可用的API: {api_url}")
        
        # 保存API信息
        api_info = {
            'url': api_url,
            'method': 'GET',
            'headers': dict(analyzer.session.headers),
            'sample_response': data
        }
        
        with open('buff_api_info.json', 'w', encoding='utf-8') as f:
            json.dump(api_info, f, ensure_ascii=False, indent=2)
        print("📄 API信息已保存到 buff_api_info.json")
    
    # 3. 搜索测试
    search_url, search_data = analyzer.search_specific_item()
    
    # 4. 提供手动分析建议
    print("\n" + "="*50)
    analyze_network_requests()

if __name__ == "__main__":
    main() 