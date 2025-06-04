#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证配置更新
"""

from config import Config

def main():
    print("🔧 配置验证")
    print("="*40)
    
    print(f"📊 价格差异配置:")
    print(f"   最小价差: {Config.PRICE_DIFF_MIN}元")
    print(f"   最大价差: {Config.PRICE_DIFF_MAX}元")
    print(f"   兼容阈值: {Config.PRICE_DIFF_THRESHOLD}元")
    
    print(f"\n📋 数量限制配置:")
    print(f"   最大输出数量: {Config.MAX_OUTPUT_ITEMS}")
    print(f"   Buff最大页数: {Config.BUFF_MAX_PAGES}")
    print(f"   悠悠有品最大页数: {Config.YOUPIN_MAX_PAGES}")
    print(f"   监控最大数量: {Config.MONITOR_MAX_ITEMS}")
    
    print(f"\n🔍 价格区间测试:")
    test_values = [2.0, 3.5, 4.0, 5.5, 10.0]
    for value in test_values:
        in_range = Config.is_price_diff_in_range(value)
        status = "✅ 符合" if in_range else "❌ 不符合"
        print(f"   {value}元: {status}")
    
    print(f"\n🔄 测试区间更新:")
    old_range = Config.get_price_range()
    print(f"   原区间: {old_range}")
    
    Config.update_price_range(5.0, 10.0)
    new_range = Config.get_price_range()
    print(f"   新区间: {new_range}")
    
    # 恢复原设置
    Config.update_price_range(old_range[0], old_range[1])
    restored_range = Config.get_price_range()
    print(f"   恢复区间: {restored_range}")
    
    print(f"\n✅ 配置验证完成！")

if __name__ == "__main__":
    main() 