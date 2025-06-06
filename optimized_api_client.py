#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的API客户端 - 降低接口失败率
"""

import asyncio
import aiohttp
import time
import random
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIRequestConfig:
    """API请求配置"""
    max_retries: int = 5              # 最大重试次数
    base_delay: float = 1.0           # 基础延迟
    max_delay: float = 10.0           # 最大延迟
    timeout: float = 30.0             # 请求超时
    concurrent_limit: int = 1         # 并发限制（降低到1）
    rate_limit_delay: float = None    # Buff API速率限制延迟（从配置文件读取）
    
    def __post_init__(self):
        """初始化后处理，从配置文件读取延迟设置"""
        if self.rate_limit_delay is None:
            try:
                from config import Config
                self.rate_limit_delay = Config.BUFF_API_DELAY
            except:
                self.rate_limit_delay = 1.0  # 默认值

class OptimizedBuffClient:
    """优化的Buff API客户端"""
    
    # 🔥 类级别的全局请求时间控制，确保所有实例共享延迟
    _global_last_request_time = 0
    _global_request_count = 0
    _global_lock = None  # 异步锁，延迟初始化避免事件循环问题
    
    def __init__(self):
        self.base_url = "https://buff.163.com"
        self.session = None
        self.config = APIRequestConfig()
        self.request_count = 0
        self.last_request_time = 0  # 保留实例级别的用于兼容
        self._cancelled = False  # 🔥 添加取消标志
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            from token_manager import token_manager
            buff_config = token_manager.get_buff_config()
            self.cookies = buff_config.get("cookies", {})
            self.headers = buff_config.get("headers", {})
        except Exception as e:
            logger.error(f"加载Buff配置失败: {e}")
            self.cookies = {}
            self.headers = {}
    
    def cancel(self):
        """取消当前客户端的所有操作"""
        self._cancelled = True
        logger.info("🛑 Buff API客户端已取消")
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._cancelled
    
    async def __aenter__(self):
        # 更保守的连接配置
        connector = aiohttp.TCPConnector(
            limit=2,                    # 降低连接池大小
            limit_per_host=1,          # 每个主机只允许1个连接
            ttl_dns_cache=300,         # DNS缓存
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout,
            connect=10,
            sock_read=15
        )
        
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            cookies=self.cookies,
            connector=connector,
            timeout=timeout,
            trust_env=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            # 给连接池时间清理
            await asyncio.sleep(self.config.rate_limit_delay)
    
    async def rate_limited_request(self, url: str, params: dict) -> Optional[Dict]:
        """带速率限制的请求 - 使用全局延迟控制"""
        # 🔥 检查是否已取消
        if self._cancelled:
            logger.info("🛑 请求已取消")
            return None
        
        # 🔥 修复：使用简单的时间戳控制，避免事件循环绑定问题
        import time
        current_time = time.time()
        time_since_last = current_time - self._global_last_request_time
        
        if time_since_last < self.config.rate_limit_delay:
            wait_time = self.config.rate_limit_delay - time_since_last
            logger.info(f"🔄 Buff API延迟等待: {wait_time:.2f}秒 (配置: {self.config.rate_limit_delay}秒)")
            await asyncio.sleep(wait_time)
        
        # 更新全局请求时间
        self._global_last_request_time = time.time()
        self._global_request_count += 1
        
        # 每10个请求后增加额外延迟
        if self._global_request_count % 10 == 0:
            extra_delay = random.uniform(3, 6)
            logger.info(f"第{self._global_request_count}个请求，额外延迟{extra_delay:.1f}秒")
            await asyncio.sleep(extra_delay)
        
        # 实际请求在锁外执行，避免阻塞其他操作
        return await self.request_with_retry(url, params)
    
    async def request_with_retry(self, url: str, params: dict) -> Optional[Dict]:
        """带重试机制的请求"""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                # 指数退避延迟
                if attempt > 0:
                    delay = min(
                        self.config.base_delay * (2 ** attempt) + random.uniform(0, 1),
                        self.config.max_delay
                    )
                    logger.info(f"重试{attempt}/{self.config.max_retries}，延迟{delay:.1f}秒")
                    await asyncio.sleep(delay)
                
                async with self.session.get(url, params=params) as response:
                    logger.info(f"请求状态: {response.status}, URL: {url}")
                    
                    if response.status == 200:
                        data = await response.json()
                        if 'data' in data:
                            items_count = len(data['data'].get('items', []))
                            logger.info(f"✅ 成功获取 {items_count} 个商品")
                            return data
                        else:
                            logger.warning(f"响应格式异常: {list(data.keys())}")
                            if attempt == self.config.max_retries - 1:
                                return data  # 最后一次尝试返回原始数据
                    
                    elif response.status == 429:
                        # 速率限制，等待更长时间
                        logger.warning("遇到速率限制 (429)")
                        await asyncio.sleep(self.config.max_delay)
                        continue
                    
                    elif response.status == 403:
                        # 认证问题
                        logger.error("认证失败 (403)，可能需要更新token")
                        text = await response.text()
                        logger.error(f"响应内容: {text[:200]}")
                        if attempt == self.config.max_retries - 1:
                            return None
                    
                    else:
                        text = await response.text()
                        logger.error(f"HTTP错误 {response.status}: {text[:200]}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.config.max_retries})")
                last_exception = "请求超时"
                
            except aiohttp.ClientError as e:
                logger.warning(f"客户端错误: {e} (尝试 {attempt + 1}/{self.config.max_retries})")
                last_exception = str(e)
                
            except Exception as e:
                logger.error(f"未知错误: {e} (尝试 {attempt + 1}/{self.config.max_retries})")
                last_exception = str(e)
        
        logger.error(f"所有重试失败，最后错误: {last_exception}")
        return None
    
    async def get_goods_list(self, page_num: int = 1, page_size: int = None) -> Optional[Dict]:
        """获取商品列表"""
        if page_size is None:
            from config import Config
            page_size = Config.BUFF_PAGE_SIZE
        
        url = f"{self.base_url}/api/market/goods"
        params = {
            'game': 'csgo',
            'page_num': page_num,
            'page_size': page_size,
            'tab': 'selling',
            '_': int(time.time() * 1000)  # 时间戳防缓存
        }
        
        return await self.rate_limited_request(url, params)
    
    async def get_all_goods_safe(self, max_pages: int = None) -> List[Dict]:
        """安全获取所有商品 - 降低失败率"""
        # 🔥 使用配置文件中的最大页数
        if max_pages is None:
            try:
                from config import Config
                max_pages = Config.BUFF_MAX_PAGES
            except Exception:
                max_pages = 50  # 降级到默认值
                
        logger.info(f"开始安全获取Buff商品，最大{max_pages}页...")
        
        all_items = []
        successful_pages = 0
        failed_pages = 0
        
        # 先获取第一页确定总数
        first_page = await self.get_goods_list(page_num=1)
        if not first_page or 'data' not in first_page:
            logger.error("无法获取第一页数据")
            return []
        
        first_data = first_page['data']
        total_count = first_data.get('total_count', 0)
        total_pages = first_data.get('total_page', 0)
        
        # 添加第一页数据
        first_items = first_data.get('items', [])
        all_items.extend(first_items)
        successful_pages = 1
        
        logger.info(f"第一页成功: {len(first_items)}个商品，总页数: {total_pages}")
        
        # 限制页数
        pages_to_fetch = min(total_pages, max_pages)
        logger.info(f"计划获取前{pages_to_fetch}页数据")
        
        # 串行获取剩余页面（避免并发问题）
        for page_num in range(2, pages_to_fetch + 1):
            # 🔥 检查是否已取消
            if self._cancelled:
                logger.info(f"🛑 获取被取消，已完成 {successful_pages} 页")
                break
                
            logger.info(f"正在获取第{page_num}/{pages_to_fetch}页...")
            
            page_data = await self.get_goods_list(page_num=page_num)
            
            if page_data and 'data' in page_data:
                items = page_data['data'].get('items', [])
                if items:
                    all_items.extend(items)
                    successful_pages += 1
                    logger.info(f"✅ 第{page_num}页成功: {len(items)}个商品")
                else:
                    failed_pages += 1
                    logger.warning(f"❌ 第{page_num}页无数据")
            else:
                failed_pages += 1
                logger.error(f"❌ 第{page_num}页失败")
            
            # 显示进度
            if page_num % 10 == 0:
                success_rate = (successful_pages / page_num) * 100
                logger.info(f"进度: {page_num}/{pages_to_fetch}, 成功率: {success_rate:.1f}%")
        
        # 最终统计
        total_attempted = pages_to_fetch
        success_rate = (successful_pages / total_attempted) * 100 if total_attempted > 0 else 0
        
        logger.info(f"✅ Buff数据获取完成:")
        logger.info(f"   成功页面: {successful_pages}/{total_attempted} ({success_rate:.1f}%)")
        logger.info(f"   失败页面: {failed_pages}")
        logger.info(f"   总商品数: {len(all_items)}")
        
        return all_items

class OptimizedYoupinClient:
    """优化的悠悠有品API客户端"""
    
    def __init__(self):
        self.base_url = "https://api.youpin898.com"
        self.session = None
        self.config = APIRequestConfig()
        self.request_count = 0
        self.last_request_time = 0
        self._cancelled = False  # 🔥 添加取消标志
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            from token_manager import token_manager
            self.youpin_config = token_manager.get_youpin_config()
        except Exception as e:
            logger.error(f"加载悠悠有品配置失败: {e}")
            self.youpin_config = {}
    
    def cancel(self):
        """取消当前客户端的所有操作"""
        self._cancelled = True
        logger.info("🛑 悠悠有品API客户端已取消")
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._cancelled
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=2,
            limit_per_host=1,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout,
            connect=10,
            sock_read=15
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            trust_env=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.2)
    
    async def get_market_goods_safe(self, page_index: int = 1, page_size: int = None) -> Optional[List]:
        """安全获取悠悠有品商品"""
        # 🔥 使用配置文件中的页面大小
        if page_size is None:
            try:
                from config import Config
                page_size = Config.YOUPIN_PAGE_SIZE
            except Exception:
                page_size = 100  # 降级到默认值
        
        # 速率限制 - 使用配置文件中的延迟设置
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        # 🔥 使用配置文件中的延迟，而不是硬编码8秒
        try:
            from config import Config
            min_delay = Config.YOUPIN_API_DELAY
        except Exception:
            min_delay = 3.0  # 降级到3秒默认值
            
        if time_since_last < min_delay:
            wait_time = min_delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
        
        url = f"{self.base_url}/api/homepage/pc/goods/market/querySaleTemplate"
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            # 🔥 更新版本信息
            'App-Version': '6.12.0',
            'AppType': '1',
            'AppVersion': '6.12.0',
            'Content-Type': 'application/json',
            'Platform': 'pc',
            'Secret-V': 'h5_v1',
            # 🔥 更新User-Agent
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'https://www.youpin898.com',
            'Referer': 'https://www.youpin898.com/',
            # 🔥 添加更多真实浏览器headers
            'Cache-Control': 'no-cache',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
        
        if self.youpin_config.get('device_id'):
            headers['DeviceId'] = self.youpin_config['device_id']
        if self.youpin_config.get('device_uk'):
            headers['DeviceUk'] = self.youpin_config['device_uk']
        if self.youpin_config.get('uk'):
            headers['Uk'] = self.youpin_config['uk']
        if self.youpin_config.get('b3'):
            headers['B3'] = self.youpin_config['b3']
            parts = self.youpin_config['b3'].split('-')
            if len(parts) >= 2:
                headers['TraceParent'] = f"00-{parts[0]}-{parts[1]}-01"
        if self.youpin_config.get('authorization'):
            headers['Authorization'] = self.youpin_config['authorization']
        
        payload = {
            "listSortType": 0,
            "sortType": 0,
            "pageSize": page_size,
            "pageIndex": page_index
        }
        
        for attempt in range(self.config.max_retries):
            try:
                if attempt > 0:
                    # 🔥 使用更合理的重试延迟
                    try:
                        from config import Config
                        min_retry_delay = Config.RETRY_DELAY
                    except Exception:
                        min_retry_delay = 2.0  # 降级到2秒默认值
                    
                    delay = min(
                        max(self.config.base_delay * (2 ** attempt), min_retry_delay),
                        15.0  # 减少最大延迟到15秒
                    )
                    logger.info(f"悠悠有品重试 {attempt}/{self.config.max_retries}，延迟{delay:.1f}秒")
                    await asyncio.sleep(delay)
                
                async with self.session.post(url, json=payload, headers=headers) as response:
                    logger.info(f"悠悠有品第{page_index}页响应状态: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict) and 'Data' in data:
                            goods_list = data['Data']
                            if isinstance(goods_list, list):
                                # 移除重复日志，在调用处统一打印
                                return goods_list
                            else:
                                logger.warning(f"悠悠有品响应Data格式异常: {type(goods_list)}")
                        else:
                            logger.warning(f"悠悠有品响应格式异常: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    
                    elif response.status == 429:
                        # 🔥 429错误特殊处理
                        text = await response.text()
                        logger.error(f"悠悠有品频率限制 (429): {text}")
                        if "版本过低" in text or "版本" in text:
                            logger.error("⚠️ 检测到版本问题，可能需要进一步更新版本信息")
                        # 🔥 429错误使用配置化延迟
                        try:
                            from config import Config
                            rate_limit_delay = Config.YOUPIN_API_DELAY * 10  # 10倍正常延迟
                        except Exception:
                            rate_limit_delay = 30.0  # 降级到30秒默认值
                        await asyncio.sleep(rate_limit_delay)
                    
                    else:
                        text = await response.text()
                        logger.error(f"悠悠有品HTTP错误 {response.status}: {text[:200]}")
                        
            except Exception as e:
                logger.error(f"悠悠有品请求异常 (尝试{attempt+1}): {e}")
        
        return None
    
    async def get_all_items_safe(self, max_pages: int = None) -> List[Dict]:
        """安全获取所有悠悠有品商品"""
        # 🔥 使用配置文件中的最大页数
        if max_pages is None:
            try:
                from config import Config
                max_pages = Config.YOUPIN_MAX_PAGES
            except Exception:
                max_pages = 20  # 降级到默认值
                
        logger.info(f"开始安全获取悠悠有品商品，最大{max_pages}页...")
        
        all_items = []
        successful_pages = 0
        consecutive_same_count = 0
        last_page_count = -1
        
        for page_index in range(1, max_pages + 1):
            # 🔥 检查是否已取消
            if self._cancelled:
                logger.info(f"🛑 悠悠有品获取被取消，已完成 {successful_pages} 页")
                break
                
            items = await self.get_market_goods_safe(page_index=page_index)
            
            if items:
                all_items.extend(items)
                successful_pages += 1
                current_count = len(items)
                
                logger.info(f"✅ 悠悠有品第{page_index}页成功: {current_count}个商品 (累计: {len(all_items)})")
                
                # 🔥 修改终止条件：只有当返回0个商品时才终止
                if current_count == 0:
                    logger.info(f"第{page_index}页返回0个商品，判断为最后一页")
                    break
                    
            else:
                logger.warning(f"第{page_index}页获取失败")
                # 连续失败才终止
                break
        
        success_rate = (successful_pages / max_pages) * 100
        logger.info(f"✅ 悠悠有品数据获取完成:")
        logger.info(f"   成功页面: {successful_pages}/{max_pages} ({success_rate:.1f}%)")
        logger.info(f"   总商品数: {len(all_items)}")
        
        return all_items

# 测试函数
async def test_optimized_clients():
    """测试优化后的客户端"""
    print("🧪 测试优化后的API客户端")
    print("="*50)
    
    # 测试Buff
    print("\n📊 测试Buff API...")
    async with OptimizedBuffClient() as buff_client:
        items = await buff_client.get_all_goods_safe(max_pages=3)
        print(f"Buff获取结果: {len(items)}个商品")
    
    # 测试悠悠有品
    print("\n📊 测试悠悠有品API...")
    async with OptimizedYoupinClient() as youpin_client:
        items = await youpin_client.get_all_items_safe(max_pages=3)
        print(f"悠悠有品获取结果: {len(items)}个商品")

if __name__ == "__main__":
    asyncio.run(test_optimized_clients()) 
