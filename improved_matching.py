#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的匹配算法
使用多级匹配策略提高两个平台的商品匹配率
"""

import re
from difflib import SequenceMatcher
from typing import Dict, Set, Tuple, Optional

class ImprovedMatcher:
    """改进的商品匹配器"""
    
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
        # 将全角字符转为半角
        normalized = normalized.replace('（', '(').replace('）', ')')
        normalized = normalized.replace('｜', '|')
        
        # 3. 统一大小写（保持原有大小写，但用于比较时忽略）
        return normalized
    
    def extract_weapon_name(self, hash_name: str) -> str:
        """提取武器名称（去除磨损等级）"""
        if not hash_name:
            return ""
        
        # 移除磨损等级，如 (Factory New), (Field-Tested), (Battle-Scarred) 等
        weapon_name = re.sub(r'\s*\([^)]*\)\s*$', '', hash_name)
        
        # 移除 StatTrak™ 标记进行更广泛的匹配
        weapon_name_no_stattrak = re.sub(r'StatTrak™?\s*', '', weapon_name)
        
        return weapon_name_no_stattrak.strip()
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度"""
        if not str1 or not str2:
            return 0.0
        
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def find_best_match(self, buff_hash: str, youpin_hashes: Set[str], 
                       youpin_price_map: Dict[str, float]) -> Optional[Tuple[float, str, str]]:
        """
        为Buff商品找到最佳匹配的悠悠有品商品
        返回: (price, match_type, matched_hash) 或 None
        """
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
        
        # 3. 武器名称匹配（去除磨损等级）
        weapon_name_buff = self.extract_weapon_name(buff_hash)
        if weapon_name_buff:
            for youpin_hash in youpin_hashes:
                weapon_name_youpin = self.extract_weapon_name(youpin_hash)
                if weapon_name_buff.lower() == weapon_name_youpin.lower() and youpin_hash in youpin_price_map:
                    self.weapon_matches += 1
                    return (youpin_price_map[youpin_hash], "武器名称匹配", youpin_hash)
        
        # 4. 高相似度模糊匹配（90%以上相似度）
        best_match = None
        best_similarity = 0.9  # 最低90%相似度
        
        for youpin_hash in youpin_hashes:
            if youpin_hash in youpin_price_map:
                similarity = self.calculate_similarity(buff_hash, youpin_hash)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = youpin_hash
        
        if best_match:
            self.fuzzy_matches += 1
            return (youpin_price_map[best_match], f"模糊匹配({best_similarity:.1%})", best_match)
        
        # 5. 武器名称模糊匹配（85%以上相似度）
        weapon_name_buff = self.extract_weapon_name(buff_hash)
        if weapon_name_buff and len(weapon_name_buff) > 5:  # 只对较长的武器名称进行模糊匹配
            best_weapon_match = None
            best_weapon_similarity = 0.85
            
            for youpin_hash in youpin_hashes:
                if youpin_hash in youpin_price_map:
                    weapon_name_youpin = self.extract_weapon_name(youpin_hash)
                    if weapon_name_youpin and len(weapon_name_youpin) > 5:
                        similarity = self.calculate_similarity(weapon_name_buff, weapon_name_youpin)
                        if similarity > best_weapon_similarity:
                            best_weapon_similarity = similarity
                            best_weapon_match = youpin_hash
            
            if best_weapon_match:
                self.fuzzy_matches += 1
                return (youpin_price_map[best_weapon_match], f"武器模糊匹配({best_weapon_similarity:.1%})", best_weapon_match)
        
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
    
    def print_statistics(self):
        """打印匹配统计信息"""
        stats = self.get_statistics()
        
        print(f"\n📊 改进匹配算法统计:")
        print(f"   总处理商品: {stats['total_processed']}")
        print(f"   总匹配数量: {stats['total_matches']}")
        print(f"   匹配成功率: {stats['match_rate']:.1f}%")
        print(f"\n🎯 匹配类型分布:")
        print(f"   精确匹配: {stats['exact_matches']} ({stats['exact_matches']/stats['total_processed']*100:.1f}%)")
        print(f"   规范化匹配: {stats['normalized_matches']} ({stats['normalized_matches']/stats['total_processed']*100:.1f}%)")
        print(f"   武器名称匹配: {stats['weapon_matches']} ({stats['weapon_matches']/stats['total_processed']*100:.1f}%)")
        print(f"   模糊匹配: {stats['fuzzy_matches']} ({stats['fuzzy_matches']/stats['total_processed']*100:.1f}%)")
        print(f"   未匹配: {stats['no_matches']} ({stats['no_matches']/stats['total_processed']*100:.1f}%)")

# 测试函数
def test_improved_matching():
    """测试改进的匹配算法"""
    matcher = ImprovedMatcher()
    
    # 测试数据
    buff_hashes = [
        "AK-47 | Redline (Field-Tested)",
        "AWP | Dragon Lore (Factory New)",
        "M4A4 | Howl (Minimal Wear)",
        "StatTrak™ Glock-18 | Water Elemental (Factory New)",
        "Karambit | Fade (Factory New)"
    ]
    
    youpin_hashes = {
        "AK-47 | Redline (Field-Tested)",  # 精确匹配
        "AWP | Dragon Lore (Factory New)",  # 精确匹配
        "M4A4 | Howl (Minimal Wear)",      # 精确匹配
        "Glock-18 | Water Elemental (Factory New)",  # 武器名称匹配（无StatTrak）
        "Karambit | Fade (Factory New)"    # 精确匹配
    }
    
    youpin_price_map = {hash_name: 100.0 for hash_name in youpin_hashes}
    
    print("🧪 测试改进匹配算法:")
    print("=" * 50)
    
    for buff_hash in buff_hashes:
        result = matcher.find_best_match(buff_hash, youpin_hashes, youpin_price_map)
        if result:
            price, match_type, matched_hash = result
            print(f"✅ {buff_hash}")
            print(f"   -> {matched_hash} ({match_type})")
        else:
            print(f"❌ {buff_hash} (无匹配)")
    
    matcher.print_statistics()

if __name__ == "__main__":
    test_improved_matching() 