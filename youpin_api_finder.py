#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品API发现工具

通过分析网页源码和网络请求来找到真正的API接口
"""

import asyncio
import aiohttp
import json
import re
import logging
from typing import Optional, Dict, List, Set
from urllib.parse import quote, urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YoupinAPIFinder:
    """悠悠有品API发现器"""
    
    def __init__(self):
        self.base_url = "https://www.youpin898.com"
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def discover_api_endpoints(self):
        """发现API端点"""
        print("🔍 开始发现悠悠有品的真实API接口...")
        print("="*80)
        
        # 1. 分析主页
        print("\n📄 第一步：分析主页源码")
        main_page_apis = await self._analyze_main_page()
        
        # 2. 分析搜索页面
        print("\n🔍 第二步：分析搜索页面")
        search_page_apis = await self._analyze_search_page()
        
        # 3. 分析商品页面
        print("\n📦 第三步：分析商品列表页面")
        goods_page_apis = await self._analyze_goods_page()
        
        # 4. 尝试常见的API模式
        print("\n🎯 第四步：测试常见API模式")
        common_apis = await self._test_common_api_patterns()
        
        # 合并所有发现的API
        all_apis = set()
        all_apis.update(main_page_apis)
        all_apis.update(search_page_apis)
        all_apis.update(goods_page_apis)
        all_apis.update(common_apis)
        
        print(f"\n🎉 总结：发现了 {len(all_apis)} 个可能的API接口")
        for api in sorted(all_apis):
            print(f"   ✅ {api}")
        
        return list(all_apis)
    
    async def _analyze_main_page(self) -> Set[str]:
        """分析主页源码"""
        apis = set()
        
        try:
            print(f"   📤 请求主页: {self.base_url}")
            async with self.session.get(self.base_url) as response:
                print(f"   📥 响应状态: {response.status}")
                
                if response.status == 200:
                    html = await response.text()
                    print(f"   📄 页面长度: {len(html)} 字符")
                    
                    # 提取JavaScript中的API调用
                    found_apis = self._extract_apis_from_html(html)
                    apis.update(found_apis)
                    
                    if found_apis:
                        print(f"   🎯 在主页发现 {len(found_apis)} 个API:")
                        for api in sorted(found_apis):
                            print(f"      - {api}")
                    else:
                        print(f"   ⚠️ 主页未发现明显的API调用")
                else:
                    print(f"   ❌ 无法访问主页: {response.status}")
                    
        except Exception as e:
            print(f"   ❌ 分析主页失败: {e}")
        
        return apis
    
    async def _analyze_search_page(self) -> Set[str]:
        """分析搜索页面"""
        apis = set()
        
        try:
            search_urls = [
                f"{self.base_url}/search?keyword=AK-47",
                f"{self.base_url}/search?q=AK-47",
                f"{self.base_url}/goods?search=AK-47",
                f"{self.base_url}/market?keyword=AK-47",
            ]
            
            for url in search_urls:
                try:
                    print(f"   📤 请求搜索页: {url}")
                    async with self.session.get(url) as response:
                        print(f"   📥 响应状态: {response.status}")
                        
                        if response.status == 200:
                            html = await response.text()
                            found_apis = self._extract_apis_from_html(html)
                            apis.update(found_apis)
                            
                            if found_apis:
                                print(f"   🎯 发现API: {found_apis}")
                                
                except Exception as e:
                    print(f"   ⚠️ 请求失败: {e}")
                    
        except Exception as e:
            print(f"   ❌ 分析搜索页失败: {e}")
        
        return apis
    
    async def _analyze_goods_page(self) -> Set[str]:
        """分析商品页面"""
        apis = set()
        
        try:
            goods_urls = [
                f"{self.base_url}/goods",
                f"{self.base_url}/market",
                f"{self.base_url}/items",
                f"{self.base_url}/csgo",
            ]
            
            for url in goods_urls:
                try:
                    print(f"   📤 请求商品页: {url}")
                    async with self.session.get(url) as response:
                        print(f"   📥 响应状态: {response.status}")
                        
                        if response.status == 200:
                            html = await response.text()
                            found_apis = self._extract_apis_from_html(html)
                            apis.update(found_apis)
                            
                except Exception as e:
                    print(f"   ⚠️ 请求失败: {e}")
                    
        except Exception as e:
            print(f"   ❌ 分析商品页失败: {e}")
        
        return apis
    
    async def _test_common_api_patterns(self) -> Set[str]:
        """测试常见的API模式"""
        apis = set()
        
        # 常见的API路径模式
        api_patterns = [
            # 不同的API版本
            "/api/v1/search",
            "/api/v2/search", 
            "/api/v1/goods",
            "/api/v2/goods",
            "/api/v1/market",
            "/api/v2/market",
            
            # RESTful API
            "/api/search",
            "/api/goods",
            "/api/market",
            "/api/items",
            "/api/products",
            
            # 带游戏ID的API
            "/api/csgo/search",
            "/api/csgo/goods",
            "/api/steam/search",
            
            # 移动端API
            "/mobile/api/search",
            "/m/api/search",
            "/app/api/search",
            
            # 内部API
            "/internal/api/search",
            "/ajax/search",
            "/xhr/search",
        ]
        
        print(f"   🧪 测试 {len(api_patterns)} 个常见API模式...")
        
        for pattern in api_patterns:
            try:
                url = f"{self.base_url}{pattern}"
                params = {'keyword': 'AK-47', 'q': 'test'}
                
                async with self.session.get(url, params=params) as response:
                    content_type = response.headers.get('content-type', '')
                    
                    if response.status == 200 and 'json' in content_type:
                        apis.add(url)
                        print(f"   ✅ 发现有效API: {pattern}")
                        
                        # 尝试读取响应
                        try:
                            data = await response.json()
                            print(f"      📊 响应数据类型: {type(data)}")
                            if isinstance(data, dict):
                                print(f"      📊 响应字段: {list(data.keys())[:5]}")
                        except:
                            pass
                            
                    elif response.status == 200:
                        # 即使不是JSON，也可能是有用的端点
                        print(f"   📄 端点存在但非JSON: {pattern} ({content_type})")
                        
            except Exception as e:
                # 忽略连接错误，继续测试其他端点
                pass
        
        return apis
    
    def _extract_apis_from_html(self, html: str) -> Set[str]:
        """从HTML中提取API调用"""
        apis = set()
        
        # API调用的正则表达式模式
        api_patterns = [
            # fetch调用
            r'fetch\([\'"]([^\'"\s]+)[\'"]',
            r'fetch\s*\(\s*[\'"]([^\'"\s]+)[\'"]',
            
            # axios调用
            r'axios\.get\([\'"]([^\'"\s]+)[\'"]',
            r'axios\.post\([\'"]([^\'"\s]+)[\'"]',
            r'axios\([\'"]([^\'"\s]+)[\'"]',
            
            # jQuery AJAX
            r'\$\.get\([\'"]([^\'"\s]+)[\'"]',
            r'\$\.post\([\'"]([^\'"\s]+)[\'"]',
            r'\$\.ajax\([^{]*[\'"]url[\'"]:\s*[\'"]([^\'"\s]+)[\'"]',
            
            # XMLHttpRequest
            r'\.open\([\'"]GET[\'"],\s*[\'"]([^\'"\s]+)[\'"]',
            r'\.open\([\'"]POST[\'"],\s*[\'"]([^\'"\s]+)[\'"]',
            
            # 一般的URL模式
            r'[\'"]([^\'"\s]*api[^\'"\s]*)[\'"]',
            r'[\'"]([^\'"\s]*/search[^\'"\s]*)[\'"]',
            r'[\'"]([^\'"\s]*/goods[^\'"\s]*)[\'"]',
            r'[\'"]([^\'"\s]*/market[^\'"\s]*)[\'"]',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                # 过滤掉无效的URL
                if self._is_valid_api_url(match):
                    # 转换为绝对URL
                    absolute_url = urljoin(self.base_url, match)
                    apis.add(absolute_url)
        
        return apis
    
    def _is_valid_api_url(self, url: str) -> bool:
        """检查是否是有效的API URL"""
        # 排除无效的URL
        invalid_patterns = [
            r'^#',  # 锚点链接
            r'^javascript:',  # JavaScript代码
            r'^mailto:',  # 邮件链接
            r'^tel:',  # 电话链接
            r'\.(css|js|png|jpg|jpeg|gif|ico|svg)$',  # 静态资源
            r'^/static/',  # 静态文件路径
            r'^/assets/',  # 资源文件路径
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 必须包含这些关键词之一
        api_keywords = ['api', 'search', 'goods', 'market', 'ajax', 'xhr']
        return any(keyword in url.lower() for keyword in api_keywords)

async def main():
    """主函数"""
    print("🎯 悠悠有品API发现工具")
    print("="*80)
    
    async with YoupinAPIFinder() as finder:
        apis = await finder.discover_api_endpoints()
        
        if apis:
            print(f"\n🎉 成功发现 {len(apis)} 个可能的API接口！")
            print("\n📝 建议接下来：")
            print("1. 使用这些API接口更新 youpin_api_client.py")
            print("2. 测试每个接口的参数和响应格式")
            print("3. 找到真正可用的价格查询接口")
        else:
            print(f"\n😔 未发现任何API接口")
            print("📝 建议：")
            print("1. 使用浏览器开发者工具手动分析网络请求")
            print("2. 查看网站的JavaScript源码")
            print("3. 可能需要模拟更复杂的用户行为")

if __name__ == "__main__":
    asyncio.run(main()) 