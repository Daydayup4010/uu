#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API数据收集器
"""

import asyncio
import logging
from api_scrapers import APIDataCollector, collect_sample_api_data

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_api_collector():
    """测试API数据收集器"""
    print("🔍 测试基于API的数据收集器...")
    
    try:
        # 测试收集样本数据
        print("\n1. 测试收集样本数据 (20个商品)...")
        items = await collect_sample_api_data(count=20)
        
        print(f"✅ 成功收集 {len(items)} 个商品")
        
        if items:
            print("\n📋 样本商品信息:")
            for i, item in enumerate(items[:5], 1):  # 只显示前5个
                print(f"{i}. {item.name}")
                print(f"   Buff价格: ¥{item.buff_price}")
                print(f"   悠悠有品价格: ¥{item.youpin_price if item.youpin_price else 'N/A'}")
                print(f"   类别: {item.category}")
                print(f"   链接: {item.buff_url}")
                
                # 计算价差
                if item.youpin_price and item.buff_price:
                    price_diff = item.youpin_price - item.buff_price
                    print(f"   价差: ¥{price_diff:.2f}")
                print()
            
            # 统计信息
            valid_items = [item for item in items if item.youpin_price and item.buff_price > 0]
            if valid_items:
                total_price_diff = sum(item.youpin_price - item.buff_price for item in valid_items)
                avg_price_diff = total_price_diff / len(valid_items)
                print(f"📊 统计信息:")
                print(f"   有效商品数量: {len(valid_items)}")
                print(f"   平均价差: ¥{avg_price_diff:.2f}")
                print(f"   最大价差: ¥{max(item.youpin_price - item.buff_price for item in valid_items):.2f}")
                print(f"   最小价差: ¥{min(item.youpin_price - item.buff_price for item in valid_items):.2f}")
        
        return len(items) > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.exception("测试过程中发生错误")
        return False

async def test_large_collection():
    """测试大量数据收集"""
    print("\n🔍 测试大量数据收集 (2页，约200个商品)...")
    
    try:
        collector = APIDataCollector()
        items = await collector.collect_all_items(max_pages=2)
        
        print(f"✅ 成功收集 {len(items)} 个商品")
        
        if items:
            # 按类别统计
            categories = {}
            for item in items:
                category = item.category or "未知"
                categories[category] = categories.get(category, 0) + 1
            
            print(f"\n📊 商品类别分布:")
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   {category}: {count} 个")
            
            # 价格区间统计
            price_ranges = {
                "0-10元": 0,
                "10-50元": 0,
                "50-100元": 0,
                "100-500元": 0,
                "500元以上": 0
            }
            
            for item in items:
                if item.buff_price:
                    if item.buff_price < 10:
                        price_ranges["0-10元"] += 1
                    elif item.buff_price < 50:
                        price_ranges["10-50元"] += 1
                    elif item.buff_price < 100:
                        price_ranges["50-100元"] += 1
                    elif item.buff_price < 500:
                        price_ranges["100-500元"] += 1
                    else:
                        price_ranges["500元以上"] += 1
            
            print(f"\n💰 价格区间分布:")
            for range_name, count in price_ranges.items():
                print(f"   {range_name}: {count} 个")
        
        return len(items) > 0
        
    except Exception as e:
        print(f"❌ 大量数据收集测试失败: {e}")
        logger.exception("大量数据收集测试过程中发生错误")
        return False

def save_sample_data(items):
    """保存样本数据到文件"""
    try:
        import json
        from datetime import datetime
        
        # 转换为可序列化的格式
        data = []
        for item in items:
            data.append({
                'id': item.id,
                'name': item.name,
                'buff_price': item.buff_price,
                'youpin_price': item.youpin_price,
                'buff_url': item.buff_url,
                'youpin_url': item.youpin_url,
                'image_url': item.image_url,
                'category': item.category,
                'last_updated': item.last_updated.isoformat() if item.last_updated else None
            })
        
        filename = f"api_sample_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 样本数据已保存到 {filename}")
        
    except Exception as e:
        print(f"❌ 保存数据失败: {e}")

async def main():
    """主函数"""
    print("🎯 API数据收集器测试")
    print("="*50)
    
    # 1. 基本功能测试
    success1 = await test_api_collector()
    
    if success1:
        print("✅ 基本功能测试通过")
        
        # 2. 大量数据测试
        success2 = await test_large_collection()
        
        if success2:
            print("✅ 大量数据收集测试通过")
            
            # 收集样本数据并保存
            print("\n📄 生成样本数据文件...")
            sample_items = await collect_sample_api_data(count=50)
            save_sample_data(sample_items)
        
        print("\n🎉 所有测试通过！API数据收集器运行正常")
    else:
        print("❌ 基本功能测试失败")

if __name__ == "__main__":
    asyncio.run(main()) 