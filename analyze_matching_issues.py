#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析两个平台数据匹配问题
"""

import asyncio
import json
import re
from collections import defaultdict, Counter
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient
from config import Config

async def analyze_matching_issues():
    """分析匹配问题"""
    print("🔍 分析两个平台数据匹配问题")
    print("=" * 60)
    
    # 获取最新数据
    print("📊 获取最新数据样本...")
    
    # 获取小样本数据进行分析（避免等待太久）
    async with OptimizedBuffClient() as buff_client:
        buff_data = await buff_client.get_all_goods_safe(max_pages=5)  # 获取5页数据
    
    async with OptimizedYoupinClient() as youpin_client:
        youpin_data = await youpin_client.get_all_items_safe(max_pages=5)  # 获取5页数据
    
    if not buff_data or not youpin_data:
        print("❌ 无法获取数据")
        return
    
    print(f"✅ 获取数据：Buff {len(buff_data)}个，悠悠有品 {len(youpin_data)}个")
    
    # 分析 Buff 数据格式
    print("\n📊 Buff 数据格式分析:")
    analyze_buff_data_format(buff_data[:10])
    
    # 分析悠悠有品数据格式
    print("\n📊 悠悠有品数据格式分析:")
    analyze_youpin_data_format(youpin_data[:10])
    
    # 建立Hash名称集合
    print("\n🔗 Hash名称匹配分析:")
    buff_hashes = set()
    youpin_hashes = set()
    
    # 从Buff数据提取Hash
    for item in buff_data:
        hash_name = item.get('market_hash_name', '')
        if hash_name:
            buff_hashes.add(hash_name)
    
    # 从悠悠有品数据提取Hash
    for item in youpin_data:
        hash_name = item.get('commodityHashName', '')
        if hash_name:
            youpin_hashes.add(hash_name)
    
    print(f"Buff Hash names: {len(buff_hashes)}个")
    print(f"悠悠有品 Hash names: {len(youpin_hashes)}个")
    
    # 精确匹配
    exact_matches = buff_hashes & youpin_hashes
    print(f"精确匹配: {len(exact_matches)}个 ({len(exact_matches)/min(len(buff_hashes), len(youpin_hashes))*100:.1f}%)")
    
    if exact_matches:
        print("精确匹配示例:")
        for i, match in enumerate(list(exact_matches)[:5]):
            print(f"  {i+1}. {match}")
    
    # 分析不匹配的原因
    print("\n🔍 分析不匹配原因:")
    analyze_mismatch_patterns(buff_hashes, youpin_hashes)
    
    # 尝试改进匹配策略
    print("\n🛠️ 改进匹配策略:")
    suggest_improved_matching(buff_hashes, youpin_hashes)

def analyze_buff_data_format(items):
    """分析Buff数据格式"""
    print("样本数据:")
    for i, item in enumerate(items[:3]):
        print(f"  {i+1}. ID: {item.get('id')}")
        print(f"     名称: {item.get('name')}")
        print(f"     Hash: {item.get('market_hash_name')}")
        print(f"     价格: {item.get('sell_min_price')}")
        print()

def analyze_youpin_data_format(items):
    """分析悠悠有品数据格式"""
    print("样本数据:")
    for i, item in enumerate(items[:3]):
        print(f"  {i+1}. ID: {item.get('id')}")
        print(f"     名称: {item.get('commodityName')}")
        print(f"     Hash: {item.get('commodityHashName')}")
        print(f"     价格: {item.get('price')}")
        print()

def analyze_mismatch_patterns(buff_hashes, youpin_hashes):
    """分析不匹配的模式"""
    
    # 样本分析
    buff_sample = list(buff_hashes)[:10]
    youpin_sample = list(youpin_hashes)[:10]
    
    print("Buff Hash样本:")
    for i, hash_name in enumerate(buff_sample):
        print(f"  {i+1}. {hash_name}")
    
    print("\n悠悠有品 Hash样本:")
    for i, hash_name in enumerate(youpin_sample):
        print(f"  {i+1}. {hash_name}")
    
    # 分析字符差异
    print("\n字符差异分析:")
    
    # 检查特殊字符
    buff_special_chars = set()
    youpin_special_chars = set()
    
    for hash_name in buff_hashes:
        for char in hash_name:
            if not char.isalnum() and char != ' ':
                buff_special_chars.add(char)
    
    for hash_name in youpin_hashes:
        for char in hash_name:
            if not char.isalnum() and char != ' ':
                youpin_special_chars.add(char)
    
    print(f"Buff特殊字符: {sorted(buff_special_chars)}")
    print(f"悠悠有品特殊字符: {sorted(youpin_special_chars)}")
    
    # 检查长度分布
    buff_lengths = [len(h) for h in buff_hashes]
    youpin_lengths = [len(h) for h in youpin_hashes]
    
    print(f"\nHash长度分布:")
    print(f"Buff: 平均{sum(buff_lengths)/len(buff_lengths):.1f}, 范围{min(buff_lengths)}-{max(buff_lengths)}")
    print(f"悠悠有品: 平均{sum(youpin_lengths)/len(youpin_lengths):.1f}, 范围{min(youpin_lengths)}-{max(youpin_lengths)}")

def suggest_improved_matching(buff_hashes, youpin_hashes):
    """建议改进的匹配策略"""
    
    print("尝试改进匹配策略:")
    
    # 1. 规范化匹配
    def normalize_hash(hash_name):
        """规范化Hash名称"""
        # 移除多余空格，统一大小写
        return re.sub(r'\s+', ' ', hash_name.strip())
    
    buff_normalized = {normalize_hash(h): h for h in buff_hashes}
    youpin_normalized = {normalize_hash(h): h for h in youpin_hashes}
    
    normalized_matches = set(buff_normalized.keys()) & set(youpin_normalized.keys())
    print(f"1. 规范化后匹配: {len(normalized_matches)}个")
    
    # 2. 移除特殊符号匹配
    def remove_special_chars(hash_name):
        """移除特殊字符"""
        return re.sub(r'[^\w\s]', '', hash_name).strip()
    
    buff_no_special = {remove_special_chars(h): h for h in buff_hashes}
    youpin_no_special = {remove_special_chars(h): h for h in youpin_hashes}
    
    no_special_matches = set(buff_no_special.keys()) & set(youpin_no_special.keys())
    print(f"2. 移除特殊符号后匹配: {len(no_special_matches)}个")
    
    # 3. 模糊匹配（Levenshtein距离）
    def fuzzy_match_count(buff_set, youpin_set, threshold=0.9):
        """计算模糊匹配数量"""
        from difflib import SequenceMatcher
        
        matches = 0
        for buff_hash in list(buff_set)[:100]:  # 限制样本避免耗时过长
            for youpin_hash in youpin_set:
                similarity = SequenceMatcher(None, buff_hash.lower(), youpin_hash.lower()).ratio()
                if similarity >= threshold:
                    matches += 1
                    break
        return matches
    
    try:
        fuzzy_matches = fuzzy_match_count(buff_hashes, youpin_hashes, 0.9)
        print(f"3. 模糊匹配(90%相似度): 约{fuzzy_matches}个")
    except Exception as e:
        print(f"3. 模糊匹配分析失败: {e}")
    
    # 4. 武器名称匹配
    def extract_weapon_name(hash_name):
        """提取武器名称部分"""
        # 移除条件描述，如(Field-Tested), (Factory New)等
        weapon_name = re.sub(r'\s*\([^)]*\)\s*$', '', hash_name)
        return weapon_name.strip()
    
    buff_weapons = {extract_weapon_name(h): h for h in buff_hashes}
    youpin_weapons = {extract_weapon_name(h): h for h in youpin_hashes}
    
    weapon_matches = set(buff_weapons.keys()) & set(youpin_weapons.keys())
    print(f"4. 武器名称匹配(忽略磨损): {len(weapon_matches)}个")
    
    # 输出改进建议
    print("\n💡 改进建议:")
    print("1. 使用多级匹配策略：精确匹配 -> 规范化匹配 -> 武器名称匹配")
    print("2. 添加预处理步骤：统一字符编码、移除多余空格")
    print("3. 建立武器名称映射表：处理不同平台的命名差异")
    print("4. 使用模糊匹配作为最后手段：适度降低匹配阈值")

if __name__ == "__main__":
    asyncio.run(analyze_matching_issues()) 