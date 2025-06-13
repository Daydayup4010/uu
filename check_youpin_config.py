#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from token_manager import token_manager

def check_youpin_config():
    """检查悠悠有品Token配置"""
    print("🔍 检查悠悠有品Token配置...")
    
    config = token_manager.get_youpin_config()
    
    print("\n📊 配置详情:")
    print("=" * 50)
    
    device_id = config.get('device_id', '')
    uk = config.get('uk', '')
    device_uk = config.get('device_uk', '')
    b3 = config.get('b3', '')
    authorization = config.get('authorization', '')
    
    print(f"Device ID: {'✅ 已配置' if device_id else '❌ 未配置'}")
    if device_id:
        print(f"   长度: {len(device_id)} 字符")
        print(f"   前10字符: {device_id[:10]}...")
    
    print(f"UK: {'✅ 已配置' if uk else '❌ 未配置'}")
    if uk:
        print(f"   长度: {len(uk)} 字符")
        print(f"   前10字符: {uk[:10]}...")
    
    print(f"Device UK: {'✅ 已配置' if device_uk else '❌ 未配置'}")
    if device_uk:
        print(f"   长度: {len(device_uk)} 字符")
    
    print(f"B3: {'✅ 已配置' if b3 else '❌ 未配置'}")
    if b3:
        print(f"   长度: {len(b3)} 字符")
    
    print(f"Authorization: {'✅ 已配置' if authorization else '❌ 未配置'}")
    if authorization:
        print(f"   长度: {len(authorization)} 字符")
    
    # 检查必需字段
    print(f"\n🎯 配置状态:")
    print("=" * 50)
    
    required_fields = ['device_id', 'uk']
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        print(f"❌ 缺少必需字段: {', '.join(missing_fields)}")
        return False
    else:
        print("✅ 所有必需字段都已配置")
        
        # 检查字段格式
        issues = []
        
        if len(device_id) < 10:
            issues.append("Device ID长度可能不正确")
        
        if len(uk) < 10:
            issues.append("UK长度可能不正确")
        
        if issues:
            print(f"⚠️ 潜在问题: {', '.join(issues)}")
            print("💡 建议: 请检查Token是否是最新的，可能需要重新获取")
            return False
        else:
            print("✅ 配置格式看起来正常")
            print("💡 如果仍然验证失败，可能是Token已过期，需要重新获取")
            return True

if __name__ == "__main__":
    check_youpin_config() 