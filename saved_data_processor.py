#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从已保存数据重新处理筛选 - 修复版本

当筛选条件更新时，从已保存的全量数据中重新筛选，避免重复API调用
"""

import json
import os
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from models import PriceDiffItem, SkinItem
from config import Config

# 导入改进的匹配器（避免循环导入，这里重新定义）
import re
from difflib import SequenceMatcher

class ImprovedMatcher:
    """改进的商品匹配器（本地版本）"""
    
    def __init__(self):
        self.exact_matches = 0
        self.normalized_matches = 0
        self.weapon_matches = 0
        self.fuzzy_matches = 0
        self.no_matches = 0
    
    def normalize_hash_name(self, hash_name: str) -> str:
        """规范化Hash名称"""
        if not hash_name:
            return ""
        
        # 1. 移除多余空格
        normalized = re.sub(r'\s+', ' ', hash_name.strip())
        
        # 2. 统一特殊字符
        normalized = normalized.replace('（', '(').replace('）', ')')
        normalized = normalized.replace('｜', '|')
        
        return normalized
    
    # 🚫 已禁用此方法 - 移除磨损等级和StatTrak标记会导致价格匹配错误
    # def extract_weapon_name(self, hash_name: str) -> str:
    #     """提取武器名称（去除磨损等级）"""
    #     if not hash_name:
    #         return ""
    #     
    #     # 移除磨损等级
    #     weapon_name = re.sub(r'\s*\([^)]*\)\s*$', '', hash_name)
    #     
    #     # 移除 StatTrak™ 标记进行更广泛的匹配
    #     weapon_name_no_stattrak = re.sub(r'StatTrak™?\s*', '', weapon_name)
    #     
    #     return weapon_name_no_stattrak.strip()
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度"""
        if not str1 or not str2:
            return 0.0
        
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def find_best_match(self, buff_hash: str, youpin_hashes: Set[str], 
                       youpin_price_map: Dict[str, float]) -> Optional[Tuple[float, str, str]]:
        """为Buff商品找到最佳匹配的悠悠有品商品"""
        if not buff_hash or not youpin_hashes:
            return None
        
        # 1. 精确匹配
        if buff_hash in youpin_hashes and buff_hash in youpin_price_map:
            self.exact_matches += 1
            return (youpin_price_map[buff_hash], "精确匹配", buff_hash)
        
        # 2. 规范化后精确匹配
        normalized_buff = self.normalize_hash_name(buff_hash)
        for youpin_hash in youpin_hashes:
            normalized_youpin = self.normalize_hash_name(youpin_hash)
            if normalized_buff == normalized_youpin and youpin_hash in youpin_price_map:
                self.normalized_matches += 1
                return (youpin_price_map[youpin_hash], "规范化匹配", youpin_hash)
        
        # 🚫 第3种匹配已禁用 - 移除磨损等级和StatTrak标记会导致价格匹配错误
        # 磨损等级（Field-Tested, Minimal Wear等）和StatTrak™标记是影响价格的核心特征
        # 移除这些特征会导致匹配到错误的商品，造成严重的价格判断错误
        
        # 🔥 禁用所有可能造成错误匹配的算法 - 只保留精确匹配
        # 对于24K+商品，模糊匹配会导致5亿次计算，性能极差
        # 同时移除磨损等级等重要特征会造成价格匹配错误
        
        # # 3. 武器名称匹配（去除磨损等级）  -- 已禁用，会造成价格错误
        # # 4. 高相似度模糊匹配（90%以上相似度）  -- 已禁用，性能问题  
        # # 5. 武器名称模糊匹配（85%以上相似度）  -- 已禁用，性能问题
        
        # 没有找到匹配
        self.no_matches += 1
        return None
    
    def find_best_match_fast(self, buff_hash: str, youpin_price_map: Dict[str, float], 
                            normalized_youpin_map: Dict[str, List[str]]) -> Optional[Tuple[float, str, str]]:
        """🚀 高性能匹配方法：使用预建索引进行快速匹配"""
        if not buff_hash:
            return None
        
        # 1. 精确匹配 - O(1)复杂度
        if buff_hash in youpin_price_map:
            self.exact_matches += 1
            return (youpin_price_map[buff_hash], "精确匹配", buff_hash)
        
        # 2. 规范化匹配 - O(1)复杂度查找，不需要遍历
        normalized_buff = self.normalize_hash_name(buff_hash)
        candidate_hashes = normalized_youpin_map.get(normalized_buff, [])
        
        for youpin_hash in candidate_hashes:
            if youpin_hash in youpin_price_map:
                self.normalized_matches += 1
                return (youpin_price_map[youpin_hash], "规范化匹配", youpin_hash)
        
        # 没有找到匹配
        self.no_matches += 1
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """获取匹配统计信息"""
        total = self.exact_matches + self.normalized_matches + self.weapon_matches + self.fuzzy_matches + self.no_matches
        
        return {
            'total_processed': total,
            'exact_matches': self.exact_matches,
            'normalized_matches': self.normalized_matches,
            'weapon_matches': self.weapon_matches,
            'fuzzy_matches': self.fuzzy_matches,
            'no_matches': self.no_matches,
            'total_matches': total - self.no_matches,
            'match_rate': ((total - self.no_matches) / total * 100) if total > 0 else 0
        }

logger = logging.getLogger(__name__)

class SavedDataProcessor:
    """从已保存数据重新处理筛选"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
    
    def get_latest_full_data_files(self) -> Dict[str, Optional[str]]:
        """获取全量数据文件（支持新旧两种命名方式）"""
        try:
            if not os.path.exists(self.data_dir):
                logger.warning(f"数据目录不存在: {self.data_dir}")
                return {'buff_file': None, 'youpin_file': None}
            
            # 优先查找新的固定文件名
            buff_file = "buff_full.json"
            youpin_file = "youpin_full.json"
            
            buff_exists = os.path.exists(os.path.join(self.data_dir, buff_file))
            youpin_exists = os.path.exists(os.path.join(self.data_dir, youpin_file))
            
            # 如果新文件存在，直接使用
            if buff_exists and youpin_exists:
                logger.info(f"📂 找到新版全量数据文件: {buff_file}, {youpin_file}")
                return {'buff_file': buff_file, 'youpin_file': youpin_file}
            
            # 如果新文件不存在，查找旧的时间戳文件作为兼容
            buff_files = []
            youpin_files = []
            
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
                logger.info(f"📂 找到旧版数据文件: Buff={result['buff_file']}, 悠悠有品={result['youpin_file']}")
                logger.info(f"💡 建议运行全量更新以生成新版固定文件名")
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
    
    def _deduplicate_diff_items(self, diff_items: List[PriceDiffItem]) -> List[PriceDiffItem]:
        """对价差商品列表进行去重处理"""
        if not diff_items:
            return diff_items
        
        def generate_item_key(item):
            """生成商品的唯一关键字"""
            # 优先使用skin_item的ID，其次使用hash_name
            if hasattr(item, 'skin_item') and item.skin_item and hasattr(item.skin_item, 'id') and item.skin_item.id:
                return f"id_{item.skin_item.id}"
            elif hasattr(item, 'skin_item') and item.skin_item and hasattr(item.skin_item, 'hash_name') and item.skin_item.hash_name:
                return f"hash_{item.skin_item.hash_name}"
            elif hasattr(item, 'skin_item') and item.skin_item and hasattr(item.skin_item, 'name') and item.skin_item.name:
                return f"name_{item.skin_item.name}"
            else:
                return f"fallback_{str(item)}"
        
        unique_items = {}
        
        for item in diff_items:
            key = generate_item_key(item)
            
            if key not in unique_items:
                unique_items[key] = item
            else:
                # 发现重复，保留利润率更高的
                existing_item = unique_items[key]
                if item.profit_rate > existing_item.profit_rate:
                    unique_items[key] = item
        
        return list(unique_items.values())
    
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
            'after_price_filter_count': 0,  # 🔥 新增：价格筛选后剩余商品数
            'after_sell_num_filter_count': 0,  # 🔥 新增：在售数量筛选后剩余商品数
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
        
        # 🔥 第一步：价格筛选
        logger.info(f"🔥 开始第一步筛选：价格区间 {Config.BUFF_PRICE_MIN}-{Config.BUFF_PRICE_MAX}元")
        price_filtered_items = []
        
        for item_data in buff_items:
            stats['processed_count'] += 1
            
            # 解析基本信息
            buff_price_str = item_data.get('sell_min_price', '0')
            
            # 处理价格
            try:
                buff_price = float(buff_price_str) if buff_price_str else 0.0
            except (ValueError, TypeError):
                buff_price = 0.0
            
            if not buff_price or buff_price <= 0:
                continue
            
            # 🔥 第一步筛选：价格区间
            if not Config.is_buff_price_in_range(buff_price):
                stats['price_filtered_count'] += 1
                continue
            
            # 通过价格筛选的商品
            price_filtered_items.append(item_data)
        
        stats['after_price_filter_count'] = len(price_filtered_items)
        logger.info(f"   第一步完成：{stats['price_filtered_count']}个商品被价格筛选过滤，剩余{stats['after_price_filter_count']}个")
        
        # 🔥 第二步：在售数量筛选
        logger.info(f"🔥 开始第二步筛选：在售数量 ≥{Config.BUFF_SELL_NUM_MIN}个")
        final_filtered_items = []
        
        for item_data in price_filtered_items:
            sell_num = item_data.get('sell_num', 0)
            
            # 🔥 第二步筛选：在售数量
            if not Config.is_buff_sell_num_valid(sell_num):
                stats['sell_num_filtered_count'] += 1
                continue
            
            # 通过所有筛选的商品
            final_filtered_items.append(item_data)
        
        stats['after_sell_num_filter_count'] = len(final_filtered_items)
        logger.info(f"   第二步完成：{stats['sell_num_filtered_count']}个商品被在售数量筛选过滤，剩余{stats['after_sell_num_filter_count']}个")
        
        # 🔥 使用改进的匹配算法并预建索引
        improved_matcher = ImprovedMatcher()
        youpin_hashes = set(youpin_hash_map.keys())
        
        # 🚀 性能优化：预建规范化映射表，避免重复计算
        logger.info(f"🚀 性能优化：预建规范化映射表...")
        normalized_youpin_map = {}
        for youpin_hash in youpin_hashes:
            normalized = improved_matcher.normalize_hash_name(youpin_hash)
            if normalized not in normalized_youpin_map:
                normalized_youpin_map[normalized] = []
            normalized_youpin_map[normalized].append(youpin_hash)
        
        logger.info(f"✅ 映射表建立完成：{len(normalized_youpin_map)}个规范化键")
        
        # 处理通过筛选的商品
        logger.info(f"🔥 开始匹配阶段：处理{len(final_filtered_items)}个通过筛选的商品")
        match_start_time = time.time()
        processed_in_match = 0
        
        for item_data in final_filtered_items:
            processed_in_match += 1
            
            # 🚀 每处理1000个商品显示一次进度
            if processed_in_match % 1000 == 0:
                elapsed = time.time() - match_start_time
                rate = processed_in_match / elapsed if elapsed > 0 else 0
                logger.info(f"   匹配进度: {processed_in_match}/{len(final_filtered_items)} ({rate:.0f}个/秒)")
            # 解析基本信息
            buff_id = str(item_data.get('id', ''))
            buff_name = item_data.get('name', '')
            buff_price_str = item_data.get('sell_min_price', '0')
            hash_name = item_data.get('market_hash_name', '')
            sell_num = item_data.get('sell_num', 0)
            
            # 处理价格（已经通过筛选，这里只是为了计算）
            try:
                buff_price = float(buff_price_str) if buff_price_str else 0.0
            except (ValueError, TypeError):
                buff_price = 0.0
            
            # 🚀 使用高性能匹配算法（预建索引）
            match_result = improved_matcher.find_best_match_fast(
                hash_name, 
                youpin_hash_map,
                normalized_youpin_map
            )
            
            # 如果没有找到匹配，跳过
            if not match_result:
                continue
            
            youpin_price, matched_by, matched_name = match_result
            stats['found_count'] += 1
            
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
        
        # 🔥 新增：在排序前进行去重
        original_count = len(diff_items)
        diff_items = self._deduplicate_diff_items(diff_items)
        if len(diff_items) < original_count:
            logger.info(f"🔄 去重完成: 移除{original_count - len(diff_items)}个重复商品")
        
        # 按利润率排序
        diff_items.sort(key=lambda x: x.profit_rate, reverse=True)
        
        # 限制输出数量
        final_original_count = len(diff_items)
        if len(diff_items) > Config.MAX_OUTPUT_ITEMS:
            diff_items = diff_items[:Config.MAX_OUTPUT_ITEMS]
            stats['limited_output'] = True
            stats['original_final_count'] = final_original_count
        else:
            stats['limited_output'] = False
        
        # 添加筛选条件信息
        stats['filters_applied'] = {
            'price_diff_range': f"{Config.PRICE_DIFF_MIN}-{Config.PRICE_DIFF_MAX}元",
            'buff_price_range': f"{Config.BUFF_PRICE_MIN}-{Config.BUFF_PRICE_MAX}元",
            'buff_sell_num_min': Config.get_buff_sell_num_min(),
            'max_output_items': Config.MAX_OUTPUT_ITEMS
        }
        
        # 🚀 匹配阶段性能统计
        match_end_time = time.time()
        match_duration = match_end_time - match_start_time
        match_rate = len(final_filtered_items) / match_duration if match_duration > 0 else 0
        
        logger.info(f"✅ 匹配阶段完成：耗时 {match_duration:.2f}秒，处理速度 {match_rate:.0f}个/秒")
        
        # 🔥 添加改进匹配算法的统计信息
        matcher_stats = improved_matcher.get_statistics()
        stats.update({
            'match_duration_seconds': match_duration,
            'match_rate_per_second': match_rate,
            'matcher_exact_matches': matcher_stats['exact_matches'],
            'matcher_normalized_matches': matcher_stats['normalized_matches'],
            'matcher_weapon_matches': matcher_stats['weapon_matches'],
            'matcher_fuzzy_matches': matcher_stats['fuzzy_matches'],
            'matcher_no_matches': matcher_stats['no_matches'],
            'matcher_total_matches': matcher_stats['total_matches'],
            'matcher_match_rate': matcher_stats['match_rate']
        })
        
        logger.info(f"📊 筛选统计:")
        logger.info(f"   处理商品: {stats['processed_count']}个")
        logger.info(f"   🔥 第一步-价格筛选: 过滤{stats['price_filtered_count']}个 → 剩余{stats['after_price_filter_count']}个")
        logger.info(f"   🔥 第二步-在售数量筛选: 过滤{stats['sell_num_filtered_count']}个 → 剩余{stats['after_sell_num_filter_count']}个")
        logger.info(f"   找到匹配: {stats['found_count']}个 (匹配率:{matcher_stats['match_rate']:.1f}%)")
        logger.info(f"   🎯 匹配类型分布:")
        logger.info(f"      精确匹配: {matcher_stats['exact_matches']}个")
        logger.info(f"      规范化匹配: {matcher_stats['normalized_matches']}个")
        logger.info(f"      武器名称匹配: {matcher_stats['weapon_matches']}个")
        logger.info(f"      模糊匹配: {matcher_stats['fuzzy_matches']}个")
        logger.info(f"      未匹配: {matcher_stats['no_matches']}个")
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