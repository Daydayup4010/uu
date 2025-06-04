#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品API接口分析工具

分析悠悠有品的API接口，用于获取真实价格数据
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional
import re
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YoupinAPIAnalyzer:
    """悠悠有品API分析器"""
    
    def __init__(self):
        self.base_url = "https://www.youpin898.com"
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """设置请求会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'{self.base_url}/',
            'X-Requested-With': 'XMLHttpRequest',
        })
    
    def discover_api_endpoints(self):
        """发现API端点"""
        print("🔍 分析悠悠有品的API接口...")
        
        # 常见的API端点模式
        api_patterns = [
            "/api/search",
            "/api/goods",
            "/api/market/goods",
            "/api/product/search",
            "/search/api",
            "/goods/api",
            "/api/v1/search",
            "/api/v1/goods",
            "/ajax/search",
            "/ajax/goods",
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
                    except:
                        print(f"      📄 HTML响应，长度: {len(response.content)}")
                        
            except Exception as e:
                print(f"   {pattern}: ❌ {e}")
    
    def test_search_api(self, keyword: str = "AK-47"):
        """测试搜索API"""
        print(f"\n🔍 测试悠悠有品搜索API（关键词: {keyword}）...")
        
        # 尝试几种可能的搜索API格式
        api_urls = [
            f"{self.base_url}/api/search?keyword={quote(keyword)}",
            f"{self.base_url}/search/api?q={quote(keyword)}",
            f"{self.base_url}/api/goods/search?name={quote(keyword)}",
            f"{self.base_url}/ajax/search?keyword={quote(keyword)}",
            f"{self.base_url}/api/v1/search?keyword={quote(keyword)}",
            f"{self.base_url}/search?keyword={quote(keyword)}&format=json",
        ]
        
        for url in api_urls:
            try:
                print(f"   尝试: {url}")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ 成功！响应结构:")
                        print(f"      状态: {data.get('status', data.get('code', 'N/A'))}")
                        print(f"      消息: {data.get('message', data.get('msg', 'N/A'))}")
                        
                        # 查找商品数据
                        items = None
                        for key in ['data', 'items', 'goods', 'products', 'result']:
                            if key in data:
                                items = data[key]
                                break
                        
                        if items and isinstance(items, list) and len(items) > 0:
                            print(f"      📦 找到 {len(items)} 个商品")
                            first_item = items[0]
                            print(f"      📋 商品字段: {list(first_item.keys())}")
                            return url, data
                        
                    except json.JSONDecodeError:
                        print(f"   ❌ 非JSON响应")
                        # 尝试从HTML中提取数据
                        html_content = response.text
                        if self._extract_from_html(html_content, keyword):
                            return url, {'html': True}
                else:
                    print(f"   ❌ 状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 错误: {e}")
        
        return None, None
    
    def _extract_from_html(self, html_content: str, keyword: str) -> bool:
        """从HTML中提取商品信息"""
        try:
            # 查找常见的价格模式
            price_patterns = [
                r'¥(\d+\.?\d*)',
                r'price["\']:\s*(\d+\.?\d*)',
                r'sell_price["\']:\s*(\d+\.?\d*)',
                r'"price":(\d+\.?\d*)',
            ]
            
            found_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                found_prices.extend(matches)
            
            if found_prices:
                print(f"      💰 从HTML中找到价格: {found_prices[:5]}")
                return True
            
            # 查找商品名称
            if keyword.lower() in html_content.lower():
                print(f"      📦 HTML中包含商品信息")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"解析HTML失败: {e}")
            return False
    
    def analyze_page_structure(self, keyword: str = "AK-47"):
        """分析页面结构"""
        print(f"\n🔍 分析悠悠有品页面结构...")
        
        try:
            # 访问搜索页面
            search_url = f"{self.base_url}/search"
            params = {'keyword': keyword}
            
            response = self.session.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # 查找可能的API调用
                api_patterns = [
                    r'\.get\(["\']([^"\']*api[^"\']*)["\']',
                    r'\.post\(["\']([^"\']*api[^"\']*)["\']',
                    r'ajax\(["\']([^"\']*)["\']',
                    r'fetch\(["\']([^"\']*api[^"\']*)["\']',
                ]
                
                found_apis = []
                for pattern in api_patterns:
                    matches = re.findall(pattern, html_content)
                    found_apis.extend(matches)
                
                if found_apis:
                    print(f"   📡 发现可能的API端点:")
                    for api in set(found_apis)[:10]:
                        print(f"      {api}")
                
                # 查找数据结构
                json_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'window\.__DATA__\s*=\s*({.*?});',
                    r'var\s+data\s*=\s*({.*?});',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, html_content, re.DOTALL)
                    if matches:
                        try:
                            data = json.loads(matches[0])
                            print(f"   📊 找到页面数据结构:")
                            print(f"      数据字段: {list(data.keys())[:10]}")
                            return data
                        except:
                            continue
                
                print(f"   📄 页面长度: {len(html_content)} 字符")
                return True
            else:
                print(f"   ❌ 无法访问搜索页面: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 分析页面结构失败: {e}")
            return False

def main():
    """主函数"""
    print("🎯 悠悠有品API接口分析工具")
    print("="*50)
    
    analyzer = YoupinAPIAnalyzer()
    
    # 1. 发现API端点
    analyzer.discover_api_endpoints()
    
    # 2. 测试搜索API
    api_url, data = analyzer.test_search_api("AK-47")
    
    if api_url:
        print(f"\n🎉 找到可用的API: {api_url}")
    else:
        print(f"\n⚠️ 未找到可用的API接口")
    
    # 3. 分析页面结构
    page_data = analyzer.analyze_page_structure("AK-47")
    
    # 4. 保存分析结果
    analysis_result = {
        'api_url': api_url,
        'api_data': data if data and not isinstance(data, dict) or 'html' not in data else None,
        'page_data': page_data if isinstance(page_data, dict) else None,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('youpin_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 分析结果已保存到 youpin_analysis.json")
    
    # 5. 提供建议
    print("\n" + "="*50)
    print("💡 获取悠悠有品真实价格的建议:")
    print("1. 手动分析网站的网络请求（Chrome开发者工具）")
    print("2. 查找AJAX/Fetch请求中的价格数据")
    print("3. 实现对应的API调用")
    print("4. 或者使用网页爬虫解析HTML页面")

if __name__ == "__main__":
    main() 