#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悠悠有品API调试版本

查看API返回的实际数据结构和商品信息
"""

import asyncio
import aiohttp
import json
import time
from typing import Optional, Dict, List

class YoupinDebugAPI:
    """悠悠有品调试API客户端"""
    
    def __init__(self):
        self.api_base = "https://api.youpin898.com"
        self.web_base = "https://www.youpin898.com"
        self.session = None
        
        # 设备信息
        self.device_id = "5b38ebeb-5a5b-4b1a-afe9-b51edbbb8e01"
        self.device_uk = "5FL1Llbg5qN4z5LjXWo7VlMewPJ7hWEHtwHQpvWQToDNErV6KwbpSj6JBBCjogH1L"
        self.uk = "5FEvkZD2PSMLMTtE0BqOfidTtuoaX9HWBIze4zzFxfdXrsajaPWS4yY5ay96BuX1M"
        self.b3 = "833f3214b9b04819a399c94ed1fab7af-2a9cab244348658f-1"
        
        # 请求头
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'app-version': '5.26.0',
            'apptype': '1',
            'appversion': '5.26.0',
            'b3': self.b3,
            'content-type': 'application/json',
            'deviceid': self.device_id,
            'deviceuk': self.device_uk,
            'origin': self.web_base,
            'platform': 'pc',
            'referer': f'{self.web_base}/',
            'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'secret-v': 'h5_v1',
            'traceparent': f'00-{self.b3.split("-")[0]}-{self.b3.split("-")[1]}-01',
            'uk': self.uk,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0'
        }
        
        self.last_request_time = 0
        self.min_interval = 3.0  # 3秒间隔避免频率限制
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=3)
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
    
    async def _rate_limit(self):
        """频率控制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            print(f"   ⏱️ 等待 {sleep_time:.1f} 秒...")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def debug_api_response(self):
        """调试API响应"""
        print("🔍 调试悠悠有品API响应")
        print("="*80)
        
        await self._rate_limit()
        
        try:
            url = f"{self.api_base}/api/homepage/pc/goods/market/querySaleTemplate"
            
            payload = {
                "listSortType": 0,
                "sortType": 0,
                "pageSize": 10,  # 只获取10个商品进行调试
                "pageIndex": 1
            }
            
            print(f"📤 请求URL: {url}")
            print(f"📋 请求数据: {payload}")
            
            async with self.session.post(url, json=payload) as response:
                print(f"📥 响应状态: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 成功获取JSON数据")
                    
                    # 打印完整的响应结构
                    print(f"\n📊 完整响应结构:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000] + "...")
                    
                    # 分析数据结构
                    self._analyze_response_structure(data)
                    
                    return data
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 请求失败: {response.status}")
                    print(f"📄 错误内容: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def _analyze_response_structure(self, data: Dict):
        """分析响应数据结构"""
        print(f"\n🔍 分析响应数据结构:")
        print(f"   📊 顶级字段: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        
        if isinstance(data, dict):
            # 查找商品数据
            goods_found = False
            
            for key, value in data.items():
                print(f"   📋 字段 '{key}': {type(value)}")
                
                if isinstance(value, list):
                    print(f"      📝 列表长度: {len(value)}")
                    if len(value) > 0:
                        print(f"      📝 第一个元素类型: {type(value[0])}")
                        if isinstance(value[0], dict):
                            print(f"      📝 第一个元素字段: {list(value[0].keys())}")
                            self._show_sample_item(value[0])
                            goods_found = True
                
                elif isinstance(value, dict):
                    print(f"      📝 字典字段: {list(value.keys())}")
                    
                    # 检查是否包含商品列表
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, list) and len(sub_value) > 0:
                            print(f"         📋 子字段 '{sub_key}': 列表长度 {len(sub_value)}")
                            if isinstance(sub_value[0], dict):
                                print(f"         📝 商品字段: {list(sub_value[0].keys())}")
                                self._show_sample_item(sub_value[0])
                                goods_found = True
                                break
            
            if not goods_found:
                print(f"   ⚠️ 未找到明显的商品列表数据")
    
    def _show_sample_item(self, item: Dict):
        """显示示例商品信息"""
        print(f"\n📦 示例商品信息:")
        
        # 显示所有字段
        for key, value in item.items():
            if isinstance(value, (str, int, float)):
                print(f"   {key}: {value}")
            else:
                print(f"   {key}: {type(value)}")
        
        # 尝试提取关键信息
        name = item.get('name', item.get('title', item.get('goods_name', '未知')))
        price = item.get('price', item.get('sell_price', item.get('current_price', '未知')))
        
        print(f"\n🎯 关键信息:")
        print(f"   商品名称: {name}")
        print(f"   价格: {price}")

async def main():
    """主函数"""
    print("🎯 悠悠有品API调试工具")
    print("="*80)
    
    async with YoupinDebugAPI() as client:
        data = await client.debug_api_response()
        
        if data:
            print(f"\n✅ 调试完成！")
            print(f"💡 现在我们知道了API的真实数据结构")
        else:
            print(f"\n❌ 调试失败")

if __name__ == "__main__":
    asyncio.run(main()) 