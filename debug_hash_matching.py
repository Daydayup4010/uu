#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Hash匹配功能
"""

import asyncio
from integrated_price_system import BuffAPIClient, IntegratedPriceAnalyzer
from youpin_working_api import YoupinWorkingAPI

async def debug_hash_matching():
    """调试Hash匹配功能"""
    print("🔍 Hash匹配调试")
    print("="*50)
    
    # 1. 检查Buff商品的hash_name字段
    print("\n1️⃣ 检查Buff商品数据结构")
    async with BuffAPIClient() as buff_client:
        # 获取一些Buff商品
        goods_data = await buff_client.get_goods_list(page_num=1, page_size=5)
        if goods_data and 'data' in goods_data:
            items = goods_data['data'].get('items', [])
            print(f"获取到 {len(items)} 个Buff商品")
            
            for i, item_data in enumerate(items[:3], 1):
                print(f"\n📦 Buff商品 #{i}:")
                print(f"   原始数据字段: {list(item_data.keys())}")
                print(f"   name: {item_data.get('name', 'N/A')}")
                print(f"   market_hash_name: {item_data.get('market_hash_name', 'N/A')}")
                
                # 解析为SkinItem
                skin_item = buff_client.parse_goods_item(item_data)
                if skin_item:
                    print(f"   解析后的hash_name: {skin_item.hash_name}")
                    print(f"   解析后的name: {skin_item.name}")
                else:
                    print("   ❌ 解析失败")
    
    # 2. 检查悠悠有品商品的数据结构
    print("\n2️⃣ 检查悠悠有品商品数据结构")
    async with YoupinWorkingAPI() as youpin_client:
        # 获取一些悠悠有品商品
        youpin_items = await youpin_client.get_market_goods(page_index=1, page_size=5)
        if youpin_items:
            print(f"获取到 {len(youpin_items)} 个悠悠有品商品")
            
            for i, item in enumerate(youpin_items[:3], 1):
                print(f"\n📦 悠悠有品商品 #{i}:")
                print(f"   原始数据字段: {list(item.keys())}")
                print(f"   commodityName: {item.get('commodityName', 'N/A')}")
                print(f"   commodityHashName: {item.get('commodityHashName', 'N/A')}")
                print(f"   price: {item.get('price', 'N/A')}")
        else:
            print("❌ 未能获取悠悠有品商品数据")
    
    # 3. 对比Hash名称
    print("\n3️⃣ Hash名称对比分析")
    async with BuffAPIClient() as buff_client, YoupinWorkingAPI() as youpin_client:
        # 获取更多数据进行分析
        buff_goods = await buff_client.get_goods_list(page_num=1, page_size=10)
        youpin_items = await youpin_client.get_market_goods(page_index=1, page_size=10)
        
        if buff_goods and youpin_items:
            buff_items = buff_goods['data'].get('items', [])
            
            # 创建悠悠有品Hash映射
            youpin_hash_map = {}
            youpin_name_map = {}
            
            for item in youpin_items:
                hash_name = item.get('commodityHashName', '')
                commodity_name = item.get('commodityName', '')
                price = item.get('price', 0)
                
                if hash_name:
                    youpin_hash_map[hash_name] = price
                if commodity_name:
                    youpin_name_map[commodity_name] = price
            
            print(f"悠悠有品Hash映射数量: {len(youpin_hash_map)}")
            print(f"悠悠有品名称映射数量: {len(youpin_name_map)}")
            
            if len(youpin_hash_map) > 0:
                print(f"\n悠悠有品Hash样本:")
                for i, hash_name in enumerate(list(youpin_hash_map.keys())[:3]):
                    print(f"   #{i+1}: {hash_name}")
            
            # 检查匹配情况
            print(f"\n🔍 匹配测试:")
            hash_matches = 0
            name_matches = 0
            total_buff_items = 0
            
            for item_data in buff_items[:5]:  # 只测试前5个
                skin_item = buff_client.parse_goods_item(item_data)
                if not skin_item:
                    continue
                    
                total_buff_items += 1
                print(f"\n🎯 测试Buff商品: {skin_item.name}")
                print(f"   Buff hash_name: '{skin_item.hash_name}'")
                
                # 测试Hash匹配
                if skin_item.hash_name and skin_item.hash_name in youpin_hash_map:
                    hash_matches += 1
                    price = youpin_hash_map[skin_item.hash_name]
                    print(f"   ✅ Hash匹配成功! 价格: {price}")
                else:
                    print(f"   ❌ Hash匹配失败")
                    
                    # 尝试查找相似的Hash
                    if skin_item.hash_name:
                        similar_hashes = [h for h in youpin_hash_map.keys() 
                                        if skin_item.hash_name.lower() in h.lower() 
                                        or h.lower() in skin_item.hash_name.lower()]
                        if similar_hashes:
                            print(f"   💡 可能的相似Hash: {similar_hashes[:3]}")
                
                # 测试名称匹配
                if skin_item.name in youpin_name_map:
                    name_matches += 1
                    price = youpin_name_map[skin_item.name]
                    print(f"   ✅ 名称匹配成功! 价格: {price}")
                else:
                    print(f"   ❌ 名称匹配失败")
                    
                    # 尝试查找相似的名称
                    similar_names = [n for n in youpin_name_map.keys() 
                                   if len(set(skin_item.name.lower().split()) & set(n.lower().split())) >= 2]
                    if similar_names:
                        print(f"   💡 可能的相似名称: {similar_names[:3]}")
            
            print(f"\n📊 匹配统计:")
            print(f"   总测试商品: {total_buff_items}")
            print(f"   Hash精确匹配: {hash_matches}/{total_buff_items} ({hash_matches/total_buff_items*100:.1f}%)")
            print(f"   名称精确匹配: {name_matches}/{total_buff_items} ({name_matches/total_buff_items*100:.1f}%)")

async def debug_specific_item():
    """调试特定商品的匹配"""
    print("\n4️⃣ 特定商品调试")
    
    # 让我们专门查看AWP相关的商品
    target_weapon = "AWP"
    
    async with BuffAPIClient() as buff_client, YoupinWorkingAPI() as youpin_client:
        # 获取Buff数据
        buff_goods = await buff_client.get_goods_list(page_num=1, page_size=50)
        youpin_items = await youpin_client.get_market_goods(page_index=1, page_size=50)
        
        if buff_goods and youpin_items:
            buff_items = buff_goods['data'].get('items', [])
            
            # 找到AWP商品
            awp_buff_items = []
            for item_data in buff_items:
                skin_item = buff_client.parse_goods_item(item_data)
                if skin_item and target_weapon in skin_item.name.upper():
                    awp_buff_items.append(skin_item)
            
            awp_youpin_items = []
            for item in youpin_items:
                commodity_name = item.get('commodityName', '')
                if target_weapon in commodity_name.upper():
                    awp_youpin_items.append(item)
            
            print(f"找到 {len(awp_buff_items)} 个Buff {target_weapon}商品")
            print(f"找到 {len(awp_youpin_items)} 个悠悠有品 {target_weapon}商品")
            
            if awp_buff_items and awp_youpin_items:
                print(f"\n🔍 {target_weapon}商品对比:")
                
                # 显示Buff AWP
                print(f"\nBuff {target_weapon}商品:")
                for i, item in enumerate(awp_buff_items[:3], 1):
                    print(f"   #{i}: {item.name}")
                    print(f"       hash_name: '{item.hash_name}'")
                
                # 显示悠悠有品AWP
                print(f"\n悠悠有品 {target_weapon}商品:")
                for i, item in enumerate(awp_youpin_items[:3], 1):
                    print(f"   #{i}: {item.get('commodityName', 'N/A')}")
                    print(f"       commodityHashName: '{item.get('commodityHashName', 'N/A')}'")
                
                # 尝试匹配
                print(f"\n🎯 匹配尝试:")
                for buff_item in awp_buff_items[:2]:
                    print(f"\n寻找匹配: {buff_item.name}")
                    print(f"Buff hash: '{buff_item.hash_name}'")
                    
                    found_match = False
                    for youpin_item in awp_youpin_items:
                        youpin_hash = youpin_item.get('commodityHashName', '')
                        youpin_name = youpin_item.get('commodityName', '')
                        
                        if buff_item.hash_name == youpin_hash:
                            print(f"   ✅ Hash精确匹配: {youpin_name}")
                            found_match = True
                            break
                    
                    if not found_match:
                        print(f"   ❌ 未找到Hash匹配")

async def main():
    """主函数"""
    print("🧪 Hash匹配调试工具")
    print("="*60)
    
    try:
        await debug_hash_matching()
        await debug_specific_item()
        
        print(f"\n💡 调试建议:")
        print(f"1. 检查Buff API是否正确提取market_hash_name")
        print(f"2. 检查悠悠有品API是否有commodityHashName字段")
        print(f"3. 比较两个平台的Hash名称格式是否一致")
        print(f"4. 考虑添加Hash名称标准化处理")
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 