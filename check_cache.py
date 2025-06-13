#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
import json
from datetime import datetime

def check_hashname_cache():
    try:
        with open('data/hashname_cache.pkl', 'rb') as f:
            data = pickle.load(f)
        
        hashnames = data.get('hashnames', [])
        last_update = data.get('last_full_update')
        
        print(f"🔍 HashName缓存检查:")
        print(f"  缓存关键词数量: {len(hashnames)}")
        print(f"  上次全量更新: {last_update}")
        
        if hashnames:
            print(f"  前10个关键词:")
            for i, keyword in enumerate(hashnames[:10], 1):
                print(f"    {i}. {keyword}")
        else:
            print("  ❌ 缓存为空！这会导致增量更新无法进行")
            
    except FileNotFoundError:
        print("❌ 缓存文件不存在")
    except Exception as e:
        print(f"❌ 读取缓存失败: {e}")

def check_latest_data():
    try:
        with open('data/latest_price_diff.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        items = data.get('items', [])
        
        print(f"\n📊 最新数据检查:")
        print(f"  商品数量: {len(items)}")
        print(f"  上次全量更新: {metadata.get('last_full_update')}")
        print(f"  上次增量更新: {metadata.get('last_incremental_update')}")
        print(f"  生成时间: {metadata.get('generated_at')}")
        
        if items:
            print(f"  前3个商品:")
            for i, item in enumerate(items[:3], 1):
                print(f"    {i}. {item.get('name', '')}: ¥{item.get('price_diff', 0):.2f}")
                print(f"       更新时间: {item.get('last_updated', '')}")
                
    except FileNotFoundError:
        print("❌ 最新数据文件不存在")
    except Exception as e:
        print(f"❌ 读取最新数据失败: {e}")

if __name__ == "__main__":
    check_hashname_cache()
    check_latest_data() 