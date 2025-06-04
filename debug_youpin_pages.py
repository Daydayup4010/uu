#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试悠悠有品API后续页面问题
"""

import asyncio
import aiohttp
import json
import time

class YoupinDebugClient:
    """悠悠有品调试客户端"""
    
    def __init__(self):
        self.base_url = "https://api.youpin898.com"
        self.session = None
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            from token_manager import token_manager
            self.youpin_config = token_manager.get_youpin_config()
        except Exception as e:
            print(f"加载悠悠有品配置失败: {e}")
            self.youpin_config = {}
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def debug_page_request(self, page_index: int, page_size: int = 20):
        """调试页面请求"""
        print(f"\n🔍 调试第{page_index}页请求")
        print("="*40)
        
        url = f"{self.base_url}/api/homepage/pc/goods/market/querySaleTemplate"
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://www.youpin898.com',
            'Referer': 'https://www.youpin898.com/'
        }
        
        # 添加认证信息
        if self.youpin_config.get('device_id'):
            headers['DeviceId'] = self.youpin_config['device_id']
        if self.youpin_config.get('authorization'):
            headers['Authorization'] = self.youpin_config['authorization']
        
        payload = {
            "listSortType": 0,
            "sortType": 0,
            "pageSize": page_size,
            "pageIndex": page_index
        }
        
        print(f"📤 请求URL: {url}")
        print(f"📋 请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
        print(f"📋 请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                print(f"📥 响应状态: {response.status}")
                print(f"📋 响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"✅ JSON解析成功")
                        print(f"📊 响应结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        
                        if isinstance(data, dict):
                            print(f"📄 完整响应内容:")
                            print(json.dumps(data, indent=2, ensure_ascii=False))
                            
                            if 'Data' in data:
                                data_content = data['Data']
                                print(f"🎯 Data字段类型: {type(data_content)}")
                                if isinstance(data_content, list):
                                    print(f"🎯 Data字段长度: {len(data_content)}")
                                elif data_content is None:
                                    print("⚠️ Data字段为None")
                            else:
                                print("❌ 响应中没有Data字段")
                        
                        return data
                        
                    except Exception as e:
                        print(f"❌ JSON解析失败: {e}")
                        text = await response.text()
                        print(f"📄 原始响应内容: {text}")
                        
                else:
                    text = await response.text()
                    print(f"❌ HTTP错误 {response.status}: {text}")
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        
        return None

async def debug_youpin_pages():
    """调试悠悠有品多页请求"""
    print("🧪 调试悠悠有品API多页请求")
    print("="*50)
    
    async with YoupinDebugClient() as client:
        # 测试前3页
        for page in range(1, 4):
            result = await client.debug_page_request(page_index=page)
            
            # 页面间延迟
            if page < 3:
                print(f"\n⏱️ 等待3秒后请求下一页...")
                await asyncio.sleep(3)
        
        print(f"\n🎯 调试完成")

if __name__ == "__main__":
    asyncio.run(debug_youpin_pages()) 