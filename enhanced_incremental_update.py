#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强增量更新 - 支持将增量结果合并到全量数据
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import asdict

from search_api_client import SearchResult
from config import Config

logger = logging.getLogger(__name__)

class EnhancedIncrementalUpdate:
    """增强的增量更新器 - 支持合并到全量数据"""
    
    def __init__(self):
        self.data_dir = "data"
        self.buff_full_file = os.path.join(self.data_dir, "buff_full.json")
        self.youpin_full_file = os.path.join(self.data_dir, "youpin_full.json")
    
    def merge_search_results_to_full_data(self, search_results: Dict[str, List[SearchResult]]):
        """将搜索结果合并到全量数据文件中"""
        
        # 合并到Buff全量数据
        self._merge_to_buff_full_data(search_results.get('buff', []))
        
        # 合并到悠悠有品全量数据  
        self._merge_to_youpin_full_data(search_results.get('youpin', []))
    
    def _merge_to_buff_full_data(self, buff_results: List[SearchResult]):
        """合并到Buff全量数据"""
        if not buff_results or not os.path.exists(self.buff_full_file):
            return
        
        try:
            # 读取现有全量数据
            with open(self.buff_full_file, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            
            existing_items = full_data.get('items', [])
            
            # 创建现有商品的索引 (按ID和hash_name)
            existing_index = {}
            for i, item in enumerate(existing_items):
                item_id = str(item.get('id', ''))
                hash_name = item.get('market_hash_name', '')
                
                if item_id:
                    existing_index[f"id_{item_id}"] = i
                if hash_name:
                    existing_index[f"hash_{hash_name}"] = i
            
            # 合并新的搜索结果
            updates_count = 0
            additions_count = 0
            
            for result in buff_results:
                # 将SearchResult转换为Buff数据格式
                buff_item = {
                    'id': result.id,
                    'name': result.name,
                    'market_hash_name': result.hash_name,
                    'sell_min_price': str(result.price),
                    'goods_info': {
                        'icon_url': result.image_url
                    },
                    'last_updated': datetime.now().isoformat(),
                    'source': 'incremental_search'  # 标记来源
                }
                
                # 查找是否存在
                found_index = None
                if result.id:
                    found_index = existing_index.get(f"id_{result.id}")
                if found_index is None and result.hash_name:
                    found_index = existing_index.get(f"hash_{result.hash_name}")
                
                if found_index is not None:
                    # 更新现有商品
                    existing_items[found_index].update(buff_item)
                    updates_count += 1
                else:
                    # 添加新商品
                    existing_items.append(buff_item)
                    additions_count += 1
            
            # 更新元数据
            metadata = full_data.get('metadata', {})
            metadata.update({
                'total_count': len(existing_items),
                'last_incremental_merge': datetime.now().isoformat(),
                'incremental_updates': updates_count,
                'incremental_additions': additions_count
            })
            
            # 保存更新后的数据
            full_data['metadata'] = metadata
            full_data['items'] = existing_items
            
            with open(self.buff_full_file, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Buff全量数据已更新: 更新{updates_count}个, 新增{additions_count}个")
            
        except Exception as e:
            logger.error(f"合并Buff全量数据失败: {e}")
    
    def _merge_to_youpin_full_data(self, youpin_results: List[SearchResult]):
        """合并到悠悠有品全量数据"""
        if not youpin_results or not os.path.exists(self.youpin_full_file):
            return
        
        try:
            # 读取现有全量数据
            with open(self.youpin_full_file, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            
            existing_items = full_data.get('items', [])
            
            # 创建现有商品的索引
            existing_index = {}
            for i, item in enumerate(existing_items):
                item_id = str(item.get('commodityId', ''))
                hash_name = item.get('commodityHashName', '')
                
                if item_id:
                    existing_index[f"id_{item_id}"] = i
                if hash_name:
                    existing_index[f"hash_{hash_name}"] = i
            
            # 合并新的搜索结果
            updates_count = 0
            additions_count = 0
            
            for result in youpin_results:
                # 将SearchResult转换为悠悠有品数据格式
                youpin_item = {
                    'commodityId': result.id,
                    'commodityName': result.name,
                    'commodityHashName': result.hash_name,
                    'price': result.price,
                    'commodityUrl': result.image_url,
                    'last_updated': datetime.now().isoformat(),
                    'source': 'incremental_search'  # 标记来源
                }
                
                # 查找是否存在
                found_index = None
                if result.id:
                    found_index = existing_index.get(f"id_{result.id}")
                if found_index is None and result.hash_name:
                    found_index = existing_index.get(f"hash_{result.hash_name}")
                
                if found_index is not None:
                    # 更新现有商品
                    existing_items[found_index].update(youpin_item)
                    updates_count += 1
                else:
                    # 添加新商品
                    existing_items.append(youpin_item)
                    additions_count += 1
            
            # 更新元数据
            metadata = full_data.get('metadata', {})
            metadata.update({
                'total_count': len(existing_items),
                'last_incremental_merge': datetime.now().isoformat(),
                'incremental_updates': updates_count,
                'incremental_additions': additions_count
            })
            
            # 保存更新后的数据
            full_data['metadata'] = metadata
            full_data['items'] = existing_items
            
            with open(self.youpin_full_file, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 悠悠有品全量数据已更新: 更新{updates_count}个, 新增{additions_count}个")
            
        except Exception as e:
            logger.error(f"合并悠悠有品全量数据失败: {e}")
    
    def get_merge_status(self) -> Dict:
        """获取合并状态"""
        status = {
            'buff_full_exists': os.path.exists(self.buff_full_file),
            'youpin_full_exists': os.path.exists(self.youpin_full_file),
            'buff_last_merge': None,
            'youpin_last_merge': None,
            'buff_incremental_stats': {},
            'youpin_incremental_stats': {}
        }
        
        # 检查Buff文件状态
        if status['buff_full_exists']:
            try:
                with open(self.buff_full_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                metadata = data.get('metadata', {})
                status['buff_last_merge'] = metadata.get('last_incremental_merge')
                status['buff_incremental_stats'] = {
                    'updates': metadata.get('incremental_updates', 0),
                    'additions': metadata.get('incremental_additions', 0)
                }
            except Exception as e:
                logger.error(f"读取Buff状态失败: {e}")
        
        # 检查悠悠有品文件状态
        if status['youpin_full_exists']:
            try:
                with open(self.youpin_full_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                metadata = data.get('metadata', {})
                status['youpin_last_merge'] = metadata.get('last_incremental_merge')
                status['youpin_incremental_stats'] = {
                    'updates': metadata.get('incremental_updates', 0),
                    'additions': metadata.get('incremental_additions', 0)
                }
            except Exception as e:
                logger.error(f"读取悠悠有品状态失败: {e}")
        
        return status

# 测试功能
async def test_enhanced_incremental_update():
    """测试增强的增量更新"""
    print("🧪 测试增强增量更新")
    print("="*50)
    
    # 测试合并功能
    enhancer = EnhancedIncrementalUpdate()
    merge_status = enhancer.get_merge_status()
    
    print(f"全量数据文件状态:")
    print(f"  Buff文件存在: {merge_status['buff_full_exists']}")
    print(f"  悠悠有品文件存在: {merge_status['youpin_full_exists']}")
    
    if merge_status['buff_last_merge']:
        print(f"  上次Buff合并: {merge_status['buff_last_merge']}")
        print(f"  Buff增量统计: {merge_status['buff_incremental_stats']}")
    if merge_status['youpin_last_merge']:
        print(f"  上次悠悠有品合并: {merge_status['youpin_last_merge']}")
        print(f"  悠悠有品增量统计: {merge_status['youpin_incremental_stats']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_incremental_update()) 