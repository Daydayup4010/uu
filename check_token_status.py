#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def check_token_status():
    """检查Token状态"""
    try:
        print("🔍 检查Token状态...")
        
        # 获取Token状态
        response = requests.get('http://localhost:5000/api/tokens/status')
        
        if response.status_code == 200:
            data = response.json()
            
            if data['success']:
                buff = data['data']['buff']
                youpin = data['data']['youpin']
                
                print("\n📊 Token状态详情:")
                print("=" * 50)
                
                print(f"🔵 Buff Token:")
                print(f"   - 已配置: {buff['configured']}")
                print(f"   - 缓存有效: {buff['cached_valid']}")
                print(f"   - 缓存错误: {buff.get('cached_error', 'None')}")
                print(f"   - 最后验证: {buff.get('last_validation', 'None')}")
                
                print(f"\n🟡 悠悠有品Token:")
                print(f"   - 已配置: {youpin['configured']}")
                print(f"   - 缓存有效: {youpin['cached_valid']}")
                print(f"   - 缓存错误: {youpin.get('cached_error', 'None')}")
                print(f"   - 最后验证: {youpin.get('last_validation', 'None')}")
                
                # 分析是否应该显示警报
                print("\n🚨 警报分析:")
                print("=" * 50)
                
                def should_show_alert(token_info, name):
                    configured = token_info['configured']
                    cached_valid = token_info['cached_valid']
                    cached_error = token_info.get('cached_error')
                    
                    if not configured:
                        print(f"   {name}: 未配置，不显示警报")
                        return False
                    
                    if cached_valid is True:
                        print(f"   {name}: Token有效，不显示警报")
                        return False
                    
                    if cached_valid is False and cached_error:
                        # 检查错误类型
                        error_lower = cached_error.lower()
                        
                        # 排除的关键词（网络或技术问题）
                        exclude_keywords = [
                            '网络', '超时', '连接', '响应为空', 'timeout', 'network', 
                            'connection', 'api响应为空', '格式异常', 'json', 'parse', 
                            '500', '502', '503', '504'
                        ]
                        
                        has_exclude = any(keyword in error_lower for keyword in exclude_keywords)
                        
                        if has_exclude:
                            print(f"   {name}: 验证失败但非Token失效（{cached_error}），不显示警报")
                            return False
                        
                        # Token失效关键词
                        expired_keywords = [
                            '失效', '过期', '无效', '登录', '认证失败', 'token已失效', 
                            'token无效', '401', '403', 'unauthorized', 'forbidden'
                        ]
                        
                        has_expired = any(keyword in error_lower for keyword in expired_keywords)
                        
                        if has_expired:
                            print(f"   {name}: Token失效（{cached_error}），应显示警报")
                            return True
                        else:
                            print(f"   {name}: 验证失败但原因不明（{cached_error}），不显示警报")
                            return False
                    
                    print(f"   {name}: 状态不明确，不显示警报")
                    return False
                
                buff_alert = should_show_alert(buff, "Buff")
                youpin_alert = should_show_alert(youpin, "悠悠有品")
                
                print(f"\n🎯 最终结论:")
                print(f"   - 应显示Buff警报: {buff_alert}")
                print(f"   - 应显示悠悠有品警报: {youpin_alert}")
                print(f"   - 应显示任何警报: {buff_alert or youpin_alert}")
                
            else:
                print(f"❌ API返回错误: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_token_status() 