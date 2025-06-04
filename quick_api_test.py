#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速API状态检查
"""

import asyncio
import aiohttp

async def quick_buff_test():
    """快速测试Buff API"""
    print("🔍 快速测试Buff API...")
    
    try:
        # 加载配置
        from token_manager import token_manager
        buff_config = token_manager.get_buff_config()
        cookies = buff_config.get("cookies", {})
        headers = buff_config.get("headers", {})
        
        print(f"   📝 Cookie数量: {len(cookies)}")
        print(f"   📝 Header数量: {len(headers)}")
        print(f"   📝 有Session: {'session' in cookies}")
        print(f"   📝 有CSRF: {'csrf_token' in cookies}")
        
        # 测试请求
        url = "https://buff.163.com/api/market/goods"
        params = {
            'game': 'csgo',
            'page_num': 1,
            'tab': 'selling',
            '_': 1735652100000
        }
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, cookies=cookies, headers=headers) as response:
                print(f"   📡 响应状态: {response.status}")
                print(f"   📡 响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        items_count = len(data['data'].get('items', []))
                        print(f"   ✅ 成功获取 {items_count} 个商品")
                        return True
                    else:
                        print(f"   ❌ 响应格式异常: {list(data.keys())}")
                        return False
                else:
                    text = await response.text()
                    print(f"   ❌ 请求失败: {text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False

async def quick_youpin_test():
    """快速测试悠悠有品API"""
    print("\n🔍 快速测试悠悠有品API...")
    
    try:
        # 加载配置
        from token_manager import token_manager
        youpin_config = token_manager.get_youpin_config()
        
        print(f"   📝 配置项: {list(youpin_config.keys())}")
        print(f"   📝 有Device ID: {'device_id' in youpin_config}")
        print(f"   📝 有UK: {'uk' in youpin_config}")
        
        # 构建请求
        url = "https://api.youpin898.com/api/homepage/OnSaleV2"
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 添加认证参数
        if youpin_config.get('device_id'):
            headers['device_id'] = youpin_config['device_id']
        if youpin_config.get('uk'):
            headers['uk'] = youpin_config['uk']
        if youpin_config.get('authorization'):
            headers['Authorization'] = youpin_config['authorization']
        
        payload = {
            "gameId": 730,
            "listType": 10,
            "pageIndex": 1,
            "pageSize": 10,
            "sortBy": 0
        }
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                print(f"   📡 响应状态: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   ✅ 成功获取 {len(data)} 个商品")
                        return True
                    else:
                        print(f"   ❌ 响应格式异常: {type(data)}, {len(data) if isinstance(data, list) else 'N/A'}")
                        return False
                else:
                    text = await response.text()
                    print(f"   ❌ 请求失败: {text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False

async def main():
    """主函数"""
    print("🚨 快速API状态检查")
    print("="*40)
    
    buff_ok = await quick_buff_test()
    youpin_ok = await quick_youpin_test()
    
    print(f"\n📊 结果汇总:")
    print(f"   Buff API: {'✅ 正常' if buff_ok else '❌ 异常'}")
    print(f"   悠悠有品API: {'✅ 正常' if youpin_ok else '❌ 异常'}")
    
    if not buff_ok or not youpin_ok:
        print(f"\n💡 可能的解决方案:")
        if not buff_ok:
            print(f"   🔧 Buff问题:")
            print(f"      - 检查session和csrf_token是否过期")
            print(f"      - 尝试重新登录Buff获取新的cookies")
            print(f"      - 检查网络是否能访问buff.163.com")
        
        if not youpin_ok:
            print(f"   🔧 悠悠有品问题:")
            print(f"      - 检查device_id和uk参数是否正确")
            print(f"      - 检查Authorization token是否有效")
            print(f"      - 尝试重新获取认证信息")

if __name__ == "__main__":
    asyncio.run(main()) 