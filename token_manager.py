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
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class TokenManager:
    """Token管理器（单例模式）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, config_file: str = "tokens_config.json"):
        if cls._instance is None:
            cls._instance = super(TokenManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: str = "tokens_config.json"):
        if self._initialized:
            return
            
        self.config_file = config_file
        self.tokens_config = {}
        self.load_config()
        
        # 缓存验证结果，避免频繁检查
        self._buff_validation_cache = {"valid": False, "checked_at": None, "error": None}
        self._youpin_validation_cache = {"valid": False, "checked_at": None, "error": None}
        self._cache_duration = 300  # 5分钟缓存时间
        
        # 🔥 新增：全局验证结果缓存
        self._global_validation_cache = {
            "result": None,
            "cached_at": None,
            "cache_duration": 300  # 5分钟
        }
        
        # 🔥 新增：文件缓存支持
        self._cache_file = 'token_validation_cache.json'
        self._load_cache_from_file()
        
        self._initialized = True
    
    def _load_cache_from_file(self):
        """从文件加载缓存"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                self._global_validation_cache = {
                    'result': cache_data.get('result'),
                    'cached_at': datetime.fromtimestamp(cache_data.get('cached_at', 0)),
                    'cache_duration': cache_data.get('cache_duration', 300)
                }
                logger.info("📂 已从文件加载Token验证缓存")
        except Exception as e:
            logger.warning(f"⚠️ 从文件加载缓存失败: {e}")
    
    def _save_cache_to_file(self):
        """保存缓存到文件"""
        try:
            if self._global_validation_cache['result'] and self._global_validation_cache['cached_at']:
                cache_data = {
                    'result': self._global_validation_cache['result'],
                    'cached_at': self._global_validation_cache['cached_at'].timestamp(),
                    'cache_duration': self._global_validation_cache['cache_duration']
                }
                
                with open(self._cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                logger.info("💾 已保存Token验证缓存到文件")
        except Exception as e:
            logger.warning(f"⚠️ 保存缓存到文件失败: {e}")
    
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

    def _is_cache_valid(self, cache_info: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        if not cache_info.get("checked_at"):
            return False
        
        checked_at = datetime.fromisoformat(cache_info["checked_at"])
        return datetime.now() - checked_at < timedelta(seconds=self._cache_duration)

    async def validate_buff_token(self, force_check: bool = False) -> Dict[str, Any]:
        """验证Buff Token是否有效"""
        if not force_check and self._is_cache_valid(self._buff_validation_cache):
            return {
                "valid": self._buff_validation_cache["valid"],
                "error": self._buff_validation_cache["error"],
                "cached": True
            }
        
        try:
            # 检查基本配置
            buff_config = self.get_buff_config()
            if not buff_config.get("cookies", {}).get("session"):
                result = {"valid": False, "error": "Session cookie未配置", "cached": False}
                self._update_cache("buff", result)
                return result
            
            if not buff_config.get("cookies", {}).get("csrf_token"):
                result = {"valid": False, "error": "CSRF token未配置", "cached": False}
                self._update_cache("buff", result)
                return result
            
            # 🔥 修复：尝试实际API调用，正确处理HTTP状态码
            try:
                from integrated_price_system import BuffAPIClient
                async with BuffAPIClient() as client:
                    # 尝试获取第一页数据
                    result = await client.get_goods_list(page_num=1, page_size=1)
                    
                    if result and 'data' in result:
                        validation_result = {"valid": True, "error": None, "cached": False}
                        self._update_cache("buff", validation_result)
                        return validation_result
                    else:
                        # 检查是否是认证问题
                        if isinstance(result, dict) and result.get('error'):
                            error_msg = result['error']
                            if "login" in error_msg.lower() or "auth" in error_msg.lower():
                                validation_result = {"valid": False, "error": "Token已失效，需要重新登录", "cached": False}
                            else:
                                validation_result = {"valid": False, "error": f"API调用失败: {error_msg}", "cached": False}
                        else:
                            validation_result = {"valid": False, "error": "API响应格式异常", "cached": False}
                        
                        self._update_cache("buff", validation_result)
                        return validation_result
                        
            except Exception as api_error:
                error_msg = str(api_error)
                
                # 🔥 修复：正确处理不同类型的错误
                if "401" in error_msg or "403" in error_msg or "login" in error_msg.lower():
                    validation_result = {"valid": False, "error": "Token已失效，需要重新登录", "cached": False}
                elif "429" in error_msg or "频率限制" in error_msg:
                    # 429是频率限制，不是Token失效
                    validation_result = {"valid": None, "error": "API频率限制，请稍后重试", "cached": False}
                elif "timeout" in error_msg.lower():
                    validation_result = {"valid": None, "error": "网络超时，请检查网络连接", "cached": False}
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg or "504" in error_msg:
                    validation_result = {"valid": None, "error": "服务器错误，请稍后重试", "cached": False}
                else:
                    # 其他未知错误，可能是Token问题
                    validation_result = {"valid": False, "error": f"Token验证失败: {error_msg}", "cached": False}
                
                self._update_cache("buff", validation_result)
                return validation_result
                
        except Exception as e:
            logger.error(f"验证Buff Token失败: {e}")
            validation_result = {"valid": None, "error": f"验证过程异常: {str(e)}", "cached": False}
            self._update_cache("buff", validation_result)
            return validation_result

    async def validate_youpin_token(self, force_check: bool = False) -> Dict[str, Any]:
        """验证悠悠有品Token是否有效"""
        if not force_check and self._is_cache_valid(self._youpin_validation_cache):
            return {
                "valid": self._youpin_validation_cache["valid"],
                "error": self._youpin_validation_cache["error"],
                "cached": True
            }
        
        try:
            # 检查基本配置
            youpin_config = self.get_youpin_config()
            if not youpin_config.get("device_id"):
                result = {"valid": False, "error": "Device ID未配置", "cached": False}
                self._update_cache("youpin", result)
                return result
            
            if not youpin_config.get("uk"):
                result = {"valid": False, "error": "UK参数未配置", "cached": False}
                self._update_cache("youpin", result)
                return result
            
            # 🔥 修复：尝试实际API调用，正确处理HTTP状态码
            try:
                from youpin_working_api import YoupinWorkingAPI
                async with YoupinWorkingAPI() as client:
                    # 尝试获取第一页数据
                    result = await client.get_market_goods(page_index=1, page_size=1)
                    
                    if result and len(result) > 0:
                        validation_result = {"valid": True, "error": None, "cached": False}
                        self._update_cache("youpin", validation_result)
                        return validation_result
                    else:
                        # 🔥 修复：空结果可能是Token失效，也可能是其他原因
                        validation_result = {"valid": False, "error": "Token可能已失效或API异常", "cached": False}
                        self._update_cache("youpin", validation_result)
                        return validation_result
                        
            except Exception as api_error:
                error_msg = str(api_error)
                
                # 🔥 修复：正确处理不同类型的错误
                if "401" in error_msg or "403" in error_msg or "unauthorized" in error_msg.lower():
                    validation_result = {"valid": False, "error": "Token已失效，需要重新配置", "cached": False}
                elif "429" in error_msg or "频率限制" in error_msg:
                    # 429是频率限制，不是Token失效
                    validation_result = {"valid": None, "error": "API频率限制，请稍后重试", "cached": False}
                elif "timeout" in error_msg.lower():
                    validation_result = {"valid": None, "error": "网络超时，请检查网络连接", "cached": False}
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg or "504" in error_msg:
                    validation_result = {"valid": None, "error": "服务器错误，请稍后重试", "cached": False}
                else:
                    # 其他未知错误，可能是Token问题
                    validation_result = {"valid": False, "error": f"Token验证失败: {error_msg}", "cached": False}
                
                self._update_cache("youpin", validation_result)
                return validation_result
                
        except Exception as e:
            logger.error(f"验证悠悠有品Token失败: {e}")
            validation_result = {"valid": None, "error": f"验证过程异常: {str(e)}", "cached": False}
            self._update_cache("youpin", validation_result)
            return validation_result

    def _update_cache(self, platform: str, result: Dict[str, Any]):
        """更新缓存"""
        cache_info = {
            "valid": result["valid"],
            "error": result["error"],
            "checked_at": datetime.now().isoformat()
        }
        
        if platform == "buff":
            self._buff_validation_cache = cache_info
        elif platform == "youpin":
            self._youpin_validation_cache = cache_info

    async def validate_all_tokens(self, force_check: bool = False) -> Dict[str, Any]:
        """验证所有Token状态"""
        try:
            # 检查缓存（除非强制检查）
            if not force_check and self.is_cache_valid():
                cached_result = self.get_cached_validation_result()
                if cached_result:
                    logger.info("🔄 使用缓存的Token验证结果")
                    return cached_result
            
            # 并发验证两个平台的token
            buff_result, youpin_result = await asyncio.gather(
                self.validate_buff_token(force_check),
                self.validate_youpin_token(force_check),
                return_exceptions=True
            )
            
            # 处理异常情况
            if isinstance(buff_result, Exception):
                buff_result = {"valid": False, "error": f"验证异常: {str(buff_result)}", "cached": False}
            
            if isinstance(youpin_result, Exception):
                youpin_result = {"valid": False, "error": f"验证异常: {str(youpin_result)}", "cached": False}
            
            result = {
                "buff": buff_result,
                "youpin": youpin_result,
                "overall_valid": buff_result["valid"] and youpin_result["valid"]
            }
            
            # 🔥 修复：更新全局缓存
            self._update_global_cache(result)
            
            return result
            
        except Exception as e:
            logger.error(f"验证所有Token失败: {e}")
            error_result = {
                "buff": {"valid": False, "error": f"验证失败: {str(e)}", "cached": False},
                "youpin": {"valid": False, "error": f"验证失败: {str(e)}", "cached": False},
                "overall_valid": False
            }
            # 🔥 修复：即使出错也要更新缓存
            self._update_global_cache(error_result)
            return error_result

    def get_token_status_summary(self) -> Dict[str, Any]:
        """获取Token状态摘要（不进行实际验证，仅基于配置）"""
        buff_config = self.get_buff_config()
        youpin_config = self.get_youpin_config()
        
        return {
            "buff": {
                "configured": bool(buff_config.get("cookies", {}).get("session")),
                "last_updated": buff_config.get("last_updated"),
                "last_validation": self._buff_validation_cache.get("checked_at"),
                "cached_valid": self._buff_validation_cache.get("valid", False),
                "cached_error": self._buff_validation_cache.get("error")
            },
            "youpin": {
                "configured": bool(youpin_config.get("device_id") and youpin_config.get("uk")),
                "last_updated": youpin_config.get("last_updated"),
                "last_validation": self._youpin_validation_cache.get("checked_at"),
                "cached_valid": self._youpin_validation_cache.get("valid", False),
                "cached_error": self._youpin_validation_cache.get("error")
            }
        }

    # 🔥 新增：缓存管理方法
    def get_cached_validation_result(self) -> Optional[Dict[str, Any]]:
        """获取缓存的验证结果"""
        cache = self._global_validation_cache
        if cache["result"] and cache["cached_at"]:
            return cache["result"]
        return None
    
    def is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        cache = self._global_validation_cache
        if not cache["cached_at"]:
            return False
        
        elapsed = (datetime.now() - cache["cached_at"]).total_seconds()
        return elapsed < cache["cache_duration"]
    
    def _update_global_cache(self, result: Dict[str, Any]):
        """更新全局验证缓存"""
        self._global_validation_cache["result"] = result
        self._global_validation_cache["cached_at"] = datetime.now()
        # 🔥 新增：同时保存到文件
        self._save_cache_to_file()
    
    # 🔥 新增：同步验证方法
    def validate_all_tokens_sync(self, force_check: bool = False) -> Dict[str, Any]:
        """同步验证所有Token（避免事件循环开销）"""
        try:
            import asyncio
            
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 运行异步验证
                result = loop.run_until_complete(self.validate_all_tokens(force_check))
                
                # 更新缓存
                self._update_global_cache(result)
                
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ 同步Token验证失败: {e}")
            return {
                "buff": {"valid": False, "error": str(e)},
                "youpin": {"valid": False, "error": str(e)},
                "overall_valid": False,
                "validation_time": datetime.now().isoformat()
            }
    
    def validate_buff_token_sync(self, force_check: bool = False) -> Dict[str, Any]:
        """同步验证Buff Token"""
        try:
            import asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self.validate_buff_token(force_check))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ 同步Buff Token验证失败: {e}")
            return {"valid": False, "error": str(e)}
    
    def validate_youpin_token_sync(self, force_check: bool = False) -> Dict[str, Any]:
        """同步验证悠悠有品Token"""
        try:
            import asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self.validate_youpin_token(force_check))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ 同步悠悠有品Token验证失败: {e}")
            return {"valid": False, "error": str(e)}


# 全局Token管理器实例
token_manager = TokenManager() 