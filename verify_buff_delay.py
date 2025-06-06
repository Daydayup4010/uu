#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证BUFF_API_DELAY配置是否生效
"""

from config import Config
from optimized_api_client import APIRequestConfig

def verify_buff_delay_config():
    """验证Buff延迟配置"""
    print("🔍 验证BUFF_API_DELAY配置")
    print("=" * 50)
    
    # 检查配置文件中的值
    print(f"📋 config.py中的BUFF_API_DELAY: {Config.BUFF_API_DELAY}秒")
    
    # 检查APIRequestConfig是否正确读取
    api_config = APIRequestConfig()
    print(f"📋 APIRequestConfig中的rate_limit_delay: {api_config.rate_limit_delay}秒")
    
    # 验证是否一致
    if api_config.rate_limit_delay == Config.BUFF_API_DELAY:
        print("✅ 配置一致！BUFF_API_DELAY配置已生效")
    else:
        print("❌ 配置不一致！BUFF_API_DELAY配置未生效")
        print(f"   期望值: {Config.BUFF_API_DELAY}秒")
        print(f"   实际值: {api_config.rate_limit_delay}秒")
    
    print("\n📊 验证总结:")
    print(f"   - 配置文件值: {Config.BUFF_API_DELAY}秒")
    print(f"   - 实际使用值: {api_config.rate_limit_delay}秒")
    print(f"   - 状态: {'✅ 生效' if api_config.rate_limit_delay == Config.BUFF_API_DELAY else '❌ 未生效'}")

if __name__ == "__main__":
    verify_buff_delay_config() 