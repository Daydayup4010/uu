import asyncio
import json
import time
import random
import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from retrying import retry

from config import Config
from models import SkinItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    """爬虫基类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self._setup_session()
    
    def _setup_session(self):
        """设置请求会话"""
        self.session.headers.update({
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    @retry(stop_max_attempt_number=Config.MAX_RETRIES, wait_fixed=2000)
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """发起HTTP请求（带重试）"""
        try:
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"请求失败 {url}: {e}")
            raise
    
    def _random_delay(self):
        """随机延迟"""
        time.sleep(random.uniform(1, Config.REQUEST_DELAY))

class BuffScraper(BaseScraper):
    """Buff网站爬虫"""
    
    def __init__(self):
        super().__init__()
        self.base_url = Config.BUFF_BASE_URL
    
    def get_popular_items(self, limit: int = 100) -> List[SkinItem]:
        """获取热门饰品列表"""
        items = []
        try:
            # 访问Buff首页获取热门饰品
            url = f"{self.base_url}/market/csgo"
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析饰品信息（使用正确的选择器）
            item_elements = soup.find_all('div', class_='item')[:limit]
            logger.info(f"找到 {len(item_elements)} 个饰品元素")
            
            for element in item_elements:
                try:
                    item = self._parse_item_element(element)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.error(f"解析饰品失败: {e}")
                    continue
                
                self._random_delay()
            
        except Exception as e:
            logger.error(f"获取Buff热门饰品失败: {e}")
        
        return items
    
    def _parse_item_element(self, element) -> Optional[SkinItem]:
        """解析单个饰品元素"""
        try:
            # 尝试多种可能的名称选择器
            name_elem = (element.find('h3', class_='item-name') or 
                        element.find('div', class_='item-name') or
                        element.find('a', class_='item-name') or
                        element.find('h3') or
                        element.find('h2'))
            
            if not name_elem:
                # 如果没有找到标准名称元素，尝试获取链接文本
                link_elem = element.find('a')
                if link_elem:
                    name = link_elem.get('title', '') or link_elem.get_text(strip=True)
                else:
                    return None
            else:
                name = name_elem.get_text(strip=True)
            
            if not name:
                return None
            
            # 尝试多种可能的价格选择器
            price_elem = (element.find('strong', class_='f_Strong') or
                         element.find('span', class_='price') or
                         element.find('div', class_='price') or
                         element.find('strong'))
            
            price = 0.0
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # 提取数字
                import re
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace('¥', '').replace(',', ''))
                if price_match:
                    price = float(price_match.group())
            
            # 提取商品ID
            goods_id = element.get('data-goods-id', '') or element.get('data-id', '')
            if not goods_id:
                # 从链接中提取ID
                link_elem = element.find('a')
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    if 'goods_id=' in href:
                        goods_id = href.split('goods_id=')[1].split('&')[0]
                    elif '/goods/' in href:
                        goods_id = href.split('/goods/')[1].split('?')[0]
            
            # 如果还是没有ID，生成一个基于名称的ID
            if not goods_id:
                goods_id = str(abs(hash(name)) % 1000000)
            
            # 提取图片
            img_elem = element.find('img')
            image_url = ''
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            # 构建购买链接
            buff_url = f"{self.base_url}/market/goods?goods_id={goods_id}" if goods_id else ''
            
            logger.debug(f"解析饰品: {name}, 价格: {price}, ID: {goods_id}")
            
            return SkinItem(
                id=f"buff_{goods_id}",
                name=name,
                buff_price=price,
                buff_url=buff_url,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"解析饰品元素失败: {e}")
            return None
    
    def search_item(self, item_name: str) -> Optional[SkinItem]:
        """搜索特定饰品"""
        try:
            # 构建搜索URL
            search_url = f"{self.base_url}/market/search"
            params = {
                'keyword': item_name,
                'game': 'csgo'
            }
            
            response = self._make_request(search_url, params=params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 获取第一个搜索结果
            item_elements = soup.find_all('div', class_='card-item')
            if item_elements:
                return self._parse_item_element(item_elements[0])
            
        except Exception as e:
            logger.error(f"搜索Buff饰品失败 {item_name}: {e}")
        
        return None

class YoupinScraper(BaseScraper):
    """悠悠有品爬虫"""
    
    def __init__(self):
        super().__init__()
        self.base_url = Config.YOUPIN_BASE_URL
    
    def search_item(self, item_name: str) -> Optional[SkinItem]:
        """搜索特定饰品"""
        try:
            # 悠悠有品搜索API（需要根据实际情况调整）
            search_url = f"{self.base_url}/api/search"
            params = {
                'keyword': item_name,
                'game': 'csgo'
            }
            
            response = self._make_request(search_url, params=params)
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                item_data = data['data'][0]
                return SkinItem(
                    id=f"youpin_{item_data.get('id')}",
                    name=item_data.get('name', ''),
                    youpin_price=float(item_data.get('price', 0)),
                    youpin_url=f"{self.base_url}/item/{item_data.get('id')}",
                    image_url=item_data.get('image', '')
                )
            
        except Exception as e:
            logger.error(f"搜索悠悠有品饰品失败 {item_name}: {e}")
        
        return None
    
    def get_popular_items(self, limit: int = 100) -> List[SkinItem]:
        """获取热门饰品（备用方法）"""
        items = []
        try:
            # 使用Selenium获取动态加载的内容
            driver = self._get_webdriver()
            
            try:
                driver.get(f"{self.base_url}/market")
                
                # 等待页面加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "item-card"))
                )
                
                # 获取饰品元素
                item_elements = driver.find_elements(By.CLASS_NAME, "item-card")[:limit]
                
                for element in item_elements:
                    try:
                        name = element.find_element(By.CLASS_NAME, "item-name").text
                        price_text = element.find_element(By.CLASS_NAME, "item-price").text
                        price = float(price_text.replace('¥', '').replace(',', ''))
                        
                        item_id = element.get_attribute('data-id') or str(hash(name))
                        
                        items.append(SkinItem(
                            id=f"youpin_{item_id}",
                            name=name,
                            youpin_price=price,
                            youpin_url=f"{self.base_url}/item/{item_id}"
                        ))
                        
                    except Exception as e:
                        logger.error(f"解析悠悠有品饰品失败: {e}")
                        continue
                        
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"获取悠悠有品热门饰品失败: {e}")
        
        return items
    
    def _get_webdriver(self):
        """获取Chrome WebDriver"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={random.choice(Config.USER_AGENTS)}')
        
        driver = webdriver.Chrome(options=options)
        return driver

class DataCollector:
    """数据收集器"""
    
    def __init__(self):
        self.buff_scraper = BuffScraper()
        self.youpin_scraper = YoupinScraper()
    
    async def collect_data(self) -> List[SkinItem]:
        """收集所有平台数据"""
        logger.info("开始收集数据...")
        
        # 获取Buff热门饰品
        buff_items = self.buff_scraper.get_popular_items()
        logger.info(f"获取到 {len(buff_items)} 个Buff饰品")
        
        # 为每个Buff饰品查找悠悠有品对应价格
        merged_items = []
        for buff_item in buff_items:
            try:
                # 在悠悠有品搜索相同饰品
                youpin_item = self.youpin_scraper.search_item(buff_item.name)
                
                if youpin_item and youpin_item.youpin_price:
                    # 合并数据
                    merged_item = SkinItem(
                        id=buff_item.id,
                        name=buff_item.name,
                        buff_price=buff_item.buff_price,
                        youpin_price=youpin_item.youpin_price,
                        buff_url=buff_item.buff_url,
                        youpin_url=youpin_item.youpin_url,
                        image_url=buff_item.image_url or youpin_item.image_url
                    )
                    merged_items.append(merged_item)
                
                # 延迟避免过频繁请求
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"处理饰品失败 {buff_item.name}: {e}")
                continue
        
        logger.info(f"成功合并 {len(merged_items)} 个饰品数据")
        return merged_items 