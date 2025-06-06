#!/usr/bin/env python3
"""
演示数据生成器
为系统提供测试数据，用于演示和开发
"""

import json
import random
from datetime import datetime
from models import SkinItem, PriceDiffItem
from analyzer import PriceDiffAnalyzer
from config import Config

def generate_demo_data():
    """生成演示数据"""
    
    # CS:GO饰品示例数据
    demo_items = [
        {
            "name": "AK-47 | 红线 (久经沙场)",
            "category": "步枪",
            "base_price": 580.0
        },
        {
            "name": "AWP | 龙狙 (久经沙场)",
            "category": "狙击枪", 
            "base_price": 2850.0
        },
        {
            "name": "M4A4 | 龙王 (久经沙场)",
            "category": "步枪",
            "base_price": 1280.0
        },
        {
            "name": "格洛克 18 型 | 水元素 (崭新出厂)",
            "category": "手枪",
            "base_price": 156.0
        },
        {
            "name": "刺刀(★) | 虎牙 (崭新出厂)",
            "category": "刀具",
            "base_price": 4580.0
        },
        {
            "name": "专业手套(★) | 深红织物 (久经沙场)",
            "category": "手套",
            "base_price": 3200.0
        },
        {
            "name": "沙漠之鹰 | 烈焰风暴 (略有磨损)",
            "category": "手枪",
            "base_price": 285.0
        },
        {
            "name": "蝴蝶刀(★) | 渐变之色 (久经沙场)",
            "category": "刀具",
            "base_price": 5680.0
        },
        {
            "name": "M4A1 消音型 | 热带风暴 (崭新出厂)",
            "category": "步枪",
            "base_price": 420.0
        },
        {
            "name": "USP-S | 杀戮确认 (略有磨损)",
            "category": "手枪",
            "base_price": 185.0
        },
        {
            "name": "运动手套(★) | 猩红头巾 (略有磨损)",
            "category": "手套",
            "base_price": 2850.0
        },
        {
            "name": "猎杀者匕首(★) | 虎牙 (崭新出厂)",
            "category": "刀具",
            "base_price": 3450.0
        },
        {
            "name": "P250 | 亚洲龙 (崭新出厂)",
            "category": "手枪",
            "base_price": 98.0
        },
        {
            "name": "弯刀(★) | 致命紫罗兰 (久经沙场)",
            "category": "刀具",
            "base_price": 2280.0
        },
        {
            "name": "SSG 08 | 血腥网络 (略有磨损)",
            "category": "狙击枪",
            "base_price": 68.0
        }
    ]
    
    skin_items = []
    
    for i, item_data in enumerate(demo_items):
        # 生成随机价格（模拟两个平台的价差）
        base_price = item_data["base_price"]
        
        # Buff价格（基准）
        buff_price = base_price + random.uniform(-base_price * 0.1, base_price * 0.1)
        
        # 悠悠有品价格（通常更高一些）
        price_increase = random.uniform(0.05, 0.3)  # 5-30%的价差
        youpin_price = buff_price * (1 + price_increase)
        
        # 只有部分商品有显著价差
        if random.random() < 0.7:  # 70%的商品有价差
            # 确保有足够的价差
            min_diff = Config.PRICE_DIFF_THRESHOLD
            actual_diff = youpin_price - buff_price
            if actual_diff < min_diff:
                youpin_price = buff_price + min_diff + random.uniform(0, 50)
        
        skin_item = SkinItem(
            id=f"demo_{i+1}",
            name=item_data["name"],
            category=item_data["category"],
            buff_price=round(buff_price, 2),
            youpin_price=round(youpin_price, 2),
            buff_url=f"https://buff.163.com/goods/{1000+i}",
            youpin_url=f"https://www.youpin898.com/item/{2000+i}",
            image_url=f"https://via.placeholder.com/150x150/007acc/fff?text=SKIN{i+1}",
            wear_level=random.choice(["崭新出厂", "略有磨损", "久经沙场", "破损不堪"]),
            wear_value=round(random.uniform(0.0, 1.0), 4),
            last_updated=datetime.now()
        )
        
        skin_items.append(skin_item)
    
    return skin_items

def save_demo_data():
    """保存演示数据到文件"""
    
    # 生成饰品数据
    skin_items = generate_demo_data()
    
    # 使用分析器生成差价数据
    analyzer = PriceDiffAnalyzer()
    diff_items = analyzer.analyze_price_diff(skin_items)
    
    print(f"生成了 {len(skin_items)} 个饰品数据")
    print(f"其中 {len(diff_items)} 个符合价差条件")
    
    # 显示部分数据
    print("\n前5个差价饰品：")
    for i, item in enumerate(diff_items[:5], 1):
        print(f"{i}. {item.skin_item.name}")
        print(f"   Buff价格: ¥{item.skin_item.buff_price}")
        print(f"   悠悠价格: ¥{item.skin_item.youpin_price}")
        print(f"   价差: ¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
        print()

if __name__ == "__main__":
    save_demo_data() 