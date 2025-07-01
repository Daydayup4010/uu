#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成真实悠悠有品API的价差分析系统

将工作的悠悠有品API集成到现有的价差分析系统中，
实现真实的Buff vs 悠悠有品价格对比
"""

import asyncio
import aiohttp
import json
import time
import logging
import re
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from difflib import SequenceMatcher

from config import Config
from models import SkinItem
from youpin_working_api import YoupinWorkingAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PriceDiffItem:
    """价差商品数据类"""
    id: str
    name: str
    hash_name: str  # 🔥 新增：英文格式的hash_name字段，用于API搜索
    buff_price: float
    youpin_price: float
    price_diff: float
    profit_rate: float
    buff_url: str
    youpin_url: str
    image_url: str
    category: str
    last_updated: datetime

@dataclass
class PriceComparison:
    """价格对比结果"""
    item_name: str
    buff_price: float
    youpin_price: Optional[float]
    price_diff: Optional[float] = None
    profit_rate: Optional[float] = None
    found_on_youpin: bool = False
    
    def __post_init__(self):
        """计算价差和利润率"""
        if self.buff_price and self.youpin_price:
            self.price_diff = self.youpin_price - self.buff_price
            if self.buff_price > 0:
                self.profit_rate = (self.price_diff / self.buff_price) * 100
            self.found_on_youpin = True

class BuffAPIClient:
    """Buff API客户端"""
    
    # 🔥 类级别的全局延迟控制，与其他Buff客户端共享
    _global_last_request_time = 0
    
    def __init__(self):
        self.base_url = "https://buff.163.com"
        self.session = None
        
        # 从TokenManager加载配置
        self.load_config_from_token_manager()
    
    def load_config_from_token_manager(self):
        """从TokenManager加载配置"""
        try:
            from token_manager import token_manager
            buff_config = token_manager.get_buff_config()
            
            # 加载cookies
            self.cookies = buff_config.get("cookies", {})
            
            # 加载headers
            self.headers = buff_config.get("headers", {})
            
            # 如果没有配置，使用默认值
            if not self.cookies or not any(self.cookies.values()):
                # 使用您提供的默认cookies
                self.cookies = {
                    'nts_mail_user': 'yee_agent@163.com:-1:1',
                    'Device-Id': '5fcPnxqalYXt8B35zpV2',
                    'NTES_P_UTID': 'Tdtu6TCflLMKXekYqy2AOpsqVTwdBCoh|1731294026',
                    'P_INFO': 'yee_agent@163.com|1731294026|1|mail163|00&99|fuj&1731289930&mail163#fuj&350100#10#0#0|&0|mail163|yee_agent@163.com',
                    '_ga': 'GA1.1.121880626.1732613285',
                    'Qs_lvt_382223': '1732613286%2C1732613309',
                    'Qs_pv_382223': '3379432729668202500%2C31851909096517050',
                    '_ga_C6TGHFPQ1H': 'GS1.1.1732613284.1.1.1732613347.0.0.0',
                    '_clck': '1obf3cg%7C2%7Cfr9%7C0%7C1791',
                    'Locale-Supported': 'zh-Hans',
                    'game': 'csgo',
                    'qr_code_verify_ticket': '3dccH2Q53c4430a1740cea216e5b4dbc6837',
                    'remember_me': 'U1091923010|M9qu9j35ByTqk1jO7WSjewiVvXxiNOZM',
                    'session': '1-GKbBKqfDqHKQCflrsuYZ9eJ9uUnI6jqAMQSLjXn-2qae2044457754',
                    'csrf_token': 'ImQ0MWRlOWE1NjA4ZWM0NDcwYTFiYmMzNzhmODViZTA1ZDZhODlkM2Qi.aD6cxQ.6NkPROqtVpVExVMoHDOjYYi0eEM'
                }
            
            if not self.headers or not any(self.headers.values()):
                # 使用默认headers
                self.headers = {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Connection': 'keep-alive',
                    'Referer': 'https://buff.163.com/market/csgo',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
                    'X-Requested-With': 'XMLHttpRequest',
                    'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                }
                
        except Exception as e:
            logger.error(f"加载TokenManager配置失败: {e}")
            # 使用默认配置
            self.cookies = {}
            self.headers = {}
    
    def reload_config(self):
        """重新加载配置"""
        self.load_config_from_token_manager()
        logger.info("Buff API配置已重新加载")
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            cookies=self.cookies,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_goods_list(self, page_num: int = 1, page_size: int = 100) -> Optional[Dict]:
        """获取商品列表"""
        try:
            # 🔥 使用全局延迟控制，与其他Buff客户端共享
            import time
            current_time = time.time()
            time_since_last = current_time - self.__class__._global_last_request_time
            
            # 使用配置文件中的延迟
            min_delay = Config.BUFF_API_DELAY
            if time_since_last < min_delay:
                wait_time = min_delay - time_since_last
                print(f"   ⏳ Buff API延迟 {wait_time:.1f}秒 (全局延迟控制)...")
                await asyncio.sleep(wait_time)
            
            self.__class__._global_last_request_time = time.time()
            
            url = f"{self.base_url}/api/market/goods"
            
            # 生成时间戳
            timestamp = int(time.time() * 1000)
            
            params = {
                'game': 'csgo',
                'page_num': page_num,
                'tab': 'selling',
                '_': timestamp
            }
            
            # 如果指定了page_size且不是默认值，可能需要其他参数
            if page_size != 100:
                params['page_size'] = page_size
            
            print(f"   [URL] 请求URL: {url}")
            print(f"   [INFO] 参数: {params}")
            
            async with self.session.get(url, params=params) as response:
                print(f"   📡 响应状态: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # 检查响应数据结构
                    if 'data' in data:
                        items_count = len(data['data'].get('items', []))
                        total_count = data['data'].get('total_count', 0)
                        print(f"   [SUCCESS] 成功获取 {items_count} 个商品 (总计: {total_count})")
                    else:
                        print(f"   [WARNING] 响应格式异常: {list(data.keys())}")
                    
                    return data
                    
                elif response.status == 429:
                    print(f"   [WARNING] 频率限制 (429) - 可能需要增加 BUFF_API_DELAY")
                    # 频率限制时等待更久
                    await asyncio.sleep(2.0)
                    return None
                elif response.status == 403:
                    print(f"   [WARNING] 访问被拒绝 (403)，可能需要更新认证信息")
                    await asyncio.sleep(1.0)
                    return None
                else:
                    print(f"   [ERROR] 请求失败: {response.status}")
                    # 尝试获取错误信息
                    try:
                        error_text = await response.text()
                        print(f"   错误详情: {error_text[:200]}...")
                    except:
                        pass
                    await asyncio.sleep(1.0)
                    return None
                    
        except Exception as e:
            logger.error(f"获取Buff商品列表失败 (页{page_num}): {e}")
            await asyncio.sleep(1.0)
            return None
    
    def parse_goods_item(self, item_data: dict) -> Optional[SkinItem]:
        """解析Buff商品数据"""
        try:
            goods_id = str(item_data.get('id', ''))
            name = item_data.get('name', '')
            
            # 🔥 新增：提取market_hash_name用于精准匹配
            market_hash_name = item_data.get('market_hash_name', '')
            
            # 提取价格信息
            buff_price = float(item_data.get('sell_min_price', 0))
            if buff_price <= 0:
                buff_price = float(item_data.get('sell_reference_price', 0))
            
            # 🔥 新增：提取在售数量
            sell_num = int(item_data.get('sell_num', 0))
            
            # 提取图片信息
            goods_info = item_data.get('goods_info', {})
            image_url = goods_info.get('icon_url', '')
            
            # 构建购买链接
            buff_url = f"{self.base_url}/goods/{goods_id}"
            
            # 提取类别信息
            category = "未知"
            tags = goods_info.get('info', {}).get('tags', {})
            if 'weapon' in tags:
                category = tags['weapon'].get('localized_name', '未知')
            elif 'type' in tags:
                category = tags['type'].get('localized_name', '未知')
            
            # 🔥 新增：提取在售数量
            sell_num = int(item_data.get('sell_num', 0))
            
            return SkinItem(
                id=f"buff_{goods_id}",
                name=name,
                buff_price=buff_price,
                buff_url=buff_url,
                image_url=image_url,
                category=category,
                hash_name=market_hash_name,  # 🔥 新增：保存hash名称
                sell_num=sell_num,  # 🔥 新增：保存在售数量
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"解析Buff商品数据失败: {e}")
            return None

    async def get_all_goods(self) -> Optional[List[Dict]]:
        """分页获取所有Buff商品 - 优化版本降低失败率"""
        print(f"\n📦 开始获取Buff商品（优化版本）...")
        
        try:
            # 🔥 选择使用优化客户端
            use_optimized = True  # 可通过配置控制
            
            if use_optimized:
                from optimized_api_client import OptimizedBuffClient
                print(f"   [START] 使用优化的API客户端")
                
                async with OptimizedBuffClient() as optimized_client:
                    items = await optimized_client.get_all_goods_safe(max_pages=Config.BUFF_MAX_PAGES)
                    return items
            else:
                # 原有的获取逻辑
                max_retries = 2
                
                for attempt in range(max_retries + 1):
                    try:
                        # 先获取第一页，了解总数
                        first_page = await self.get_goods_list(page_num=1, page_size=Config.BUFF_PAGE_SIZE)
                        if not first_page or 'data' not in first_page:
                            if attempt < max_retries:
                                print(f"[ERROR] 无法获取Buff第一页数据，重试 {attempt + 1}/{max_retries + 1}")
                                await asyncio.sleep(2 * (attempt + 1))
                                continue
                            else:
                                print("[ERROR] 达到最大重试次数，无法获取Buff数据")
                                return []
                        
                        first_data = first_page['data']
                        total_count = first_data.get('total_count', 0)
                        total_pages = first_data.get('total_page', 0)
                        
                        print(f"   [SUCCESS] Buff总商品数: {total_count}")
                        print(f"   [SUCCESS] Buff总页数: {total_pages}")
                        
                        all_items = []
                        first_items = first_data.get('items', [])
                        all_items.extend(first_items)
                        print(f"   [SUCCESS] 第1页获取了 {len(first_items)} 个商品")
                        
                        # 设置合理的最大页数
                        max_pages = min(total_pages, Config.BUFF_MAX_PAGES)
                        print(f"   [RESULT] 计划串行获取前 {max_pages} 页数据（降低失败率）")
                        
                        if max_pages > 1:
                            print(f"   🔄 开始串行获取第2-{max_pages}页...")
                            
                            for page_num in range(2, max_pages + 1):
                                try:
                                    page_data = await self.get_goods_list_with_retry(page_num, page_size=Config.BUFF_PAGE_SIZE)
                                    
                                    if page_data and 'data' in page_data:
                                        items = page_data['data'].get('items', [])
                                        if items:
                                            all_items.extend(items)
                                            if page_num % 10 == 0:
                                                print(f"   [SUCCESS] 第 {page_num} 页获取了 {len(items)} 个商品")
                                    
                                    # 串行请求间延迟
                                    await asyncio.sleep(Config.REQUEST_DELAY)
                                    
                                except Exception as e:
                                    print(f"   [WARNING] 第 {page_num} 页获取异常: {e}")
                                    continue
                        
                        print(f"   [SUCCESS] Buff商品获取完成，总计 {len(all_items)} 个商品")
                        return all_items
                        
                    except Exception as e:
                        if attempt < max_retries:
                            print(f"   [ERROR] 获取Buff商品异常 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                            await asyncio.sleep(3 * (attempt + 1))
                            continue
                        else:
                            print(f"   [ERROR] 获取Buff所有商品最终失败: {e}")
                            return []
                
                return []
            
        except Exception as e:
            print(f"   [ERROR] 获取Buff所有商品异常: {e}")
            return []

    async def get_goods_list_with_retry(self, page_num: int, page_size: int = None, max_retries: int = 2) -> Optional[Dict]:
        """带重试机制的获取商品列表"""
        if page_size is None:
            page_size = Config.BUFF_PAGE_SIZE
            
        for attempt in range(max_retries + 1):
            try:
                result = await self.get_goods_list(page_num=page_num, page_size=page_size)
                if result:
                    return result
                elif attempt < max_retries:
                    print(f"   [WARNING] 第 {page_num} 页获取失败，重试 {attempt + 1}/{max_retries + 1}")
                    await asyncio.sleep(1 * (attempt + 1))  # 递增延迟
                    continue
                else:
                    return None
            except Exception as e:
                if attempt < max_retries:
                    print(f"   [WARNING] 第 {page_num} 页异常，重试 {attempt + 1}/{max_retries + 1}: {e}")
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                else:
                    print(f"   [ERROR] 第 {page_num} 页最终失败: {e}")
                    return None
        return None

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
        
        print(f"\n[INFO] 改进匹配算法统计:")
        print(f"   总处理商品: {stats['total_processed']}")
        print(f"   总匹配数量: {stats['total_matches']}")
        print(f"   匹配成功率: {stats['match_rate']:.1f}%")
        print(f"\n[RESULT] 匹配类型分布:")
        print(f"   精确匹配: {stats['exact_matches']} ({stats['exact_matches']/stats['total_processed']*100:.1f}%)")
        print(f"   规范化匹配: {stats['normalized_matches']} ({stats['normalized_matches']/stats['total_processed']*100:.1f}%)")
        print(f"   武器名称匹配: {stats['weapon_matches']} ({stats['weapon_matches']/stats['total_processed']*100:.1f}%)")
        print(f"   模糊匹配: {stats['fuzzy_matches']} ({stats['fuzzy_matches']/stats['total_processed']*100:.1f}%)")
        print(f"   未匹配: {stats['no_matches']} ({stats['no_matches']/stats['total_processed']*100:.1f}%)")

class IntegratedPriceAnalyzer:
    """集成价格分析器"""
    
    def __init__(self, price_diff_threshold: float = None):
        """初始化分析器"""
        # 使用Config中的价格差异阈值，保持向后兼容
        self.price_diff_threshold = price_diff_threshold or Config.PRICE_DIFF_THRESHOLD
        self.buff_client = BuffAPIClient()
        self.youpin_client = YoupinWorkingAPI()
    
    async def __aenter__(self):
        self.buff_client = BuffAPIClient()
        self.youpin_client = YoupinWorkingAPI()
        
        await self.buff_client.__aenter__()
        await self.youpin_client.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.buff_client:
            await self.buff_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.youpin_client:
            await self.youpin_client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _deduplicate_diff_items(self, diff_items: List[PriceDiffItem]) -> List[PriceDiffItem]:
        """对价差商品列表进行去重处理"""
        if not diff_items:
            return diff_items
        
        def generate_item_key(item):
            """生成商品的唯一关键字"""
            if item.id:
                return f"id_{item.id}"
            elif hasattr(item, 'hash_name') and item.hash_name:
                return f"hash_{item.hash_name}"
            else:
                return f"name_{item.name}"
        
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
    
    async def analyze_price_differences(self, max_output_items: int = None) -> List[PriceDiffItem]:
        """
        分析价差商品 - 正确的工作流程：
        1. 获取所有商品数据（不限制数量）
        2. 对所有商品进行价格匹配
        3. 根据价格差异区间筛选
        4. 限制最终输出数量
        """
        # 使用配置文件中的默认值
        if max_output_items is None:
            max_output_items = Config.MAX_OUTPUT_ITEMS
            
        print(f"\n[RESULT] 开始分析价差商品 - 区间筛选模式")
        print(f"[INFO] 价格差异区间: {Config.PRICE_DIFF_MIN}元 - {Config.PRICE_DIFF_MAX}元")
        print(f"[DATA] 最大输出数量: {max_output_items}个")
        print("="*80)
        
        diff_items = []
        processed_count = 0
        found_count = 0
        profitable_count = 0
        
        # [START] 并行获取两个平台的数据
        print(f"\n[START] 并行获取两个平台的数据...")
        start_time = time.time()
        
        # 🔥 使用优化客户端降低失败率
        print(f"   🛡️ 使用优化API客户端降低失败率")
        
        # 创建优化客户端任务
        buff_task = asyncio.create_task(self._get_buff_data_optimized())
        youpin_task = asyncio.create_task(self._get_youpin_data_optimized())
        
        # 等待两个任务完成
        buff_data, youpin_items = await asyncio.gather(buff_task, youpin_task, return_exceptions=True)
        
        # 检查结果
        if isinstance(buff_data, Exception):
            print(f"[ERROR] Buff数据获取失败: {buff_data}")
            buff_data = []
        elif not buff_data:
            print("[ERROR] 无法获取Buff商品数据")
            return []
        
        if isinstance(youpin_items, Exception):
            print(f"[ERROR] 悠悠有品数据获取失败: {youpin_items}")
            youpin_items = []
        elif not youpin_items:
            print("[ERROR] 无法获取悠悠有品商品数据")
            youpin_items = []
        
        # 🔥 移除回退逻辑，避免重复获取
        # 如果优化客户端失败，直接返回空结果而不是启动第二套获取逻辑
        if not buff_data and not youpin_items:
            print("[ERROR] 两个平台都无法获取数据，分析终止")
            return []
        
        parallel_time = time.time() - start_time
        print(f"⚡ 并行获取完成，耗时: {parallel_time:.2f} 秒")
        
        # 显示获取结果
        items = buff_data
        total_items = len(items)
        youpin_count = len(youpin_items) if youpin_items else 0
        print(f"[SUCCESS] 成功获取 {total_items} 个Buff商品")
        print(f"[SUCCESS] 成功获取 {youpin_count} 个悠悠有品商品")
        
        # 🔥 新增：保存完整数据为 full data 文件
        await self._save_full_data(buff_data, youpin_items)
        
        # 🔥 修正：处理所有商品，不限制数量
        items_to_process = items  # 处理所有商品
        print(f"🔄 将处理所有 {len(items_to_process)} 个商品进行价格匹配...")
        
        # 🔥 新的精准匹配逻辑：创建commodityHashName到价格的映射
        youpin_hash_map = {}  # hash名称 -> 价格
        youpin_name_map = {}
        
        if youpin_items:
            print(f"[INFO] 悠悠有品商品数据样本:")
            for i, item in enumerate(youpin_items[:3]):  # 显示前3个商品的数据结构
                print(f"   #{i+1}: {item}")
            
            for item in youpin_items:
                # 提取hash名称和价格
                hash_name = item.get('commodityHashName', '')
                commodity_name = item.get('commodityName', '')
                price = item.get('price', 0)
                
                if hash_name and price:
                    try:
                        price_float = float(price)
                        youpin_hash_map[hash_name] = price_float
                    except (ValueError, TypeError):
                        continue
                
                # 同时建立商品名称映射作为备用
                if commodity_name and price:
                    try:
                        price_float = float(price)
                        youpin_name_map[commodity_name] = price_float
                    except (ValueError, TypeError):
                        continue
        
        print(f"📈 建立映射表:")
        print(f"   Hash映射数量: {len(youpin_hash_map)}")
        print(f"   名称映射数量: {len(youpin_name_map)}")
        
        # 🔥 显示Hash映射样本
        if len(youpin_hash_map) > 0:
            print(f"\n[DEBUG] 悠悠有品Hash样本:")
            for i, hash_name in enumerate(list(youpin_hash_map.keys())[:5]):
                print(f"   #{i+1}: {hash_name}")
        
        print(f"\n🔄 开始处理 {len(items_to_process)} 个商品...")
        
        # 🔥 使用改进的匹配算法
        improved_matcher = ImprovedMatcher()
        youpin_hashes = set(youpin_hash_map.keys())
        
        # 处理每个商品
        for i, item_data in enumerate(items_to_process, 1):
            processed_count += 1
            
            # 解析Buff商品
            buff_item = self.buff_client.parse_goods_item(item_data)
            if not buff_item:
                continue
            
            # 🔥 检查Buff价格是否在筛选范围内
            if not Config.is_buff_price_in_range(buff_item.buff_price):
                continue
            
            # 🔥 新增：检查Buff在售数量是否符合条件
            if hasattr(buff_item, 'sell_num') and buff_item.sell_num is not None:
                if not Config.is_buff_sell_num_valid(buff_item.sell_num):
                    continue
            
            # 🔥 使用改进匹配算法找到最佳匹配
            match_result = improved_matcher.find_best_match(
                buff_item.hash_name, 
                youpin_hashes, 
                youpin_hash_map
            )
            
            # 如果没有找到匹配，跳过
            if not match_result:
                continue
            
            youpin_price, matched_by, matched_name = match_result
            found_count += 1
            
            # 计算价差
            if youpin_price and buff_item.buff_price:
                price_diff = youpin_price - buff_item.buff_price
                if buff_item.buff_price > 0:
                    profit_rate = (price_diff / buff_item.buff_price) * 100
                else:
                    profit_rate = 0
                
                # 🔥 使用区间筛选逻辑
                if Config.is_price_diff_in_range(price_diff):
                    profitable_count += 1
                    
                    # 🔥 修复：提取hash_name，优先使用market_hash_name
                    hash_name = getattr(buff_item, 'market_hash_name', None) or getattr(buff_item, 'hash_name', None) or buff_item.name
                    
                    # 创建价差商品
                    diff_item = PriceDiffItem(
                        id=buff_item.id,
                        name=buff_item.name,
                        hash_name=hash_name,  # 🔥 新增hash_name字段
                        buff_price=buff_item.buff_price,
                        youpin_price=youpin_price,
                        price_diff=price_diff,
                        profit_rate=profit_rate,
                        buff_url=buff_item.buff_url,
                        youpin_url=f"https://www.youpin898.com/search?keyword={buff_item.name}",
                        image_url=buff_item.image_url,
                        category=buff_item.category,
                        last_updated=datetime.now()
                    )
                    
                    diff_items.append(diff_item)
                    
                    # 只在找到符合条件的商品时打印详细信息
                    print(f"   📦 #{len(diff_items)}: {buff_item.name}")
                    print(f"      💰 价差: ¥{price_diff:.2f} ({profit_rate:.1f}%) - {matched_by}")
                    print(f"      [RESULT] 符合区间要求！")
            
            # 显示进度（每处理1000个商品显示一次）
            if processed_count % 1000 == 0:
                print(f"\n[INFO] 进度统计 ({processed_count}/{len(items_to_process)}):")
                print(f"   已处理: {processed_count} 个商品")
                print(f"   找到匹配: {found_count} 个商品")
                print(f"   符合区间: {len(diff_items)} 个商品")
        
        total_time = time.time() - start_time
        print(f"\n[SUCCESS] 价差分析完成！总耗时: {total_time:.2f} 秒")
        print(f"[INFO] 最终统计:")
        print(f"   总处理: {processed_count} 个商品")
        print(f"   悠悠有品覆盖率: {(found_count/processed_count)*100:.1f}%")
        print(f"   符合价差区间: {len(diff_items)} 个商品")
        
        # 🔥 显示改进匹配算法的详细统计
        improved_matcher.print_statistics()
        
        # 🔥 新增：在返回前进行去重检查
        original_count = len(diff_items)
        diff_items = self._deduplicate_diff_items(diff_items)
        if len(diff_items) < original_count:
            print(f"🔄 去重完成: 移除{original_count - len(diff_items)}个重复商品")
        
        # 按利润率排序
        diff_items.sort(key=lambda x: x.profit_rate, reverse=True)
        
        # 🔥 限制输出数量
        if len(diff_items) > max_output_items:
            print(f"🔄 输出商品数量限制为 {max_output_items} 个（按利润率排序）")
            diff_items = diff_items[:max_output_items]
        
        return diff_items
    
    async def _get_buff_data_optimized(self) -> List[Dict]:
        """使用优化客户端获取Buff数据"""
        from optimized_api_client import OptimizedBuffClient
        
        async with OptimizedBuffClient() as optimized_client:
            return await optimized_client.get_all_goods_safe(max_pages=Config.BUFF_MAX_PAGES)
    
    async def _get_youpin_data_optimized(self) -> List[Dict]:
        """使用优化客户端获取悠悠有品数据"""
        from optimized_api_client import OptimizedYoupinClient
        
        async with OptimizedYoupinClient() as optimized_client:
            return await optimized_client.get_all_items_safe(max_pages=Config.YOUPIN_MAX_PAGES)
    
    async def _save_full_data(self, buff_data: List[Dict], youpin_data: List[Dict]):
        """保存完整数据为 full data 文件（直接覆盖，不使用时间戳）"""
        try:
            import json
            import os
            from datetime import datetime
            
            # 确保数据目录存在
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # 保存 Buff 完整数据 - 直接覆盖，不用时间戳
            if buff_data:
                buff_filename = os.path.join(data_dir, "buff_full.json")
                
                # 计算实际页数
                actual_pages = len(buff_data) // Config.BUFF_PAGE_SIZE
                if len(buff_data) % Config.BUFF_PAGE_SIZE > 0:
                    actual_pages += 1
                
                buff_file_data = {
                    'metadata': {
                        'platform': 'buff',
                        'total_count': len(buff_data),
                        'max_pages': Config.BUFF_MAX_PAGES,
                        'actual_pages': actual_pages,
                        'generated_at': datetime.now().isoformat(),
                        'api_config': {
                            'delay': Config.BUFF_API_DELAY,
                            'page_size': Config.BUFF_PAGE_SIZE
                        },
                        'collection_type': 'full_integrated_system'
                    },
                    'items': buff_data
                }
                
                with open(buff_filename, 'w', encoding='utf-8') as f:
                    json.dump(buff_file_data, f, ensure_ascii=False, indent=2)
                
                file_size = os.path.getsize(buff_filename) / 1024 / 1024  # MB
                print(f"💾 Buff完整数据已保存: {len(buff_data)}个商品 -> {buff_filename} ({file_size:.1f} MB)")
            
            # 保存悠悠有品完整数据 - 直接覆盖，不用时间戳
            if youpin_data:
                youpin_filename = os.path.join(data_dir, "youpin_full.json")
                
                # 转换为可序列化的格式
                items_data = []
                for item in youpin_data:
                    if isinstance(item, dict):
                        items_data.append(item)
                    else:
                        items_data.append(item.__dict__ if hasattr(item, '__dict__') else str(item))
                
                # 计算实际页数
                actual_pages = len(items_data) // Config.YOUPIN_PAGE_SIZE
                if len(items_data) % Config.YOUPIN_PAGE_SIZE > 0:
                    actual_pages += 1
                
                youpin_file_data = {
                    'metadata': {
                        'platform': 'youpin',
                        'total_count': len(items_data),
                        'max_pages': Config.YOUPIN_MAX_PAGES,
                        'actual_pages': actual_pages,
                        'generated_at': datetime.now().isoformat(),
                        'api_config': {
                            'delay': Config.YOUPIN_API_DELAY,
                            'page_size': Config.YOUPIN_PAGE_SIZE
                        },
                        'collection_type': 'full_integrated_system'
                    },
                    'items': items_data
                }
                
                with open(youpin_filename, 'w', encoding='utf-8') as f:
                    json.dump(youpin_file_data, f, ensure_ascii=False, indent=2)
                
                file_size = os.path.getsize(youpin_filename) / 1024 / 1024  # MB
                print(f"💾 悠悠有品完整数据已保存: {len(items_data)}个商品 -> {youpin_filename} ({file_size:.1f} MB)")
                
            print(f"[SUCCESS] 完整数据保存完成！")
            
        except Exception as e:
            print(f"[ERROR] 保存完整数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 🔥 以下模糊匹配方法已禁用 - 只使用Hash精确匹配
    # def _fuzzy_match_price_with_name(self, buff_name: str, youpin_price_map: dict) -> Optional[tuple]:
    #     """模糊匹配悠悠有品价格，返回(价格, 商品名称) - 已禁用"""
    #     # 模糊匹配代码已移除，只保留精确匹配
    #     return None
    
    # def _is_weapon_alias_match(self, weapon1: str, weapon2: str) -> bool:
    #     """检查武器别名匹配 - 已禁用"""
    #     return False
    
    # def _extract_weapon_name(self, name: str) -> str:
    #     """提取武器名称 - 已禁用"""
    #     return ""
    
    # def _fuzzy_match_price(self, buff_name: str, youpin_price_map: dict) -> Optional[float]:
    #     """模糊匹配悠悠有品价格（保持向后兼容）- 已禁用"""
    #     return None
    
    # def _extract_keywords(self, name: str) -> str:
    #     """提取商品名称关键词 - 已禁用"""
    #     return ""

    async def quick_analysis(self, count: int = 10) -> List[PriceDiffItem]:
        """快速分析（少量商品测试）"""
        return await self.analyze_price_differences(max_output_items=count)

# 数据保存和加载功能
def save_price_diff_data(diff_items: List[PriceDiffItem], filename: str = None):
    """保存价差数据到JSON文件"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/price_diff_analysis_{timestamp}.json"
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'total_count': len(diff_items),
        'items': [asdict(item) for item in diff_items]
    }
    
    # 处理datetime序列化
    for item in data['items']:
        if isinstance(item['last_updated'], datetime):
            item['last_updated'] = item['last_updated'].isoformat()
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"价差数据已保存到: {filename}")
    return filename

def load_price_diff_data(filename: str) -> List[PriceDiffItem]:
    """从JSON文件加载价差数据"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        diff_items = []
        for item_data in data['items']:
            # 转换datetime
            if 'last_updated' in item_data:
                item_data['last_updated'] = datetime.fromisoformat(item_data['last_updated'])
            
            # 🔥 兼容处理：如果没有hash_name字段，使用name
            if 'hash_name' not in item_data:
                item_data['hash_name'] = item_data.get('name', '')
            
            diff_items.append(PriceDiffItem(**item_data))
        
        logger.info(f"从 {filename} 加载了 {len(diff_items)} 个价差商品")
        return diff_items
        
    except Exception as e:
        logger.error(f"加载价差数据失败: {e}")
        return []

# 测试和演示功能
async def test_integrated_system():
    """测试集成系统"""
    print("[RESULT] 测试集成价差分析系统")
    print("="*80)
    
    async with IntegratedPriceAnalyzer(price_diff_threshold=5.0) as analyzer:
        # 快速测试
        print("\n1️⃣ 快速测试（5个商品）")
        diff_items = await analyzer.analyze_price_differences(max_output_items=5)
        
        if diff_items:
            print(f"\n[RESULT] 发现 {len(diff_items)} 个有价差的商品:")
            for i, item in enumerate(diff_items[:3], 1):
                print(f"   #{i}: {item.name}")
                print(f"       Buff: ¥{item.buff_price} → 悠悠有品: ¥{item.youpin_price}")
                print(f"       价差: ¥{item.price_diff:.2f} ({item.profit_rate:.1f}%)")
            
            # 保存数据
            filename = save_price_diff_data(diff_items)
            print(f"\n💾 数据已保存到: {filename}")
        else:
            print("[ERROR] 未发现有价差的商品")

async def run_full_analysis():
    """运行完整价差分析"""
    print("[RESULT] 完整价差分析系统")
    print("="*80)
    
    async with IntegratedPriceAnalyzer(price_diff_threshold=10.0) as analyzer:
        # 分析50个商品
        diff_items = await analyzer.analyze_price_differences(max_output_items=50)
        
        if diff_items:
            # 保存数据
            filename = save_price_diff_data(diff_items)
            
            # 显示结果
            print(f"\n[RESULT] 发现 {len(diff_items)} 个有价差的商品:")
            print("="*80)
            
            for i, item in enumerate(diff_items[:10], 1):
                print(f"#{i}: {item.name}")
                print(f"    Buff: ¥{item.buff_price} | 悠悠有品: ¥{item.youpin_price}")
                print(f"    价差: ¥{item.price_diff:.2f} | 利润率: {item.profit_rate:.1f}%")
                print(f"    Buff链接: {item.buff_url}")
                print("-" * 40)
        else:
            print("[ERROR] 未发现有价差的商品")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "full":
        asyncio.run(run_full_analysis())
    else:
        asyncio.run(test_integrated_system()) 
