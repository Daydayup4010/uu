#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复启动时数据为空的问题

问题分析：
1. 系统启动时检测到有hashname缓存，跳过全量更新
2. 但加载价差数据失败，导致current_diff_items为空
3. api/data接口返回空数据，前端显示空页面

解决方案：
1. 清理可能损坏的缓存文件
2. 强制执行一次全量更新
3. 验证数据是否正常
"""

import os
import sys

def clear_problematic_cache():
    """清理可能有问题的缓存文件"""
    print("🧹 清理可能有问题的缓存文件...")
    
    cache_files = [
        "data/hashname_cache.pkl",
        "data/latest_price_diff.json"
    ]
    
    for cache_file in cache_files:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"   ✅ 已删除: {cache_file}")
            except Exception as e:
                print(f"   ❌ 删除失败 {cache_file}: {e}")
        else:
            print(f"   ⚠️ 文件不存在: {cache_file}")

def trigger_force_update():
    """触发强制更新"""
    print("\n🔄 触发强制全量更新...")
    
    try:
        import requests
        
        # 调用强制更新API
        response = requests.post("http://localhost:5000/api/force_update", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ 强制更新已触发")
                return True
            else:
                print(f"   ❌ 更新失败: {result.get('error')}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️ 服务器未运行，请先启动应用")
    except Exception as e:
        print(f"   ❌ 触发更新失败: {e}")
    
    return False

def check_data_status():
    """检查数据状态"""
    print("\n📊 检查数据状态...")
    
    try:
        import requests
        
        response = requests.get("http://localhost:5000/api/data", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                data = result.get('data', {})
                items_count = data.get('total_count', 0)
                print(f"   📈 当前数据: {items_count}个商品")
                
                if items_count > 0:
                    print("   ✅ 数据正常")
                    return True
                else:
                    print("   ⚠️ 数据仍为空")
                    return False
            else:
                print(f"   ❌ API错误: {result.get('error')}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️ 服务器未运行")
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    return False

def main():
    """主函数"""
    print("🛠️ 修复启动时数据为空问题")
    print("="*50)
    
    # 1. 清理缓存
    clear_problematic_cache()
    
    # 2. 检查当前状态
    if check_data_status():
        print("\n🎉 数据正常，无需修复!")
        return
    
    # 3. 触发强制更新
    if trigger_force_update():
        print("\n⏳ 更新已触发，请等待2-3分钟后重新检查")
        print("   或者访问前端页面刷新查看")
    
    print("\n📝 修复完成! 建议操作:")
    print("   1. 重启应用以确保修复生效")
    print("   2. 等待2-3分钟让全量更新完成")
    print("   3. 刷新前端页面查看数据")
    print("   4. 如果仍有问题，请检查应用日志")

if __name__ == "__main__":
    main() 