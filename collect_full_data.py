#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收集完整的平台数据
使用配置中的最大页数收集全部饰品数据
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from config import Config
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FullDataCollector:
    """完整数据收集器"""
    
    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    async def collect_all_data(self, use_config_limits: bool = True):
        """收集所有平台的完整数据"""
        
        if use_config_limits:
            buff_max_pages = Config.BUFF_MAX_PAGES
            youpin_max_pages = Config.YOUPIN_MAX_PAGES
            logger.info(f"🎯 使用配置限制: Buff {buff_max_pages}页, 悠悠有品 {youpin_max_pages}页")
        else:
            # 获取所有可用页面
            buff_max_pages = None
            youpin_max_pages = None
            logger.info("🚀 收集所有可用页面的数据")
        
        print("🔍 开始收集完整平台数据")
        print("=" * 60)
        
        # 收集 Buff 数据
        await self.collect_buff_data(buff_max_pages)
        
        # 等待一段时间避免请求过快
        await asyncio.sleep(5)
        
        # 收集悠悠有品数据
        await self.collect_youpin_data(youpin_max_pages)
        
        print("\n✅ 完整数据收集完成！")
    
    async def collect_buff_data(self, max_pages: int = None):
        """收集 Buff 完整数据"""
        try:
            print(f"\n📊 开始收集 Buff 数据...")
            if max_pages:
                print(f"   最大页数: {max_pages}")
                print(f"   预计商品数: {max_pages * Config.BUFF_PAGE_SIZE}")
            else:
                print("   收集所有可用页面")
            
            async with OptimizedBuffClient() as client:
                items = await client.get_all_goods_safe(max_pages=max_pages)
            
            if items:
                # 保存数据
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(self.data_dir, f"buff_full_{timestamp}.json")
                
                # 计算实际页数
                actual_pages = len(items) // Config.BUFF_PAGE_SIZE
                if len(items) % Config.BUFF_PAGE_SIZE > 0:
                    actual_pages += 1
                
                data = {
                    'metadata': {
                        'platform': 'buff',
                        'total_count': len(items),
                        'max_pages': max_pages or actual_pages,
                        'actual_pages': actual_pages,
                        'generated_at': datetime.now().isoformat(),
                        'api_config': {
                            'delay': Config.BUFF_API_DELAY,
                            'page_size': Config.BUFF_PAGE_SIZE
                        },
                        'collection_type': 'full' if max_pages is None else 'limited'
                    },
                    'items': items
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                file_size = os.path.getsize(filename) / 1024 / 1024  # MB
                
                print(f"   ✅ Buff数据收集完成:")
                print(f"      商品数量: {len(items)}")
                print(f"      实际页数: {actual_pages}")
                print(f"      文件大小: {file_size:.1f} MB")
                print(f"      保存位置: {filename}")
                
                # 显示价格分布
                self.analyze_buff_price_distribution(items)
                
            else:
                print("   ❌ Buff数据收集失败")
                
        except Exception as e:
            logger.error(f"收集Buff数据失败: {e}")
    
    async def collect_youpin_data(self, max_pages: int = None):
        """收集悠悠有品完整数据"""
        try:
            print(f"\n🛍️ 开始收集悠悠有品数据...")
            if max_pages:
                print(f"   最大页数: {max_pages}")
                print(f"   预计商品数: {max_pages * Config.YOUPIN_PAGE_SIZE}")
            else:
                print("   收集所有可用页面")
            
            async with OptimizedYoupinClient() as client:
                items = await client.get_all_items_safe(max_pages=max_pages)
            
            if items:
                # 保存数据
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(self.data_dir, f"youpin_full_{timestamp}.json")
                
                # 转换为可序列化的格式
                items_data = []
                for item in items:
                    if isinstance(item, dict):
                        items_data.append(item)
                    else:
                        items_data.append(item.__dict__ if hasattr(item, '__dict__') else str(item))
                
                # 计算实际页数
                actual_pages = len(items_data) // Config.YOUPIN_PAGE_SIZE
                if len(items_data) % Config.YOUPIN_PAGE_SIZE > 0:
                    actual_pages += 1
                
                data = {
                    'metadata': {
                        'platform': 'youpin',
                        'total_count': len(items_data),
                        'max_pages': max_pages or actual_pages,
                        'actual_pages': actual_pages,
                        'generated_at': datetime.now().isoformat(),
                        'api_config': {
                            'delay': Config.YOUPIN_API_DELAY,
                            'page_size': Config.YOUPIN_PAGE_SIZE
                        },
                        'collection_type': 'full' if max_pages is None else 'limited'
                    },
                    'items': items_data
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                file_size = os.path.getsize(filename) / 1024 / 1024  # MB
                
                print(f"   ✅ 悠悠有品数据收集完成:")
                print(f"      商品数量: {len(items_data)}")
                print(f"      实际页数: {actual_pages}")
                print(f"      文件大小: {file_size:.1f} MB")
                print(f"      保存位置: {filename}")
                
                # 显示价格分布
                self.analyze_youpin_price_distribution(items_data)
                
            else:
                print("   ❌ 悠悠有品数据收集失败")
                
        except Exception as e:
            logger.error(f"收集悠悠有品数据失败: {e}")
    
    def analyze_buff_price_distribution(self, items):
        """分析 Buff 价格分布"""
        try:
            prices = []
            for item in items:
                price_str = item.get('sell_min_price', '0')
                try:
                    price = float(price_str) if price_str else 0
                    if price > 0:
                        prices.append(price)
                except:
                    continue
            
            if prices:
                print(f"      价格分析 (共{len(prices)}个有效价格):")
                print(f"        最低价格: ¥{min(prices):.2f}")
                print(f"        最高价格: ¥{max(prices):.2f}")
                print(f"        平均价格: ¥{sum(prices)/len(prices):.2f}")
                
        except Exception as e:
            logger.warning(f"Buff价格分析失败: {e}")
    
    def analyze_youpin_price_distribution(self, items):
        """分析悠悠有品价格分布"""
        try:
            prices = []
            for item in items:
                price_str = item.get('price', '0')
                try:
                    price = float(price_str) if price_str else 0
                    if price > 0:
                        prices.append(price)
                except:
                    continue
            
            if prices:
                print(f"      价格分析 (共{len(prices)}个有效价格):")
                print(f"        最低价格: ¥{min(prices):.2f}")
                print(f"        最高价格: ¥{max(prices):.2f}")
                print(f"        平均价格: ¥{sum(prices)/len(prices):.2f}")
                
        except Exception as e:
            logger.warning(f"悠悠有品价格分析失败: {e}")

async def main():
    """主函数"""
    print("🚀 完整数据收集器")
    print("=" * 60)
    
    collector = FullDataCollector()
    
    # 显示当前配置
    print(f"📋 当前配置:")
    print(f"   Buff最大页数: {Config.BUFF_MAX_PAGES}")
    print(f"   悠悠有品最大页数: {Config.YOUPIN_MAX_PAGES}")
    print(f"   Buff页大小: {Config.BUFF_PAGE_SIZE}")
    print(f"   悠悠有品页大小: {Config.YOUPIN_PAGE_SIZE}")
    print(f"   预计Buff商品数: {Config.BUFF_MAX_PAGES * Config.BUFF_PAGE_SIZE}")
    print(f"   预计悠悠有品商品数: {Config.YOUPIN_MAX_PAGES * Config.YOUPIN_PAGE_SIZE}")
    
    # 开始收集
    await collector.collect_all_data(use_config_limits=True)

if __name__ == "__main__":
    asyncio.run(main()) 