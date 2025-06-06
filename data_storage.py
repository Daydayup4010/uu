#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据存储管理器
负责保存和加载两个平台的全量数据
"""

import json
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import logging

from integrated_price_system import PriceDiffItem
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient
from config import Config

logger = logging.getLogger(__name__)

class DataStorage:
    """数据存储管理器"""
    
    def __init__(self):
        self.data_dir = Config.DATA_DIR
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_price_diff_data(self, diff_items: List[PriceDiffItem], 
                           metadata: Dict = None) -> bool:
        """保存价差数据"""
        try:
            # 转换为可序列化的格式
            items_data = []
            for item in diff_items:
                items_data.append({
                    'id': item.id,
                    'name': item.name,
                    'buff_price': item.buff_price,
                    'youpin_price': item.youpin_price,
                    'price_diff': item.price_diff,
                    'profit_rate': item.profit_rate,
                    'buff_url': item.buff_url,
                    'youpin_url': item.youpin_url,
                    'image_url': item.image_url,
                    'category': item.category,
                    'last_updated': item.last_updated.isoformat() if item.last_updated else None
                })
            
            data = {
                'metadata': {
                    'total_count': len(items_data),
                    'generated_at': datetime.now().isoformat(),
                    'config': {
                        'price_diff_min': Config.PRICE_DIFF_MIN,
                        'price_diff_max': Config.PRICE_DIFF_MAX,
                        'buff_price_min': Config.BUFF_PRICE_MIN,
                        'buff_price_max': Config.BUFF_PRICE_MAX,
                        'max_output_items': Config.MAX_OUTPUT_ITEMS
                    },
                    **(metadata or {})
                },
                'items': items_data
            }
            
            # 保存到最新数据文件
            with open(Config.LATEST_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存到带时间戳的备份文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.data_dir, f"price_diff_{timestamp}.json")
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 已保存 {len(items_data)} 个价差商品到文件")
            return True
            
        except Exception as e:
            logger.error(f"保存价差数据失败: {e}")
            return False
    
    def load_latest_price_diff_data(self) -> List[PriceDiffItem]:
        """加载最新的价差数据"""
        try:
            if os.path.exists(Config.LATEST_DATA_FILE):
                with open(Config.LATEST_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换为PriceDiffItem对象
                loaded_items = []
                for item_data in data.get('items', []):
                    try:
                        item = PriceDiffItem(
                            id=item_data.get('id', ''),
                            name=item_data.get('name', ''),
                            buff_price=float(item_data.get('buff_price', 0)),
                            youpin_price=float(item_data.get('youpin_price', 0)),
                            price_diff=float(item_data.get('price_diff', 0)),
                            profit_rate=float(item_data.get('profit_rate', 0)),
                            buff_url=item_data.get('buff_url', ''),
                            youpin_url=item_data.get('youpin_url', ''),
                            image_url=item_data.get('image_url', ''),
                            category=item_data.get('category', ''),
                            last_updated=datetime.fromisoformat(item_data['last_updated']) if item_data.get('last_updated') else datetime.now()
                        )
                        loaded_items.append(item)
                    except Exception as e:
                        logger.warning(f"解析商品数据失败: {e}")
                        continue
                
                logger.info(f"📊 已加载 {len(loaded_items)} 个价差商品")
                return loaded_items
            else:
                logger.info("未找到价差数据文件")
                return []
                
        except Exception as e:
            logger.error(f"加载价差数据失败: {e}")
            return []
    
    async def save_full_platform_data(self, max_pages: int = None):
        """获取并保存两个平台的全量数据"""
        if max_pages is None:
            max_pages = 10  # 限制页数避免过度获取
        
        logger.info(f"🔄 开始获取两个平台的全量数据 (最多{max_pages}页)")
        
        # 保存Buff全量数据
        await self._save_buff_full_data(max_pages)
        
        # 等待一下避免请求过快
        await asyncio.sleep(3)
        
        # 保存悠悠有品全量数据
        await self._save_youpin_full_data(max_pages)
        
        logger.info("✅ 两个平台全量数据保存完成")
    
    async def _save_buff_full_data(self, max_pages: int):
        """保存Buff全量数据"""
        try:
            logger.info(f"🔥 开始获取Buff全量数据...")
            
            async with OptimizedBuffClient() as client:
                items = await client.get_all_goods_safe(max_pages=max_pages)
            
            if items:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(self.data_dir, f"buff_full_{timestamp}.json")
                
                data = {
                    'metadata': {
                        'platform': 'buff',
                        'total_count': len(items),
                        'max_pages': max_pages,
                        'generated_at': datetime.now().isoformat(),
                        'api_config': {
                            'delay': Config.BUFF_API_DELAY,
                            'page_size': Config.BUFF_PAGE_SIZE
                        }
                    },
                    'items': items
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"💾 Buff全量数据已保存: {len(items)}个商品 -> {filename}")
            else:
                logger.warning("❌ Buff全量数据获取失败")
                
        except Exception as e:
            logger.error(f"保存Buff全量数据失败: {e}")
    
    async def _save_youpin_full_data(self, max_pages: int):
        """保存悠悠有品全量数据"""
        try:
            logger.info(f"🛍️ 开始获取悠悠有品全量数据...")
            
            async with OptimizedYoupinClient() as client:
                items = await client.get_all_items_safe(max_pages=max_pages)
            
            if items:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(self.data_dir, f"youpin_full_{timestamp}.json")
                
                # 转换为可序列化的格式
                items_data = []
                for item in items:
                    if isinstance(item, dict):
                        items_data.append(item)
                    else:
                        # 如果是其他类型，尝试转换
                        items_data.append(item.__dict__ if hasattr(item, '__dict__') else str(item))
                
                data = {
                    'metadata': {
                        'platform': 'youpin',
                        'total_count': len(items_data),
                        'max_pages': max_pages,
                        'generated_at': datetime.now().isoformat(),
                        'api_config': {
                            'delay': Config.YOUPIN_API_DELAY,
                            'page_size': Config.YOUPIN_PAGE_SIZE
                        }
                    },
                    'items': items_data
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"💾 悠悠有品全量数据已保存: {len(items_data)}个商品 -> {filename}")
            else:
                logger.warning("❌ 悠悠有品全量数据获取失败")
                
        except Exception as e:
            logger.error(f"保存悠悠有品全量数据失败: {e}")
    
    def get_latest_files_info(self) -> Dict:
        """获取最新文件信息"""
        info = {
            'price_diff_file': None,
            'buff_full_files': [],
            'youpin_full_files': []
        }
        
        try:
            if os.path.exists(Config.LATEST_DATA_FILE):
                stat = os.stat(Config.LATEST_DATA_FILE)
                info['price_diff_file'] = {
                    'path': Config.LATEST_DATA_FILE,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            
            # 查找所有备份文件
            for filename in os.listdir(self.data_dir):
                if filename.startswith('buff_full_') and filename.endswith('.json'):
                    filepath = os.path.join(self.data_dir, filename)
                    stat = os.stat(filepath)
                    info['buff_full_files'].append({
                        'filename': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                elif filename.startswith('youpin_full_') and filename.endswith('.json'):
                    filepath = os.path.join(self.data_dir, filename)
                    stat = os.stat(filepath)
                    info['youpin_full_files'].append({
                        'filename': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # 按修改时间排序
            info['buff_full_files'].sort(key=lambda x: x['modified'], reverse=True)
            info['youpin_full_files'].sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
        
        return info

# 测试功能
async def test_data_storage():
    """测试数据存储功能"""
    print("🧪 测试数据存储功能")
    print("="*50)
    
    storage = DataStorage()
    
    # 测试获取全量数据
    print("📊 获取两个平台全量数据...")
    await storage.save_full_platform_data(max_pages=2)
    
    # 显示文件信息
    print("\n📁 文件信息:")
    info = storage.get_latest_files_info()
    
    if info['price_diff_file']:
        print(f"价差数据: {info['price_diff_file']['path']}")
    
    print(f"Buff文件: {len(info['buff_full_files'])}个")
    for file_info in info['buff_full_files'][:3]:  # 显示最新3个
        print(f"  - {file_info['filename']} ({file_info['size']} bytes)")
    
    print(f"悠悠有品文件: {len(info['youpin_full_files'])}个")
    for file_info in info['youpin_full_files'][:3]:  # 显示最新3个
        print(f"  - {file_info['filename']} ({file_info['size']} bytes)")

if __name__ == "__main__":
    asyncio.run(test_data_storage()) 