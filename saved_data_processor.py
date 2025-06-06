#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从已保存数据重新处理筛选 - 修复版本

当筛选条件更新时，从已保存的全量数据中重新筛选，避免重复API调用
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from models import PriceDiffItem, SkinItem
from config import Config

logger = logging.getLogger(__name__)

class SavedDataProcessor:
    """从已保存数据重新处理筛选"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
    
    def get_latest_full_data_files(self) -> Dict[str, Optional[str]]:
        """获取最新的全量数据文件"""
        buff_files = []
        youpin_files = []
        
        try:
            if not os.path.exists(self.data_dir):
                logger.warning(f"数据目录不存在: {self.data_dir}")
                return {'buff_file': None, 'youpin_file': None}
            
            for filename in os.listdir(self.data_dir):
                if filename.startswith('buff_full_') and filename.endswith('.json'):
                    buff_files.append(filename)
                elif filename.startswith('youpin_full_') and filename.endswith('.json'):
                    youpin_files.append(filename)
            
            # 按时间戳排序，获取最新的
            buff_files.sort(reverse=True)
            youpin_files.sort(reverse=True)
            
            result = {
                'buff_file': buff_files[0] if buff_files else None,
                'youpin_file': youpin_files[0] if youpin_files else None
            }
            
            if result['buff_file'] and result['youpin_file']:
                logger.info(f"📂 找到最新数据文件: Buff={result['buff_file']}, 悠悠有品={result['youpin_file']}")
            else:
                logger.warning(f"⚠️ 缺少全量数据文件: Buff={result['buff_file']}, 悠悠有品={result['youpin_file']}")
            
            return result
            
        except Exception as e:
            logger.error(f"获取全量数据文件列表失败: {e}")
            return {'buff_file': None, 'youpin_file': None}
    
    def load_saved_data(self, filepath: str) -> Optional[Dict]:
        """加载已保存的数据文件"""
        try:
            full_path = os.path.join(self.data_dir, filepath)
            if not os.path.exists(full_path):
                logger.error(f"数据文件不存在: {full_path}")
                return None
                
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items_count = len(data.get('items', []))
            logger.info(f"✅ 加载数据文件: {filepath} ({items_count}个商品)")
            return data
            
        except Exception as e:
            logger.error(f"加载数据文件失败 {filepath}: {e}")
            return None
    
    def has_valid_full_data(self) -> bool:
        """检查是否有有效的全量数据文件"""
        files = self.get_latest_full_data_files()
        return files['buff_file'] is not None and files['youpin_file'] is not None
    
    def reprocess_with_current_filters(self) -> Tuple[List[PriceDiffItem], Dict]:
        """使用当前筛选条件重新处理已保存的数据"""
        logger.info("🔄 开始从已保存数据重新筛选...")
        
        # 1. 获取最新的数据文件
        files = self.get_latest_full_data_files()
        buff_file = files['buff_file']
        youpin_file = files['youpin_file']
        
        if not buff_file or not youpin_file:
            logger.warning("❌ 缺少全量数据文件，无法重新筛选")
            return [], {'error': '缺少全量数据文件，请先执行全量更新'}
        
        # 2. 加载数据
        buff_data = self.load_saved_data(buff_file)
        youpin_data = self.load_saved_data(youpin_file)
        
        if not buff_data or not youpin_data:
            logger.error("❌ 数据文件加载失败")
            return [], {'error': '数据文件加载失败'}
        
        buff_items = buff_data.get('items', [])
        youpin_items = youpin_data.get('items', [])
        
        logger.info(f"📊 加载数据: Buff {len(buff_items)}个, 悠悠有品 {len(youpin_items)}个")
        
        # 3. 重新执行筛选分析
        diff_items, stats = self._analyze_with_current_filters(buff_items, youpin_items)
        
        # 4. 添加文件信息到统计
        stats.update({
            'buff_file': buff_file,
            'youpin_file': youpin_file,
            'buff_file_time': buff_data.get('metadata', {}).get('generated_at'),
            'youpin_file_time': youpin_data.get('metadata', {}).get('generated_at'),
            'reprocessed_at': datetime.now().isoformat()
        })
        
        logger.info(f"✅ 重新筛选完成: 符合条件的商品 {len(diff_items)}个")
        
        return diff_items, stats
    
    def _analyze_with_current_filters(self, buff_items: List[Dict], youpin_items: List[Dict]) -> Tuple[List[PriceDiffItem], Dict]:
        """使用当前筛选条件分析数据"""
        diff_items = []
        stats = {
            'total_buff_items': len(buff_items),
            'total_youpin_items': len(youpin_items),
            'processed_count': 0,
            'found_count': 0,
            'hash_match_count': 0,
            'name_match_count': 0,
            'price_filtered_count': 0,
            'sell_num_filtered_count': 0,
            'final_count': 0,
            'creation_errors': 0
        }
        
        # 建立悠悠有品价格映射
        youpin_hash_map = {}
        youpin_name_map = {}
        
        for item in youpin_items:
            hash_name = item.get('commodityHashName', '')
            commodity_name = item.get('commodityName', '')
            price = item.get('price', 0)
            
            if hash_name and price:
                try:
                    youpin_hash_map[hash_name] = float(price)
                except (ValueError, TypeError):
                    continue
            
            if commodity_name and price:
                try:
                    youpin_name_map[commodity_name] = float(price)
                except (ValueError, TypeError):
                    continue
        
        logger.info(f"📈 建立映射表: Hash映射{len(youpin_hash_map)}个, 名称映射{len(youpin_name_map)}个")
        
        # 处理Buff商品
        for item_data in buff_items:
            stats['processed_count'] += 1
            
            # 解析基本信息
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
            
            # 🔥 应用Buff价格筛选
            if not Config.is_buff_price_in_range(buff_price):
                stats['price_filtered_count'] += 1
                continue
            
            # 🔥 应用Buff在售数量筛选
            if not Config.is_buff_sell_num_valid(sell_num):
                stats['sell_num_filtered_count'] += 1
                continue
            
            # 查找悠悠有品价格
            youpin_price = None
            matched_by = None
            
            # 优先Hash匹配
            if hash_name and hash_name in youpin_hash_map:
                youpin_price = youpin_hash_map[hash_name]
                matched_by = "Hash精确匹配"
                stats['hash_match_count'] += 1
                stats['found_count'] += 1
            # 备用名称匹配
            elif buff_name in youpin_name_map:
                youpin_price = youpin_name_map[buff_name]
                matched_by = "名称精确匹配"
                stats['name_match_count'] += 1
                stats['found_count'] += 1
            
            if not youpin_price:
                continue
            
            # 计算价差
            price_diff = youpin_price - buff_price
            profit_rate = (price_diff / buff_price) * 100 if buff_price > 0 else 0
            
            # 🔥 应用价差区间筛选
            if Config.is_price_diff_in_range(price_diff):
                try:
                    # 🔥 修复：正确创建SkinItem和PriceDiffItem
                    skin_item = SkinItem(
                        id=buff_id,
                        name=buff_name,
                        buff_price=buff_price,
                        youpin_price=youpin_price,
                        buff_url=f"https://buff.163.com/goods/{buff_id}",
                        youpin_url=f"https://www.youpin898.com/search?keyword={buff_name}",
                        image_url=item_data.get('goods_info', {}).get('icon_url', ''),
                        hash_name=hash_name,
                        sell_num=sell_num,
                        category="重新筛选",
                        last_updated=datetime.now()
                    )
                    
                    diff_item = PriceDiffItem(
                        skin_item=skin_item,
                        price_diff=price_diff,
                        profit_rate=profit_rate,
                        buff_buy_url=f"https://buff.163.com/goods/{buff_id}"
                    )
                    
                    diff_items.append(diff_item)
                    stats['final_count'] += 1
                    
                except Exception as e:
                    logger.error(f"创建PriceDiffItem失败: {e}")
                    logger.error(f"商品数据: id={buff_id}, name={buff_name}, buff_price={buff_price}, youpin_price={youpin_price}")
                    stats['creation_errors'] += 1
                    continue
        
        # 按利润率排序
        diff_items.sort(key=lambda x: x.profit_rate, reverse=True)
        
        # 限制输出数量
        original_count = len(diff_items)
        if len(diff_items) > Config.MAX_OUTPUT_ITEMS:
            diff_items = diff_items[:Config.MAX_OUTPUT_ITEMS]
            stats['limited_output'] = True
            stats['original_final_count'] = original_count
        else:
            stats['limited_output'] = False
        
        # 添加筛选条件信息
        stats['filters_applied'] = {
            'price_diff_range': f"{Config.PRICE_DIFF_MIN}-{Config.PRICE_DIFF_MAX}元",
            'buff_price_range': f"{Config.BUFF_PRICE_MIN}-{Config.BUFF_PRICE_MAX}元",
            'buff_sell_num_min': Config.get_buff_sell_num_min(),
            'max_output_items': Config.MAX_OUTPUT_ITEMS
        }
        
        logger.info(f"📊 筛选统计:")
        logger.info(f"   处理商品: {stats['processed_count']}个")
        logger.info(f"   价格筛选过滤: {stats['price_filtered_count']}个")
        logger.info(f"   在售数量过滤: {stats['sell_num_filtered_count']}个")
        logger.info(f"   找到匹配: {stats['found_count']}个 (Hash:{stats['hash_match_count']}, 名称:{stats['name_match_count']})")
        logger.info(f"   符合价差条件: {stats['final_count']}个")
        if stats['creation_errors'] > 0:
            logger.warning(f"   创建错误: {stats['creation_errors']}个")
        
        return diff_items, stats

# 全局实例
_saved_data_processor = None

def get_saved_data_processor() -> SavedDataProcessor:
    """获取全局的保存数据处理器实例"""
    global _saved_data_processor
    if _saved_data_processor is None:
        _saved_data_processor = SavedDataProcessor()
    return _saved_data_processor 