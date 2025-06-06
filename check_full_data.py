#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 full data 文件的内容和结构
"""

import json
import os
from datetime import datetime

def check_full_data_files():
    """检查 full data 文件"""
    
    data_dir = "data"
    
    print("🔍 检查 Full Data 文件")
    print("=" * 50)
    
    # 查找所有 full data 文件
    full_data_files = []
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if "full" in filename and filename.endswith(".json"):
                full_data_files.append(os.path.join(data_dir, filename))
    
    if not full_data_files:
        print("❌ 未找到任何 full data 文件")
        return
    
    print(f"📁 找到 {len(full_data_files)} 个 full data 文件:")
    for file_path in full_data_files:
        print(f"   - {file_path}")
    
    print()
    
    # 分析每个文件
    for file_path in full_data_files:
        analyze_file(file_path)
        print()

def analyze_file(file_path):
    """分析单个文件"""
    try:
        # 获取文件基本信息
        file_size = os.path.getsize(file_path) / 1024  # KB
        platform = "Buff" if "buff" in file_path.lower() else "悠悠有品"
        
        print(f"📊 {platform} 数据文件分析: {os.path.basename(file_path)}")
        print(f"   文件大小: {file_size:.1f} KB")
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 元数据信息
        metadata = data.get('metadata', {})
        print(f"   平台: {metadata.get('platform', '未知')}")
        print(f"   总数量: {metadata.get('total_count', '未知')}")
        print(f"   最大页数: {metadata.get('max_pages', '未知')}")
        print(f"   生成时间: {metadata.get('generated_at', '未知')}")
        
        # API配置
        api_config = metadata.get('api_config', {})
        if api_config:
            print(f"   API配置: 延迟={api_config.get('delay', '未知')}s, 页大小={api_config.get('page_size', '未知')}")
        
        # 商品数据分析
        items = data.get('items', [])
        print(f"   实际商品数量: {len(items)}")
        
        if items:
            # 分析第一个商品的字段
            first_item = items[0]
            print(f"   商品字段数量: {len(first_item.keys())}")
            
            # 检查关键字段
            if "buff" in file_path.lower():
                check_buff_item_fields(first_item)
            else:
                check_youpin_item_fields(first_item)
            
            # 价格范围分析
            analyze_price_range(items, platform)
            
    except Exception as e:
        print(f"❌ 分析文件失败 {file_path}: {e}")

def check_buff_item_fields(item):
    """检查 Buff 商品字段"""
    required_fields = [
        'id', 'name', 'market_hash_name', 'sell_min_price', 'sell_num',
        'goods_info', 'steam_market_url'
    ]
    
    print("   🔍 Buff字段检查:")
    for field in required_fields:
        status = "✅" if field in item else "❌"
        print(f"     {status} {field}")
    
    # 检查商品详细信息
    goods_info = item.get('goods_info', {})
    if goods_info:
        print("   📋 商品详细信息:")
        print(f"     图片URL: {'✅' if goods_info.get('icon_url') else '❌'}")
        print(f"     Steam价格: {'✅' if goods_info.get('steam_price') else '❌'}")
        print(f"     分类标签: {'✅' if goods_info.get('info', {}).get('tags') else '❌'}")

def check_youpin_item_fields(item):
    """检查悠悠有品商品字段"""
    required_fields = [
        'id', 'commodityName', 'commodityHashName', 'price', 'onSaleCount',
        'iconUrl', 'typeName', 'rarity'
    ]
    
    print("   🔍 悠悠有品字段检查:")
    for field in required_fields:
        status = "✅" if field in item else "❌"
        print(f"     {status} {field}")

def analyze_price_range(items, platform):
    """分析价格范围"""
    try:
        prices = []
        for item in items:
            if platform == "Buff":
                price_str = item.get('sell_min_price', '0')
                try:
                    price = float(price_str) if price_str else 0
                    if price > 0:
                        prices.append(price)
                except:
                    continue
            else:  # 悠悠有品
                price_str = item.get('price', '0')
                try:
                    price = float(price_str) if price_str else 0
                    if price > 0:
                        prices.append(price)
                except:
                    continue
        
        if prices:
            print(f"   💰 价格分析 (共{len(prices)}个有效价格):")
            print(f"     最低价格: ¥{min(prices):.2f}")
            print(f"     最高价格: ¥{max(prices):.2f}")
            print(f"     平均价格: ¥{sum(prices)/len(prices):.2f}")
            
            # 价格区间分析
            ranges = {
                "0-10元": len([p for p in prices if 0 < p <= 10]),
                "10-50元": len([p for p in prices if 10 < p <= 50]),
                "50-100元": len([p for p in prices if 50 < p <= 100]),
                "100-500元": len([p for p in prices if 100 < p <= 500]),
                "500元以上": len([p for p in prices if p > 500])
            }
            
            print("     价格区间分布:")
            for range_name, count in ranges.items():
                if count > 0:
                    print(f"       {range_name}: {count}个 ({count/len(prices)*100:.1f}%)")
        else:
            print("   ⚠️ 未找到有效价格数据")
            
    except Exception as e:
        print(f"   ❌ 价格分析失败: {e}")

if __name__ == "__main__":
    check_full_data_files() 