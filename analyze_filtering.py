#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析筛选过程和匹配率计算
解释为什么匹配到656个商品，匹配率80.4%
"""

import os
import json
from config import Config

def load_json_data(filepath: str):
    """加载JSON数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载文件失败 {filepath}: {e}")
        return {}

def analyze_filtering_process():
    """分析筛选过程"""
    print("🔍 分析筛选过程和匹配率计算...")
    print("=" * 60)
    
    # 加载数据
    data_dir = "data"
    buff_file = os.path.join(data_dir, "buff_full.json")
    youpin_file = os.path.join(data_dir, "youpin_full.json")
    
    if not os.path.exists(buff_file) or not os.path.exists(youpin_file):
        print("❌ 找不到数据文件")
        return
    
    buff_data = load_json_data(buff_file)
    youpin_data = load_json_data(youpin_file)
    
    if not buff_data or not youpin_data:
        print("❌ 数据加载失败")
        return
    
    buff_items = buff_data.get('items', [])
    youpin_items = youpin_data.get('items', [])
    
    print(f"📊 原始数据:")
    print(f"   Buff商品: {len(buff_items):,}个")
    print(f"   悠悠有品商品: {len(youpin_items):,}个")
    
    # 建立悠悠有品价格映射
    youpin_hash_map = {}
    for item in youpin_items:
        hash_name = item.get('commodityHashName', '')
        price = item.get('price', 0)
        if hash_name and price:
            try:
                youpin_hash_map[hash_name] = float(price)
            except (ValueError, TypeError):
                continue
    
    youpin_hashes = set(youpin_hash_map.keys())
    print(f"   悠悠有品Hash映射: {len(youpin_hash_map):,}个")
    
    # 分析筛选过程
    print(f"\n🔍 Config筛选条件:")
    print(f"   Buff价格区间: {Config.BUFF_PRICE_MIN}元 - {Config.BUFF_PRICE_MAX}元")
    print(f"   Buff在售数量: ≥{Config.BUFF_SELL_NUM_MIN}个")
    print(f"   价差区间: {Config.PRICE_DIFF_MIN}元 - {Config.PRICE_DIFF_MAX}元")
    
    # 统计各个筛选步骤 - 按照实际代码逻辑
    total_items = len(buff_items)
    processed_count = 0
    price_filtered_count = 0
    sell_num_filtered_count = 0
    valid_for_matching = 0
    matched_count = 0
    unmatched_count = 0
    price_diff_valid = 0
    
    print(f"\n📈 筛选过程分析 (模拟实际代码逻辑):")
    
    for item_data in buff_items:
        processed_count += 1  # 对应 stats['processed_count'] += 1
        
        buff_id = str(item_data.get('id', ''))
        buff_name = item_data.get('name', '')
        buff_price_str = item_data.get('sell_min_price', '0')
        hash_name = item_data.get('market_hash_name', '')
        sell_num = item_data.get('sell_num', 0)
        
        # 处理价格
        try:
            buff_price = float(buff_price_str) if buff_price_str else 0.0
        except (ValueError, TypeError):
            buff_price = 0.0
        
        if not buff_price or buff_price <= 0:
            continue
        
        # 🔥 应用Buff价格筛选 - 对应代码中的逻辑
        if not Config.is_buff_price_in_range(buff_price):
            price_filtered_count += 1  # 对应 stats['price_filtered_count'] += 1
            continue
        
        # 🔥 应用Buff在售数量筛选 - 对应代码中的逻辑  
        if not Config.is_buff_sell_num_valid(sell_num):
            sell_num_filtered_count += 1  # 对应 stats['sell_num_filtered_count'] += 1
            continue
        
        # 通过了前两步筛选，进入匹配阶段
        valid_for_matching += 1
        
        # 尝试匹配
        if hash_name in youpin_hashes and hash_name in youpin_hash_map:
            matched_count += 1
            youpin_price = youpin_hash_map[hash_name]
            price_diff = youpin_price - buff_price
            
            # 步骤3: 价差区间筛选
            if Config.is_price_diff_in_range(price_diff):
                price_diff_valid += 1
        else:
            unmatched_count += 1
    
    # 输出分析结果
    print(f"   处理商品: {processed_count:,}个")
    print(f"   价格筛选过滤: {price_filtered_count:,}个 ({price_filtered_count/total_items*100:.1f}%)")
    print(f"   在售数量过滤: {sell_num_filtered_count:,}个 ({sell_num_filtered_count/total_items*100:.1f}%)")
    print(f"   通过筛选进入匹配: {valid_for_matching:,}个 ({valid_for_matching/total_items*100:.1f}%)")
    
    print(f"\n🎯 匹配结果:")
    print(f"   找到匹配: {matched_count:,}个")
    print(f"   未匹配: {unmatched_count:,}个")
    print(f"   总参与匹配: {matched_count + unmatched_count:,}个")
    
    if (matched_count + unmatched_count) > 0:
        match_rate = matched_count / (matched_count + unmatched_count) * 100
        print(f"   匹配率: {match_rate:.1f}%")
    
    print(f"\n💰 价差筛选:")
    print(f"   符合价差条件: {price_diff_valid:,}个")
    if matched_count > 0:
        price_diff_rate = price_diff_valid / matched_count * 100
        print(f"   价差合格率: {price_diff_rate:.1f}%")
    
    # 对比日志数据
    print(f"\n📋 与日志数据对比:")
    print(f"   日志显示 - 处理商品: 24,572个 vs 计算: {processed_count:,}个")
    print(f"   日志显示 - 价格筛选过滤: 11,798个 vs 计算: {price_filtered_count:,}个")
    print(f"   日志显示 - 在售数量过滤: 11,875个 vs 计算: {sell_num_filtered_count:,}个") 
    print(f"   日志显示 - 找到匹配: 656个 vs 计算: {matched_count:,}个")
    print(f"   日志显示 - 未匹配: 160个 vs 计算: {unmatched_count:,}个")
    if (matched_count + unmatched_count) > 0:
        print(f"   日志显示 - 匹配率: 80.4% vs 计算: {match_rate:.1f}%")
    
    print(f"\n✅ 分析完成！")
    print(f"\n💡 结论:")
    print(f"   1. 严格的筛选条件过滤掉了96%的商品")
    print(f"   2. 只有{valid_for_matching:,}个商品参与匹配计算")
    print(f"   3. 匹配率{match_rate:.1f}%是基于这{valid_for_matching:,}个商品计算的")
    print(f"   4. 最终只有{price_diff_valid:,}个商品符合所有条件")

if __name__ == "__main__":
    analyze_filtering_process() 