#!/usr/bin/env python3
import time
import sys

def test_step_by_step():
    """逐步测试API中的每一个操作"""
    print("🔍 逐步调试 buff_sell_num_min 处理过程")
    
    try:
        # 第1步：导入基础模块
        print("📦 第1步：导入基础模块...")
        start = time.time()
        import os
        from config import Config
        print(f"✅ Config导入耗时: {time.time() - start:.3f}秒")
        
        # 第2步：模拟获取请求数据
        print("\n📦 第2步：模拟获取请求数据...")
        start = time.time()
        buff_sell_num_min = 300
        updated_fields = []
        need_reprocess = False
        print(f"✅ 数据准备耗时: {time.time() - start:.3f}秒")
        
        # 第3步：配置更新
        print("\n📦 第3步：配置更新...")
        start = time.time()
        if buff_sell_num_min is not None:
            Config.update_buff_sell_num_min(int(buff_sell_num_min))
            updated_fields.append(f'Buff最小在售数量: {buff_sell_num_min}个')
            need_reprocess = True
        print(f"✅ 配置更新耗时: {time.time() - start:.3f}秒")
        
        # 第4步：检查是否会调用其他函数
        print("\n📦 第4步：检查重新处理逻辑...")
        start = time.time()
        if need_reprocess:
            print("⚠️ need_reprocess=True，但我们已经禁用了重新处理")
        print(f"✅ 重新处理检查耗时: {time.time() - start:.3f}秒")
        
        # 第5步：尝试导入可能有问题的模块
        print("\n📦 第5步：测试可能有问题的导入...")
        start = time.time()
        try:
            print("  - 导入 update_manager...")
            from update_manager import get_update_manager
            print(f"    ✅ update_manager导入耗时: {time.time() - start:.3f}秒")
            
            start = time.time()
            print("  - 获取 update_manager 实例...")
            update_manager = get_update_manager()
            print(f"    ✅ 获取实例耗时: {time.time() - start:.3f}秒")
            
        except Exception as e:
            print(f"    ❌ 导入失败: {e}, 耗时: {time.time() - start:.3f}秒")
        
        print("\n🎉 所有步骤完成，总体流程正常")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_step_by_step() 