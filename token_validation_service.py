#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token验证服务

定期检查API Token状态，并提供失效通知功能
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from threading import Thread
import json

logger = logging.getLogger(__name__)

@dataclass
class TokenAlert:
    """Token警报信息"""
    platform: str
    alert_type: str  # 'expired', 'expiring', 'error'
    message: str
    timestamp: datetime
    resolved: bool = False

class TokenValidationService:
    """Token验证服务"""
    
    def __init__(self, 
                 check_interval: int = 300,  # 5分钟检查一次
                 alert_threshold: int = 3600):  # 1小时内失效预警
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.running = False
        self.alerts: List[TokenAlert] = []
        self.alert_callbacks: List[Callable] = []
        self.last_check = {}
        self.validation_history = {}
        
        # 统计信息
        self.stats = {
            'total_checks': 0,
            'buff_failures': 0,
            'youpin_failures': 0,
            'last_successful_check': None
        }
    
    def add_alert_callback(self, callback: Callable):
        """添加警报回调函数"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable):
        """移除警报回调函数"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def _trigger_alerts(self, alert: TokenAlert):
        """触发警报回调"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"警报回调执行失败: {e}")
    
    async def check_single_token(self, platform: str) -> Dict:
        """检查单个平台的Token"""
        try:
            # 直接使用TokenManager，避免HTTP API循环调用
            from token_manager import TokenManager
            
            # 创建新的TokenManager实例，避免全局实例的上下文问题
            tm = TokenManager()
            
            if platform == 'buff':
                result = await tm.validate_buff_token(force_check=True)
            elif platform == 'youpin':
                result = await tm.validate_youpin_token(force_check=True)
            else:
                result = {'valid': False, 'error': f'不支持的平台: {platform}', 'cached': False}
            
            # 记录历史
            if platform not in self.validation_history:
                self.validation_history[platform] = []
            
            self.validation_history[platform].append({
                'timestamp': datetime.now().isoformat(),
                'valid': result.get('valid', False),
                'error': result.get('error', ''),
                'cached': result.get('cached', False)
            })
            
            # 只保留最近100条记录
            if len(self.validation_history[platform]) > 100:
                self.validation_history[platform] = self.validation_history[platform][-100:]
            
            logger.info(f"[DEBUG] {platform} Token验证结果: valid={result.get('valid')}, error={result.get('error')}")
            return result
            
        except Exception as e:
            logger.error(f"检查{platform}Token失败: {e}")
            return {'valid': False, 'error': str(e), 'cached': False}
    
    async def check_all_tokens(self) -> Dict:
        """检查所有Token状态"""
        try:
            results = {}
            
            # 并发检查
            buff_result, youpin_result = await asyncio.gather(
                self.check_single_token('buff'),
                self.check_single_token('youpin'),
                return_exceptions=True
            )
            
            # 处理结果
            if isinstance(buff_result, Exception):
                buff_result = {'valid': False, 'error': str(buff_result), 'cached': False}
            if isinstance(youpin_result, Exception):
                youpin_result = {'valid': False, 'error': str(youpin_result), 'cached': False}
            
            results['buff'] = buff_result
            results['youpin'] = youpin_result
            
            # 更新统计
            self.stats['total_checks'] += 1
            
            # 只对真正的Token失效创建警报，忽略技术性错误
            if not buff_result['valid']:
                error_msg = buff_result.get('error', '')
                # 只有明确的认证错误才算Token失效
                if any(keyword in error_msg.lower() for keyword in ['login', 'auth', '登录', '认证', 'unauthorized', '401', '403']):
                    self.stats['buff_failures'] += 1
                    self._create_alert('buff', 'expired', buff_result['error'])
                else:
                    logger.info(f"[DEBUG] Buff Token技术性错误，不创建警报: {error_msg}")
            
            if not youpin_result['valid']:
                error_msg = youpin_result.get('error', '')
                # 只有明确的认证错误才算Token失效
                if any(keyword in error_msg.lower() for keyword in ['login', 'auth', '登录', '认证', 'unauthorized', '401', '403']):
                    self.stats['youpin_failures'] += 1
                    self._create_alert('youpin', 'expired', youpin_result['error'])
                else:
                    logger.info(f"[DEBUG] 悠悠有品Token技术性错误，不创建警报: {error_msg}")
            
            # 记录最后检查时间
            self.last_check = {
                'timestamp': datetime.now().isoformat(),
                'buff_valid': buff_result['valid'],
                'youpin_valid': youpin_result['valid']
            }
            
            if buff_result['valid'] and youpin_result['valid']:
                self.stats['last_successful_check'] = datetime.now().isoformat()
            
            return results
            
        except Exception as e:
            logger.error(f"检查所有Token失败: {e}")
            return {
                'buff': {'valid': False, 'error': str(e), 'cached': False},
                'youpin': {'valid': False, 'error': str(e), 'cached': False}
            }
    
    def _create_alert(self, platform: str, alert_type: str, message: str):
        """创建警报"""
        # 避免重复警报
        recent_alerts = [
            alert for alert in self.alerts 
            if alert.platform == platform 
            and alert.alert_type == alert_type 
            and not alert.resolved
            and datetime.now() - alert.timestamp < timedelta(hours=1)
        ]
        
        if not recent_alerts:
            alert = TokenAlert(
                platform=platform,
                alert_type=alert_type,
                message=message,
                timestamp=datetime.now()
            )
            
            self.alerts.append(alert)
            self._trigger_alerts(alert)
            
            logger.warning(f"[ALERT] Token警报: {platform} - {alert_type} - {message}")
    
    def get_active_alerts(self) -> List[TokenAlert]:
        """获取活跃警报"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: int):
        """解决警报"""
        if 0 <= alert_id < len(self.alerts):
            self.alerts[alert_id].resolved = True
    
    def clear_resolved_alerts(self):
        """清除已解决的警报"""
        self.alerts = [alert for alert in self.alerts if not alert.resolved]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'active_alerts': len(self.get_active_alerts()),
            'total_alerts': len(self.alerts),
            'last_check': self.last_check,
            'service_running': self.running
        }
    
    def get_validation_history(self, platform: str = None, limit: int = 50) -> Dict:
        """获取验证历史"""
        if platform:
            return {
                platform: self.validation_history.get(platform, [])[-limit:]
            }
        else:
            return {
                key: value[-limit:] for key, value in self.validation_history.items()
            }
    
    async def _run_validation_loop(self):
        """运行验证循环"""
        logger.info("[DEBUG] Token验证服务开始运行")
        
        while self.running:
            try:
                logger.debug("[DEBUG] 开始检查Token状态")
                await self.check_all_tokens()
                logger.debug("[SUCCESS] Token状态检查完成")
                
                # 清理旧的已解决警报
                self.clear_resolved_alerts()
                
            except Exception as e:
                logger.error(f"Token验证循环异常: {e}")
            
            # 等待下次检查
            await asyncio.sleep(self.check_interval)
        
        logger.info("[STOP] Token验证服务已停止")
    
    def start(self):
        """启动验证服务"""
        if self.running:
            logger.warning("Token验证服务已经在运行")
            return
        
        self.running = True
        
        # 在独立线程中运行异步循环
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._run_validation_loop())
            finally:
                loop.close()
        
        self.thread = Thread(target=run_loop, daemon=True)
        self.thread.start()
        
        logger.info("[START] Token验证服务已启动")
    
    def stop(self):
        """停止验证服务"""
        if not self.running:
            logger.warning("Token验证服务未运行")
            return
        
        self.running = False
        logger.info("[STOP] 正在停止Token验证服务...")
        
        # 等待线程结束
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=5.0)
    
    def export_alerts(self, filepath: str):
        """导出警报到文件"""
        try:
            alerts_data = []
            for alert in self.alerts:
                alerts_data.append({
                    'platform': alert.platform,
                    'alert_type': alert.alert_type,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved
                })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(alerts_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"警报数据已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"导出警报数据失败: {e}")


class TokenAlertHandler:
    """Token警报处理器"""
    
    def __init__(self):
        self.notification_queue = []
    
    def handle_alert(self, alert: TokenAlert):
        """处理警报"""
        notification = {
            'type': 'token_alert',
            'platform': alert.platform,
            'alert_type': alert.alert_type,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'severity': self._get_severity(alert.alert_type)
        }
        
        self.notification_queue.append(notification)
        
        # 打印到日志
        severity_emoji = {
            'expired': '[ERROR]',
            'expiring': '[WARNING]',
            'error': '[ALERT]'
        }
        
        emoji = severity_emoji.get(alert.alert_type, '❓')
        logger.warning(f"{emoji} Token警报 [{alert.platform}]: {alert.message}")
    
    def _get_severity(self, alert_type: str) -> str:
        """获取警报严重程度"""
        severity_map = {
            'expired': 'high',
            'expiring': 'medium',
            'error': 'high'
        }
        return severity_map.get(alert_type, 'low')
    
    def get_notifications(self) -> List[Dict]:
        """获取通知队列"""
        return self.notification_queue
    
    def clear_notifications(self):
        """清空通知队列"""
        self.notification_queue.clear()


# 全局实例
token_validation_service = TokenValidationService()
token_alert_handler = TokenAlertHandler()

# 注册警报处理器
token_validation_service.add_alert_callback(token_alert_handler.handle_alert) 