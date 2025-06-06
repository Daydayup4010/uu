#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于真实API的演示数据生成器

使用Buff API获取真实的饰品数据，并分析价差
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import List

from api_scrapers import collect_sample_api_data, APIDataCollector
from analyzer import PriceDiffAnalyzer
from models import PriceDiffItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_api_demo_data(count: int = 200) -> List[PriceDiffItem]:
    """生成基于API的演示数据"""
    logger.info(f"开始生成基于API的演示数据，目标数量: {count}")
    
    try:
        # 使用API收集真实数据
        logger.info("正在从Buff API收集数据...")
        items = await collect_sample_api_data(count=count)
        
        if not items:
            logger.error("未能获取到任何商品数据")
            return []
        
        logger.info(f"成功收集 {len(items)} 个商品数据")
        
        # 分析价差
        analyzer = PriceDiffAnalyzer()
        diff_items = analyzer.analyze_price_diff(items)
        
        # 保存数据
        analyzer.save_diff_data(diff_items)
        
        logger.info(f"生成了 {len(diff_items)} 个有价差的商品")
        
        return diff_items
        
    except Exception as e:
        logger.error(f"生成API演示数据失败: {e}")
        return []

async def generate_large_dataset(max_pages: int = 5) -> List[PriceDiffItem]:
    """生成大型数据集"""
    if max_pages is None:
        logger.info("开始生成全量数据集（所有页面）...")
    else:
        logger.info(f"开始生成大型数据集，最大页数: {max_pages}")
    
    try:
        # 使用API收集大量数据
        collector = APIDataCollector()
        items = await collector.collect_all_items(max_pages=max_pages)
        
        if not items:
            logger.error("未能获取到任何商品数据")
            return []
        
        logger.info(f"成功收集 {len(items)} 个商品数据")
        
        # 分析价差
        analyzer = PriceDiffAnalyzer()
        diff_items = analyzer.analyze_price_diff(items)
        
        # 保存到不同的文件
        if max_pages is None:
            filename = f"data/api_full_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            filename = f"data/api_large_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs('data', exist_ok=True)
        
        # 转换为可序列化的格式
        data = []
        for item in diff_items:
            data.append({
                'id': item.skin_item.id,
                'name': item.skin_item.name,
                'buff_price': item.skin_item.buff_price,
                'youpin_price': item.skin_item.youpin_price,
                'price_diff': item.price_diff,
                'profit_margin': item.profit_rate,
                'buff_buy_url': item.buff_buy_url,
                'youpin_url': item.skin_item.youpin_url,
                'image_url': item.skin_item.image_url,
                'category': item.skin_item.category,
                'last_updated': item.skin_item.last_updated.isoformat() if item.skin_item.last_updated else None
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"大型数据集已保存到 {filename}")
        logger.info(f"生成了 {len(diff_items)} 个有价差的商品")
        
        return diff_items
        
    except Exception as e:
        logger.error(f"生成大型数据集失败: {e}")
        return []

def print_statistics(diff_items: List[PriceDiffItem]):
    """打印统计信息"""
    if not diff_items:
        print("❌ 没有数据可以分析")
        return
    
    analyzer = PriceDiffAnalyzer()
    stats = analyzer.get_statistics(diff_items)
    
    print("\n📊 API数据统计信息:")
    print(f"   总商品数量: {stats['total_count']}")
    print(f"   平均价差: ¥{stats['avg_price_diff']:.2f}")
    print(f"   最大价差: ¥{stats['max_price_diff']:.2f}")
    print(f"   最小价差: ¥{stats['min_price_diff']:.2f}")
    print(f"   平均利润率: {stats['avg_profit_rate']:.1f}%")
    print(f"   最大利润率: {stats['max_profit_rate']:.1f}%")
    
    # 按类别统计
    categories = {}
    for item in diff_items:
        category = item.skin_item.category or "未知"
        if category not in categories:
            categories[category] = []
        categories[category].append(item.price_diff)
    
    print(f"\n🏷️ 类别统计:")
    for category, price_diffs in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        avg_diff = sum(price_diffs) / len(price_diffs)
        print(f"   {category}: {len(price_diffs)} 个，平均价差 ¥{avg_diff:.2f}")
    
    # 高价差商品
    high_diff_items = sorted(diff_items, key=lambda x: x.price_diff, reverse=True)[:5]
    print(f"\n💰 价差最高的5个商品:")
    for i, item in enumerate(high_diff_items, 1):
        print(f"   {i}. {item.skin_item.name}")
        print(f"      价差: ¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
        print(f"      Buff: ¥{item.skin_item.buff_price} → 悠悠有品: ¥{item.skin_item.youpin_price}")

async def save_api_demo_data():
    """保存API演示数据的便捷函数"""
    print("🚀 开始生成基于真实API的演示数据...")
    
    # 生成演示数据
    diff_items = await generate_api_demo_data(count=100)
    
    if diff_items:
        print_statistics(diff_items)
        print(f"\n✅ API演示数据生成完成！共 {len(diff_items)} 个有价差商品")
        print("💡 数据已保存到 data/price_diff_analysis.json")
    else:
        print("❌ API演示数据生成失败")

async def save_large_api_dataset():
    """保存大型API数据集的便捷函数"""
    print("🚀 开始生成大型API数据集...")
    
    # 生成大型数据集
    diff_items = await generate_large_dataset(max_pages=3)
    
    if diff_items:
        print_statistics(diff_items)
        print(f"\n✅ 大型API数据集生成完成！共 {len(diff_items)} 个有价差商品")
    else:
        print("❌ 大型API数据集生成失败")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--large":
        # 生成大型数据集
        asyncio.run(save_large_api_dataset())
    else:
        # 生成演示数据
        asyncio.run(save_api_demo_data()) 