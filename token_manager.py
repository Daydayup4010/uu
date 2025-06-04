#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token管理器
用于管理Buff和悠悠有品的认证信息
"""

import json
import os
import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenManager:
    """Token管理器"""
    
    def __init__(self, config_file: str = "tokens_config.json"):
        self.config_file = config_file
        self.tokens_config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载Token配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.tokens_config = json.load(f)
                logger.info(f"Token配置已加载: {self.config_file}")
            else:
                self.tokens_config = self.get_default_config()
                self.save_config()
                logger.info("创建默认Token配置")
        except Exception as e:
            logger.error(f"加载Token配置失败: {e}")
            self.tokens_config = self.get_default_config()
        
        return self.tokens_config
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "buff": {
                "cookies": {
                    "nts_mail_user": "",
                    "Device-Id": "",
                    "NTES_P_UTID": "",
                    "P_INFO": "",
                    "_ga": "",
                    "Qs_lvt_382223": "",
                    "Qs_pv_382223": "",
                    "_ga_C6TGHFPQ1H": "",
                    "_clck": "",
                    "Locale-Supported": "zh-Hans",
                    "game": "csgo",
                    "qr_code_verify_ticket": "",
                    "remember_me": "",
                    "session": "",
                    "csrf_token": ""
                },
                "headers": {
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Connection": "keep-alive",
                    "Referer": "https://buff.163.com/market/csgo",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors", 
                    "Sec-Fetch-Site": "same-origin",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
                    "X-Requested-With": "XMLHttpRequest",
                    "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"'
                },
                "last_updated": None,
                "status": "未配置"
            },
            "youpin": {
                "device_id": "",
                "device_uk": "",
                "uk": "",
                "b3": "",
                "authorization": "",
                "headers": {
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                    "app-version": "5.26.0",
                    "apptype": "1",
                    "appversion": "5.26.0",
                    "content-type": "application/json",
                    "origin": "https://www.youpin898.com",
                    "platform": "pc",
                    "referer": "https://www.youpin898.com/",
                    "secret-v": "h5_v1",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
                },
                "last_updated": None,
                "status": "未配置"
            }
        }
    
    def save_config(self) -> bool:
        """保存Token配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.tokens_config, f, ensure_ascii=False, indent=2)
            logger.info(f"Token配置已保存: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存Token配置失败: {e}")
            return False
    
    def update_buff_tokens(self, cookies: Dict[str, str], headers: Optional[Dict[str, str]] = None) -> bool:
        """更新Buff Token"""
        try:
            if not self.tokens_config.get("buff"):
                self.tokens_config["buff"] = self.get_default_config()["buff"]
            
            # 更新cookies
            self.tokens_config["buff"]["cookies"].update(cookies)
            
            # 更新headers（如果提供）
            if headers:
                self.tokens_config["buff"]["headers"].update(headers)
            
            # 更新时间戳和状态
            self.tokens_config["buff"]["last_updated"] = datetime.now().isoformat()
            self.tokens_config["buff"]["status"] = "已配置"
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"更新Buff Token失败: {e}")
            return False
    
    def update_youpin_tokens(self, device_info: Dict[str, str], headers: Optional[Dict[str, str]] = None) -> bool:
        """更新悠悠有品Token"""
        try:
            if not self.tokens_config.get("youpin"):
                self.tokens_config["youpin"] = self.get_default_config()["youpin"]
            
            # 更新设备信息
            for key in ["device_id", "device_uk", "uk", "b3", "authorization"]:
                if key in device_info:
                    self.tokens_config["youpin"][key] = device_info[key]
            
            # 更新headers（如果提供）
            if headers:
                self.tokens_config["youpin"]["headers"].update(headers)
            
            # 更新特定字段到headers
            if "device_id" in device_info:
                self.tokens_config["youpin"]["headers"]["deviceid"] = device_info["device_id"]
            if "device_uk" in device_info:
                self.tokens_config["youpin"]["headers"]["deviceuk"] = device_info["device_uk"]
            if "uk" in device_info:
                self.tokens_config["youpin"]["headers"]["uk"] = device_info["uk"]
            if "b3" in device_info:
                self.tokens_config["youpin"]["headers"]["b3"] = device_info["b3"]
                # 更新traceparent
                if device_info["b3"]:
                    parts = device_info["b3"].split("-")
                    if len(parts) >= 2:
                        self.tokens_config["youpin"]["headers"]["traceparent"] = f"00-{parts[0]}-{parts[1]}-01"
            if "authorization" in device_info and device_info["authorization"]:
                self.tokens_config["youpin"]["headers"]["authorization"] = device_info["authorization"]
            
            # 更新时间戳和状态
            self.tokens_config["youpin"]["last_updated"] = datetime.now().isoformat()
            self.tokens_config["youpin"]["status"] = "已配置"
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"更新悠悠有品Token失败: {e}")
            return False
    
    def get_buff_config(self) -> Dict[str, Any]:
        """获取Buff配置"""
        return self.tokens_config.get("buff", {})
    
    def get_youpin_config(self) -> Dict[str, Any]:
        """获取悠悠有品配置"""
        return self.tokens_config.get("youpin", {})
    
    def test_buff_connection(self) -> Dict[str, Any]:
        """测试Buff连接"""
        try:
            # 创建新的事件循环来运行测试
            async def test():
                try:
                    # 使用当前配置创建客户端
                    from integrated_price_system import BuffAPIClient
                    client = BuffAPIClient()
                    
                    # 更新配置
                    buff_config = self.get_buff_config()
                    if buff_config.get("cookies"):
                        client.cookies = buff_config["cookies"]
                    if buff_config.get("headers"):
                        client.headers.update(buff_config["headers"])
                    
                    async with client:
                        # 测试获取第一页数据
                        result = await client.get_goods_list(page_num=1, page_size=10)
                        
                        if result and 'data' in result:
                            items_count = len(result['data'].get('items', []))
                            total_count = result['data'].get('total_count', 0)
                            
                            return {
                                "success": True,
                                "message": f"连接成功，获取到 {items_count} 个商品",
                                "total_count": total_count,
                                "test_time": datetime.now().isoformat()
                            }
                        else:
                            return {
                                "success": False,
                                "message": "连接失败，无法获取数据",
                                "test_time": datetime.now().isoformat()
                            }
                            
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"连接错误: {str(e)}",
                        "test_time": datetime.now().isoformat()
                    }
            
            # 检查是否已经在事件循环中运行
            try:
                import asyncio
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，创建任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, test())
                    return future.result()
            except RuntimeError:
                # 没有运行中的事件循环，直接运行
                return asyncio.run(test())
            
        except Exception as e:
            return {
                "success": False,
                "message": f"测试失败: {str(e)}",
                "test_time": datetime.now().isoformat()
            }
    
    def test_youpin_connection(self) -> Dict[str, Any]:
        """测试悠悠有品连接"""
        try:
            # 创建新的事件循环来运行测试
            async def test():
                try:
                    # 使用当前配置创建客户端
                    from youpin_working_api import YoupinWorkingAPI
                    client = YoupinWorkingAPI()
                    
                    # 更新配置
                    youpin_config = self.get_youpin_config()
                    if youpin_config.get("device_id"):
                        client.device_id = youpin_config["device_id"]
                    if youpin_config.get("device_uk"):
                        client.device_uk = youpin_config["device_uk"]
                    if youpin_config.get("uk"):
                        client.uk = youpin_config["uk"]
                    if youpin_config.get("b3"):
                        client.b3 = youpin_config["b3"]
                    if youpin_config.get("authorization"):
                        client.authorization = youpin_config["authorization"]
                        # 确保authorization也添加到headers中
                        client.headers['authorization'] = youpin_config["authorization"]
                    if youpin_config.get("headers"):
                        client.headers.update(youpin_config["headers"])
                    
                    async with client:
                        # 测试获取商品数据
                        result = await client.get_market_goods(page_index=1, page_size=10)
                        
                        if result and len(result) > 0:
                            return {
                                "success": True,
                                "message": f"连接成功，获取到 {len(result)} 个商品",
                                "items_count": len(result),
                                "test_time": datetime.now().isoformat()
                            }
                        else:
                            return {
                                "success": False,
                                "message": "连接失败，无法获取数据",
                                "test_time": datetime.now().isoformat()
                            }
                            
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"连接错误: {str(e)}",
                        "test_time": datetime.now().isoformat()
                    }
            
            # 检查是否已经在事件循环中运行
            try:
                import asyncio
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，创建任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, test())
                    return future.result()
            except RuntimeError:
                # 没有运行中的事件循环，直接运行
                return asyncio.run(test())
            
        except Exception as e:
            return {
                "success": False,
                "message": f"测试失败: {str(e)}",
                "test_time": datetime.now().isoformat()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取Token状态"""
        buff_config = self.get_buff_config()
        youpin_config = self.get_youpin_config()
        
        return {
            "buff": {
                "status": buff_config.get("status", "未配置"),
                "last_updated": buff_config.get("last_updated"),
                "has_cookies": bool(buff_config.get("cookies", {}).get("session")),
                "has_csrf": bool(buff_config.get("cookies", {}).get("csrf_token"))
            },
            "youpin": {
                "status": youpin_config.get("status", "未配置"),
                "last_updated": youpin_config.get("last_updated"),
                "has_device_id": bool(youpin_config.get("device_id")),
                "has_uk": bool(youpin_config.get("uk")),
                "has_authorization": bool(youpin_config.get("authorization"))
            }
        }

# 全局Token管理器实例
token_manager = TokenManager() 