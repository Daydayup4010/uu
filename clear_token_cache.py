#!/usr/bin/env python3
"""清除Token验证缓存"""
import requests
import json

def clear_token_cache():
    """清除Token验证缓存并重新验证"""
    base_url = 'http://localhost:5000'
    
    print("🧹 清除Token验证缓存")
    print("=" * 40)
    
    # 1. 停止验证服务
    print("1️⃣ 停止Token验证服务...")
    try:
        response = requests.post(f"{base_url}/api/tokens/validation-service", 
                               json={'action': 'stop'}, timeout=10)
        if response.status_code == 200:
            print("✅ 验证服务已停止")
        else:
            print(f"⚠️ 停止服务响应: {response.status_code}")
    except Exception as e:
        print(f"❌ 停止服务失败: {e}")
    
    # 2. 强制验证Buff Token
    print("\n2️⃣ 强制验证Buff Token...")
    try:
        response = requests.post(f"{base_url}/api/tokens/validate/buff", 
                               json={'force_check': True}, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Buff验证结果: {json.dumps(data, indent=2, ensure_ascii=False)}")
            buff_valid = data.get('data', {}).get('valid', False)
        else:
            print(f"❌ Buff验证失败: {response.status_code}")
            buff_valid = False
    except Exception as e:
        print(f"❌ Buff验证异常: {e}")
        buff_valid = False
    
    # 3. 强制验证悠悠有品Token
    print("\n3️⃣ 强制验证悠悠有品Token...")
    try:
        response = requests.post(f"{base_url}/api/tokens/validate/youpin", 
                               json={'force_check': True}, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"📊 悠悠有品验证结果: {json.dumps(data, indent=2, ensure_ascii=False)}")
            youpin_valid = data.get('data', {}).get('valid', False)
        else:
            print(f"❌ 悠悠有品验证失败: {response.status_code}")
            youpin_valid = False
    except Exception as e:
        print(f"❌ 悠悠有品验证异常: {e}")
        youpin_valid = False
    
    # 4. 检查Token状态
    print("\n4️⃣ 检查更新后的Token状态...")
    try:
        response = requests.get(f"{base_url}/api/tokens/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Token状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取状态失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取状态异常: {e}")
    
    # 5. 重新启动验证服务
    print("\n5️⃣ 重新启动Token验证服务...")
    try:
        response = requests.post(f"{base_url}/api/tokens/validation-service", 
                               json={'action': 'start'}, timeout=10)
        if response.status_code == 200:
            print("✅ 验证服务已重新启动")
        else:
            print(f"⚠️ 启动服务响应: {response.status_code}")
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")
    
    # 6. 等待一下，然后检查警报
    print("\n6️⃣ 检查警报状态...")
    import time
    time.sleep(3)  # 等待3秒
    
    try:
        response = requests.get(f"{base_url}/api/tokens/alerts", timeout=10)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('data', {}).get('active_alerts', [])
            print(f"🚨 活跃警报数量: {len(alerts)}")
            
            for alert in alerts:
                platform = alert.get('platform')
                message = alert.get('message')
                print(f"   {platform}: {message}")
        else:
            print(f"❌ 获取警报失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取警报异常: {e}")
    
    # 总结
    print("\n" + "=" * 40)
    print("📋 清理总结:")
    print(f"   Buff Token: {'✅ 有效' if buff_valid else '❌ 无效'}")
    print(f"   悠悠有品Token: {'✅ 有效' if youpin_valid else '❌ 无效'}")
    
    if buff_valid and not youpin_valid:
        print("\n💡 结论: 只有悠悠有品Token无效，Buff Token是正常的")
    elif not buff_valid and not youpin_valid:
        print("\n💡 结论: 两个Token都无效")
    elif buff_valid and youpin_valid:
        print("\n💡 结论: 两个Token都有效")
    else:
        print("\n💡 结论: 只有Buff Token无效，悠悠有品Token是正常的")

if __name__ == "__main__":
    clear_token_cache() 