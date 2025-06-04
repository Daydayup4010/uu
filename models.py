from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class SkinItem(BaseModel):
    """饰品数据模型"""
    id: str
    name: str
    wear_level: Optional[str] = None  # 磨损等级
    wear_value: Optional[float] = None  # 磨损值
    buff_price: Optional[float] = None
    youpin_price: Optional[float] = None
    buff_url: Optional[str] = None
    youpin_url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    hash_name: Optional[str] = None  # 对应Buff的market_hash_name和悠悠有品的commodityHashName
    last_updated: Optional[datetime] = None

class PriceDiffItem(BaseModel):
    """价差饰品模型"""
    skin_item: SkinItem
    price_diff: float
    profit_margin: float  # 利润率
    buff_buy_url: str
    
    @property
    def id(self) -> str:
        return self.skin_item.id
    
    @property 
    def name(self) -> str:
        return self.skin_item.name
    
    @property
    def buff_price(self) -> float:
        return self.skin_item.buff_price or 0.0
    
    @property
    def youpin_price(self) -> float:
        return self.skin_item.youpin_price or 0.0
    
    @property
    def buff_url(self) -> str:
        return self.skin_item.buff_url or ""
    
    @property
    def youpin_url(self) -> str:
        return self.skin_item.youpin_url or ""
    
    @property
    def image_url(self) -> str:
        return self.skin_item.image_url or ""
    
    @property
    def category(self) -> str:
        return self.skin_item.category or ""
    
    @property
    def last_updated(self) -> Optional[datetime]:
        return self.skin_item.last_updated

class MonitorConfig(BaseModel):
    """监控配置模型"""
    threshold: float = 20.0
    enabled_categories: List[str] = ["步枪", "狙击枪", "手枪", "冲锋枪", "霰弹枪", "机枪", "刀具", "手套"]
    min_price: float = 10.0  # 最低价格过滤
    max_price: float = 10000.0  # 最高价格过滤

class ApiResponse(BaseModel):
    """API响应模型"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None 