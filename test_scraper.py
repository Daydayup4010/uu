#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的Buff爬虫
"""

import logging
from scrapers import BuffScraper

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_buff_scraper():
    """测试Buff爬虫"""
    print("🔍 测试修复后的Buff爬虫...")
    
    scraper = BuffScraper()
    
    try:
        # 获取少量饰品进行测试
        items = scraper.get_popular_items(limit=5)
        
        print(f"✅ 成功获取 {len(items)} 个饰品")
        
        for i, item in enumerate(items, 1):
            print(f"{i}. {item.name}")
            print(f"   价格: ¥{item.buff_price}")
            print(f"   ID: {item.id}")
            print(f"   链接: {item.buff_url}")
            print()
        
        return len(items) > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_buff_scraper()
    if success:
        print("🎉 Buff爬虫修复成功！")
    else:
        print("❌ Buff爬虫仍有问题") 