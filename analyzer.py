import json
import os
import logging
from datetime import datetime
from typing import List, Dict
from models import SkinItem, PriceDiffItem, MonitorConfig
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceDiffAnalyzer:
    """价差分析器"""
    
    def __init__(self):
        self.config = MonitorConfig()
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(Config.DATA_DIR):
            os.makedirs(Config.DATA_DIR)
    
    def analyze_price_diff(self, items: List[SkinItem]) -> List[PriceDiffItem]:
        """分析价差并筛选符合条件的饰品"""
        logger.info(f"开始分析 {len(items)} 个饰品的价差...")
        
        diff_items = []
        
        for item in items:
            try:
                # 检查是否有有效价格数据
                if not item.buff_price or not item.youpin_price:
                    continue
                
                # 价格过滤
                if item.buff_price < self.config.min_price or item.buff_price > self.config.max_price:
                    continue
                
                # 计算价差
                price_diff = item.youpin_price - item.buff_price
                
                # 计算利润率
                profit_margin = (price_diff / item.buff_price) * 100 if item.buff_price > 0 else 0
                
                # 检查是否满足阈值条件
                if price_diff >= self.config.threshold:
                    # 生成购买链接
                    buff_buy_url = self._generate_buy_url(item)
                    
                    diff_item = PriceDiffItem(
                        skin_item=item,
                        price_diff=price_diff,
                        profit_margin=profit_margin,
                        buff_buy_url=buff_buy_url
                    )
                    
                    diff_items.append(diff_item)
                    
            except Exception as e:
                logger.error(f"分析饰品价差失败 {item.name}: {e}")
                continue
        
        # 按价差排序
        diff_items.sort(key=lambda x: x.price_diff, reverse=True)
        
        logger.info(f"找到 {len(diff_items)} 个符合条件的差价饰品")
        
        # 保存结果
        self._save_diff_data(diff_items)
        
        return diff_items
    
    def _generate_buy_url(self, item: SkinItem) -> str:
        """生成购买链接"""
        if item.buff_url:
            return item.buff_url
        
        # 如果没有直接链接，尝试从ID构建
        if item.id.startswith('buff_'):
            goods_id = item.id.replace('buff_', '')
            return f"{Config.BUFF_BASE_URL}/market/goods?goods_id={goods_id}"
        
        # 备用：搜索链接
        return f"{Config.BUFF_BASE_URL}/market/search?keyword={item.name}"
    
    def _save_diff_data(self, diff_items: List[PriceDiffItem]):
        """保存差价数据到文件"""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'threshold': self.config.threshold,
                'total_count': len(diff_items),
                'items': [
                    {
                        'id': item.skin_item.id,
                        'name': item.skin_item.name,
                        'buff_price': item.skin_item.buff_price,
                        'youpin_price': item.skin_item.youpin_price,
                        'price_diff': item.price_diff,
                        'profit_margin': item.profit_margin,
                        'buff_buy_url': item.buff_buy_url,
                        'image_url': item.skin_item.image_url,
                        'category': item.skin_item.category
                    }
                    for item in diff_items
                ]
            }
            
            with open(Config.DIFF_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"差价数据已保存到 {Config.DIFF_DATA_FILE}")
            
        except Exception as e:
            logger.error(f"保存差价数据失败: {e}")
    
    def load_diff_data(self) -> List[PriceDiffItem]:
        """从文件加载差价数据"""
        try:
            if not os.path.exists(Config.DIFF_DATA_FILE):
                return []
            
            with open(Config.DIFF_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            diff_items = []
            for item_data in data.get('items', []):
                # 重构SkinItem
                skin_item = SkinItem(
                    id=item_data['id'],
                    name=item_data['name'],
                    buff_price=item_data['buff_price'],
                    youpin_price=item_data['youpin_price'],
                    image_url=item_data.get('image_url'),
                    category=item_data.get('category')
                )
                
                # 重构PriceDiffItem
                diff_item = PriceDiffItem(
                    skin_item=skin_item,
                    price_diff=item_data['price_diff'],
                    profit_margin=item_data['profit_margin'],
                    buff_buy_url=item_data['buff_buy_url']
                )
                
                diff_items.append(diff_item)
            
            logger.info(f"从文件加载了 {len(diff_items)} 个差价饰品")
            return diff_items
            
        except Exception as e:
            logger.error(f"加载差价数据失败: {e}")
            return []
    
    def update_config(self, threshold: float = None, min_price: float = None, max_price: float = None):
        """更新配置参数"""
        if threshold is not None:
            self.config.threshold = threshold
            Config.update_threshold(threshold)
            logger.info(f"更新价差阈值为: {threshold}")
        
        if min_price is not None:
            self.config.min_price = min_price
            logger.info(f"更新最低价格过滤为: {min_price}")
        
        if max_price is not None:
            self.config.max_price = max_price
            logger.info(f"更新最高价格过滤为: {max_price}")
    
    def get_statistics(self, diff_items: List[PriceDiffItem]) -> Dict:
        """获取统计信息"""
        if not diff_items:
            return {
                'total_count': 0,
                'avg_price_diff': 0,
                'avg_profit_margin': 0,
                'max_price_diff': 0,
                'max_profit_margin': 0,
                'min_price_diff': 0,
                'min_profit_margin': 0
            }
        
        price_diffs = [item.price_diff for item in diff_items]
        profit_margins = [item.profit_margin for item in diff_items]
        
        return {
            'total_count': len(diff_items),
            'avg_price_diff': sum(price_diffs) / len(price_diffs),
            'avg_profit_margin': sum(profit_margins) / len(profit_margins),
            'max_price_diff': max(price_diffs),
            'max_profit_margin': max(profit_margins),
            'min_price_diff': min(price_diffs),
            'min_profit_margin': min(profit_margins),
            'threshold': self.config.threshold,
            'categories_distribution': self._get_category_distribution(diff_items)
        }
    
    def save_diff_data(self, diff_items: List[PriceDiffItem]):
        """保存差价数据到文件（公有方法）"""
        self._save_diff_data(diff_items)
    
    def _get_category_distribution(self, diff_items: List[PriceDiffItem]) -> Dict[str, int]:
        """获取分类分布"""
        distribution = {}
        for item in diff_items:
            category = item.skin_item.category or '未分类'
            distribution[category] = distribution.get(category, 0) + 1
        return distribution 