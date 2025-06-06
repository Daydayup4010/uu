#!/usr/bin/env python3
import json
import os

def check_files():
    print("📁 检查生成的数据文件")
    print("="*50)
    
    # 检查data目录
    data_dir = "data"
    if not os.path.exists(data_dir):
        print("❌ data目录不存在")
        return
    
    files = os.listdir(data_dir)
    
    # 检查Buff文件
    buff_files = [f for f in files if f.startswith('buff_full_') and f.endswith('.json')]
    if buff_files:
        latest_buff = sorted(buff_files)[-1]
        print(f"🔥 Buff文件: {latest_buff}")
        
        try:
            with open(os.path.join(data_dir, latest_buff), 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   商品数量: {data['metadata']['total_count']}")
            print(f"   生成时间: {data['metadata']['generated_at']}")
            if data['items']:
                print(f"   示例商品: {data['items'][0].get('name', '未知')}")
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
    else:
        print("❌ 未找到Buff全量文件")
    
    # 检查悠悠有品文件
    youpin_files = [f for f in files if f.startswith('youpin_full_') and f.endswith('.json')]
    if youpin_files:
        latest_youpin = sorted(youpin_files)[-1]
        print(f"🛍️ 悠悠有品文件: {latest_youpin}")
        
        try:
            with open(os.path.join(data_dir, latest_youpin), 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   商品数量: {data['metadata']['total_count']}")
            print(f"   生成时间: {data['metadata']['generated_at']}")
            if data['items']:
                first_item = data['items'][0]
                item_name = "未知"
                if isinstance(first_item, dict):
                    item_name = first_item.get('commodityName', first_item.get('name', '未知'))
                print(f"   示例商品: {item_name}")
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
    else:
        print("❌ 未找到悠悠有品全量文件")
    
    # 检查价差文件
    latest_data_file = "data/latest_price_diff.json"
    if os.path.exists(latest_data_file):
        print(f"💰 价差文件: {latest_data_file}")
        try:
            with open(latest_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   价差商品数: {data['metadata']['total_count']}")
            print(f"   生成时间: {data['metadata']['generated_at']}")
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
    else:
        print("❌ 未找到价差数据文件")

if __name__ == "__main__":
    check_files() 