#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的增量更新管理器

解决问题：
1. 增量更新后价格没有更新 - 直接更新全量数据文件
2. 缺少完成标识 - 添加详细的完成状态和进度
"""

import json
import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional

from update_manager import get_update_manager
from search_api_client import SearchManager
from config import Config

# 🔥 使用增强的日志配置
try:
    from log_config import setup_logging
    logger = setup_logging(log_level='INFO', app_name='enhanced_update_manager')
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class EnhancedIncrementalUpdater:
    """增强的增量更新器"""
    
    def __init__(self):
        self.update_manager = get_update_manager()
        self.status = {
            'is_running': False,
            'start_time': None,
            'end_time': None,
            'processed_count': 0,
            'updated_count': 0,
            'error_count': 0,
            'current_task': '',
            'completion_percentage': 0
        }
    
    async def run_enhanced_incremental_update(self) -> Dict:
        """运行增强的增量更新"""
        logger.info("🚀 开始增强增量更新")
        
        self.status = {
            'is_running': True,
            'start_time': datetime.now(),
            'end_time': None,
            'processed_count': 0,
            'updated_count': 0,
            'error_count': 0,
            'current_task': '准备中...',
            'completion_percentage': 0
        }
        
        try:
            # 1. 获取缓存的关键词
            self.status['current_task'] = '加载缓存关键词'
            hashnames = self.update_manager.hashname_cache.get_hashnames_for_search()
            
            if not hashnames:
                return self._complete_with_error("没有可搜索的关键词")
            
            logger.info(f"📝 准备更新 {len(hashnames)} 个商品的价格")
            
            # 2. 加载全量数据
            self.status['current_task'] = '加载全量数据文件'
            self.status['completion_percentage'] = 10
            
            buff_data, youpin_data = self._load_full_data()
            if not buff_data or not youpin_data:
                return self._complete_with_error("无法加载全量数据文件")
            
            # 3. 执行价格更新
            self.status['current_task'] = '搜索最新价格'
            self.status['completion_percentage'] = 20
            
            price_updates = await self._update_prices(hashnames, buff_data, youpin_data)
            
            # 4. 保存更新后的数据
            self.status['current_task'] = '保存更新数据'
            self.status['completion_percentage'] = 80
            
            await self._save_updated_data(buff_data, youpin_data, price_updates)
            
            # 5. 重新分析价差
            self.status['current_task'] = '重新分析价差'
            self.status['completion_percentage'] = 90
            
            await self._refresh_price_analysis()
            
            # 6. 完成
            return self._complete_successfully(price_updates)
            
        except Exception as e:
            logger.error(f"❌ 增量更新失败: {e}")
            return self._complete_with_error(f"更新失败: {e}")
    
    def _load_full_data(self) -> tuple:
        """加载全量数据文件"""
        try:
            buff_data = None
            youpin_data = None
            
            if os.path.exists('data/buff_full.json'):
                with open('data/buff_full.json', 'r', encoding='utf-8') as f:
                    buff_data = json.load(f)
            
            if os.path.exists('data/youpin_full.json'):
                with open('data/youpin_full.json', 'r', encoding='utf-8') as f:
                    youpin_data = json.load(f)
            
            return buff_data, youpin_data
            
        except Exception as e:
            logger.error(f"加载全量数据失败: {e}")
            return None, None
    
    async def _update_prices(self, hashnames: List[str], buff_data: Dict, youpin_data: Dict) -> Dict:
        """更新商品价格"""
        price_updates = {
            'buff_updates': 0,
            'youpin_updates': 0,
            'details': []
        }
        
        # 创建索引以快速查找
        buff_index = {}
        youpin_index = {}
        
        for i, item in enumerate(buff_data.get('items', [])):
            key = item.get('hash_name') or item.get('name', '')
            if key:
                buff_index[key] = i
        
        for i, item in enumerate(youpin_data.get('items', [])):
            key = item.get('hash_name') or item.get('name', '')
            if key:
                youpin_index[key] = i
        
        async with SearchManager() as search_manager:
            semaphore = asyncio.Semaphore(3)  # 限制并发
            
            async def update_single_item(keyword):
                async with semaphore:
                    try:
                        self.status['processed_count'] += 1
                        
                        # 更新进度
                        progress = min(20 + (self.status['processed_count'] / len(hashnames)) * 60, 80)
                        self.status['completion_percentage'] = int(progress)
                        
                        # 搜索最新价格
                        results = await search_manager.search_both_platforms(keyword)
                        
                        # 处理Buff结果
                        for buff_item in results.get('buff', []):
                            key = buff_item.hash_name or buff_item.name
                            if key and key in buff_index:
                                old_price = buff_data['items'][buff_index[key]].get('price', 0)
                                new_price = buff_item.price
                                
                                if abs(old_price - new_price) > 0.001:  # 价格有变化
                                    buff_data['items'][buff_index[key]]['price'] = new_price
                                    buff_data['items'][buff_index[key]]['last_updated'] = datetime.now().isoformat()
                                    
                                    price_updates['buff_updates'] += 1
                                    price_updates['details'].append({
                                        'platform': 'buff',
                                        'name': key,
                                        'old_price': old_price,
                                        'new_price': new_price
                                    })
                                    
                                    logger.info(f"🔄 Buff价格更新: {key} ¥{old_price} -> ¥{new_price}")
                        
                        # 处理悠悠有品结果
                        for youpin_item in results.get('youpin', []):
                            key = youpin_item.hash_name or youpin_item.name
                            if key and key in youpin_index:
                                old_price = youpin_data['items'][youpin_index[key]].get('price', 0)
                                new_price = youpin_item.price
                                
                                if abs(old_price - new_price) > 0.001:  # 价格有变化
                                    youpin_data['items'][youpin_index[key]]['price'] = new_price
                                    youpin_data['items'][youpin_index[key]]['last_updated'] = datetime.now().isoformat()
                                    
                                    price_updates['youpin_updates'] += 1
                                    price_updates['details'].append({
                                        'platform': 'youpin',
                                        'name': key,
                                        'old_price': old_price,
                                        'new_price': new_price
                                    })
                                    
                                    logger.info(f"🔄 悠悠价格更新: {key} ¥{old_price} -> ¥{new_price}")
                        
                        self.status['updated_count'] = price_updates['buff_updates'] + price_updates['youpin_updates']
                        
                    except Exception as e:
                        logger.error(f"更新商品价格失败 {keyword}: {e}")
                        self.status['error_count'] += 1
            
            # 批量处理
            batch_size = 15
            for i in range(0, len(hashnames), batch_size):
                batch = hashnames[i:i + batch_size]
                tasks = [update_single_item(keyword) for keyword in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # 进度提示
                logger.info(f"⏳ 已处理 {min(i + batch_size, len(hashnames))}/{len(hashnames)} 个商品")
                
                # 批次间延迟
                await asyncio.sleep(1)
        
        return price_updates
    
    async def _save_updated_data(self, buff_data: Dict, youpin_data: Dict, price_updates: Dict):
        """保存更新后的数据"""
        try:
            # 更新元数据
            now = datetime.now().isoformat()
            
            if price_updates['buff_updates'] > 0:
                buff_data['metadata'] = buff_data.get('metadata', {})
                buff_data['metadata']['last_incremental_update'] = now
                buff_data['metadata']['incremental_price_updates'] = price_updates['buff_updates']
                
                with open('data/buff_full.json', 'w', encoding='utf-8') as f:
                    json.dump(buff_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"💾 已保存Buff数据，更新了 {price_updates['buff_updates']} 个价格")
            
            if price_updates['youpin_updates'] > 0:
                youpin_data['metadata'] = youpin_data.get('metadata', {})
                youpin_data['metadata']['last_incremental_update'] = now
                youpin_data['metadata']['incremental_price_updates'] = price_updates['youpin_updates']
                
                with open('data/youpin_full.json', 'w', encoding='utf-8') as f:
                    json.dump(youpin_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"💾 已保存悠悠有品数据，更新了 {price_updates['youpin_updates']} 个价格")
        
        except Exception as e:
            logger.error(f"保存更新数据失败: {e}")
            raise
    
    async def _refresh_price_analysis(self):
        """重新分析价差"""
        try:
            from saved_data_processor import SavedDataProcessor
            
            processor = SavedDataProcessor()
            new_diff_items, stats = await processor.process_saved_data()
            
            if new_diff_items:
                # 更新UpdateManager中的数据
                self.update_manager.current_diff_items = new_diff_items
                self.update_manager._save_current_data()
                
                logger.info(f"🔄 重新分析完成，发现 {len(new_diff_items)} 个价差商品")
            
        except Exception as e:
            logger.error(f"重新分析价差失败: {e}")
    
    def _complete_successfully(self, price_updates: Dict) -> Dict:
        """成功完成更新"""
        self.status['is_running'] = False
        self.status['end_time'] = datetime.now()
        self.status['current_task'] = '更新完成'
        self.status['completion_percentage'] = 100
        
        duration = (self.status['end_time'] - self.status['start_time']).total_seconds()
        
        # 更新UpdateManager的时间戳
        self.update_manager.last_incremental_update = self.status['end_time']
        
        result = {
            'success': True,
            'message': f"✅ 增量更新完成",
            'duration_seconds': duration,
            'statistics': {
                'processed_count': self.status['processed_count'],
                'updated_count': self.status['updated_count'],
                'buff_updates': price_updates['buff_updates'],
                'youpin_updates': price_updates['youpin_updates'],
                'error_count': self.status['error_count']
            },
            'completion_time': self.status['end_time'].isoformat()
        }
        
        logger.info(f"✅ 增量更新完成")
        logger.info(f"📊 统计: 处理{result['statistics']['processed_count']}个商品, "
                   f"更新{result['statistics']['updated_count']}个价格, "
                   f"耗时{duration:.1f}秒")
        
        return result
    
    def _complete_with_error(self, error_message: str) -> Dict:
        """错误完成更新"""
        self.status['is_running'] = False
        self.status['end_time'] = datetime.now()
        self.status['current_task'] = f'错误: {error_message}'
        
        return {
            'success': False,
            'message': f"❌ {error_message}",
            'statistics': {
                'processed_count': self.status['processed_count'],
                'updated_count': self.status['updated_count'],
                'error_count': self.status['error_count']
            }
        }
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return self.status.copy()

# 全局实例
_enhanced_updater = None

def get_enhanced_updater() -> EnhancedIncrementalUpdater:
    """获取增强更新器实例"""
    global _enhanced_updater
    if _enhanced_updater is None:
        _enhanced_updater = EnhancedIncrementalUpdater()
    return _enhanced_updater

if __name__ == "__main__":
    async def test():
        updater = get_enhanced_updater()
        result = await updater.run_enhanced_incremental_update()
        print(f"结果: {result}")
    
    asyncio.run(test()) 