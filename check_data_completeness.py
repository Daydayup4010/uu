#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 full data 文件的数据完整性
"""

import json
import os
from collections import defaultdict

def check_data_completeness():
    """检查数据完整性"""
    
    print("🔍 检查 Full Data 数据完整性")
    print("=" * 60)
    
    # 检查 Buff 数据
    buff_file = "data/buff_full_20250605_175545.json"
    if os.path.exists(buff_file):
        print("📊 Buff 数据完整性分析:")
        analyze_buff_completeness(buff_file)
        print()
    
    # 检查悠悠有品数据
    youpin_file = "data/youpin_full_20250605_175556.json"
    if os.path.exists(youpin_file):
        print("📊 悠悠有品 数据完整性分析:")
        analyze_youpin_completeness(youpin_file)
        print()

def analyze_buff_completeness(file_path):
    """分析 Buff 数据完整性"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        total_items = len(items)
        
        print(f"   总商品数: {total_items}")
        
        # 检查关键字段的完整性
        field_stats = defaultdict(int)
        category_stats = defaultdict(int)
        weapon_types = defaultdict(int)
        
        for item in items:
            # 基本字段检查
            if item.get('id'):
                field_stats['id'] += 1
            if item.get('name'):
                field_stats['name'] += 1
            if item.get('market_hash_name'):
                field_stats['market_hash_name'] += 1
            if item.get('sell_min_price'):
                field_stats['sell_min_price'] += 1
            if item.get('sell_num') is not None:
                field_stats['sell_num'] += 1
            
            # 图片和详细信息
            goods_info = item.get('goods_info', {})
            if goods_info.get('icon_url'):
                field_stats['icon_url'] += 1
            if goods_info.get('steam_price'):
                field_stats['steam_price'] += 1
            
            # 分类信息分析
            tags = goods_info.get('info', {}).get('tags', {})
            if tags:
                field_stats['tags'] += 1
                
                # 武器类型
                weapon_type = tags.get('type', {}).get('localized_name', '未知')
                weapon_types[weapon_type] += 1
                
                # 品质/稀有度
                rarity = tags.get('rarity', {}).get('localized_name', '未知')
                category_stats[rarity] += 1
        
        print("   ✅ 字段完整性统计:")
        for field, count in field_stats.items():
            percentage = (count / total_items) * 100
            print(f"     {field}: {count}/{total_items} ({percentage:.1f}%)")
        
        print("   🎯 武器类型分布:")
        for weapon_type, count in sorted(weapon_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / total_items) * 100
            print(f"     {weapon_type}: {count} ({percentage:.1f}%)")
        
        print("   💎 稀有度分布:")
        for rarity, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_items) * 100
            print(f"     {rarity}: {count} ({percentage:.1f}%)")
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def analyze_youpin_completeness(file_path):
    """分析悠悠有品数据完整性"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        total_items = len(items)
        
        print(f"   总商品数: {total_items}")
        
        # 检查关键字段的完整性
        field_stats = defaultdict(int)
        type_stats = defaultdict(int)
        rarity_stats = defaultdict(int)
        
        for item in items:
            # 基本字段检查
            if item.get('id'):
                field_stats['id'] += 1
            if item.get('commodityName'):
                field_stats['commodityName'] += 1
            if item.get('commodityHashName'):
                field_stats['commodityHashName'] += 1
            if item.get('price'):
                field_stats['price'] += 1
            if item.get('onSaleCount') is not None:
                field_stats['onSaleCount'] += 1
            if item.get('iconUrl'):
                field_stats['iconUrl'] += 1
            if item.get('steamPrice'):
                field_stats['steamPrice'] += 1
            
            # 分类信息
            if item.get('typeName'):
                field_stats['typeName'] += 1
                type_stats[item.get('typeName')] += 1
            
            if item.get('rarity'):
                field_stats['rarity'] += 1
                rarity_stats[item.get('rarity')] += 1
            
            if item.get('exterior'):
                field_stats['exterior'] += 1
        
        print("   ✅ 字段完整性统计:")
        for field, count in field_stats.items():
            percentage = (count / total_items) * 100
            print(f"     {field}: {count}/{total_items} ({percentage:.1f}%)")
        
        print("   🎯 商品类型分布:")
        for type_name, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / total_items) * 100
            print(f"     {type_name}: {count} ({percentage:.1f}%)")
        
        print("   💎 稀有度分布:")
        for rarity, count in sorted(rarity_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_items) * 100
            print(f"     {rarity}: {count} ({percentage:.1f}%)")
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def check_hash_name_matching():
    """检查两个平台的 hash name 匹配情况"""
    print("🔗 检查平台间数据匹配性:")
    
    try:
        # 读取 Buff 数据
        buff_file = "data/buff_full_20250605_175545.json"
        with open(buff_file, 'r', encoding='utf-8') as f:
            buff_data = json.load(f)
        buff_items = buff_data.get('items', [])
        
        # 读取悠悠有品数据
        youpin_file = "data/youpin_full_20250605_175556.json"
        with open(youpin_file, 'r', encoding='utf-8') as f:
            youpin_data = json.load(f)
        youpin_items = youpin_data.get('items', [])
        
        # 建立 hash name 集合
        buff_hashes = set()
        youpin_hashes = set()
        
        for item in buff_items:
            hash_name = item.get('market_hash_name', '')
            if hash_name:
                buff_hashes.add(hash_name)
        
        for item in youpin_items:
            hash_name = item.get('commodityHashName', '')
            if hash_name:
                youpin_hashes.add(hash_name)
        
        # 计算匹配情况
        common_hashes = buff_hashes & youpin_hashes
        buff_only = buff_hashes - youpin_hashes
        youpin_only = youpin_hashes - buff_hashes
        
        print(f"   Buff平台 hash names: {len(buff_hashes)}个")
        print(f"   悠悠有品 hash names: {len(youpin_hashes)}个")
        print(f"   共同 hash names: {len(common_hashes)}个")
        print(f"   匹配率: {len(common_hashes)/max(len(buff_hashes), len(youpin_hashes))*100:.1f}%")
        
        if len(common_hashes) > 0:
            print(f"   📈 可进行价差分析的商品数量: {len(common_hashes)}")
            print("   ✅ 数据质量良好，可以进行有效的价差分析")
        else:
            print("   ⚠️ 未发现匹配的商品，可能需要检查数据收集方式")
        
        # 显示一些匹配的例子
        if common_hashes:
            print("   📋 匹配商品示例:")
            for i, hash_name in enumerate(list(common_hashes)[:5]):
                print(f"     {i+1}. {hash_name}")
                
    except Exception as e:
        print(f"❌ 匹配分析失败: {e}")

if __name__ == "__main__":
    check_data_completeness()
    print()
    check_hash_name_matching() 