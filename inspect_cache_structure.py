#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查HashName缓存的数据结构
"""

import pickle
import json

def inspect_hashname_cache():
    """详细检查HashName缓存结构"""
    print("🔍 详细检查HashName缓存结构")
    
    try:
        with open('data/hashname_cache.pkl', 'rb') as f:
            cache_data = pickle.load(f)
        
        print(f"📊 缓存数据类型: {type(cache_data)}")
        print(f"📊 缓存数据键: {cache_data.keys() if isinstance(cache_data, dict) else '不是字典类型'}")
        
        if isinstance(cache_data, dict):
            hashnames = cache_data.get('hashnames', [])
            print(f"📊 hashnames 类型: {type(hashnames)}")
            print(f"📊 hashnames 长度: {len(hashnames)}")
            
            if hashnames:
                print(f"\n📝 前3个关键词详细信息:")
                for i, item in enumerate(hashnames[:3], 1):
                    print(f"  {i}. 类型: {type(item)}")
                    print(f"     内容: {item}")
                    if isinstance(item, dict):
                        print(f"     字典键: {list(item.keys())}")
                        if 'hash_name' in item:
                            print(f"     ✅ 包含 hash_name: {item['hash_name']}")
                        else:
                            print(f"     ❌ 不包含 hash_name")
                    print()
        
        else:
            print(f"❌ 缓存数据不是字典格式: {cache_data}")
            
    except FileNotFoundError:
        print("❌ 缓存文件不存在")
    except Exception as e:
        print(f"❌ 读取缓存失败: {e}")

def check_full_data_structure():
    """检查全量数据文件的结构，看看它们是否包含hash_name"""
    print("\n🔍 检查全量数据文件结构")
    
    files_to_check = [
        'data/buff_full.json',
        'data/youpin_full.json'
    ]
    
    for file_path in files_to_check:
        print(f"\n📁 检查文件: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"   数据类型: {type(data)}")
            if isinstance(data, dict):
                print(f"   字典键: {list(data.keys())}")
                items = data.get('items', [])
                if items:
                    print(f"   商品数量: {len(items)}")
                    print(f"   第一个商品键: {list(items[0].keys()) if items[0] else '空'}")
                    
                    # 检查是否有hash_name
                    first_item = items[0]
                    if 'hash_name' in first_item:
                        print(f"   ✅ 包含 hash_name: {first_item['hash_name']}")
                    elif 'hashName' in first_item:
                        print(f"   ✅ 包含 hashName: {first_item['hashName']}")
                    elif 'name' in first_item:
                        print(f"   ⚠️ 只有 name: {first_item['name']}")
                    else:
                        print(f"   ❌ 没有找到 hash_name 或 name 字段")
            else:
                print(f"   数据不是字典格式")
                
        except FileNotFoundError:
            print(f"   ❌ 文件不存在")
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")

if __name__ == "__main__":
    inspect_hashname_cache()
    check_full_data_structure() 