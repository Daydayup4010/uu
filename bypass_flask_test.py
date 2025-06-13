#!/usr/bin/env python3
import time
import json

def simulate_api_settings_post():
    """直接模拟api_settings函数的POST逻辑"""
    print("🔍 直接模拟 API Settings POST 逻辑")
    
    try:
        # 导入必要模块
        print("📦 导入模块...")
        start = time.time()
        from config import Config
        print(f"✅ Config导入耗时: {time.time() - start:.3f}秒")
        
        # 模拟请求数据
        print("\n📝 模拟请求数据...")
        start = time.time()
        data = {"buff_sell_num_min": 300}
        
        threshold = data.get('threshold')
        price_min = data.get('price_min')
        price_max = data.get('price_max')
        buff_price_min = data.get('buff_price_min')
        buff_price_max = data.get('buff_price_max')
        buff_sell_num_min = data.get('buff_sell_num_min')
        max_output_items = data.get('max_output_items')
        
        updated_fields = []
        print(f"✅ 数据解析耗时: {time.time() - start:.3f}秒")
        
        # 处理各种配置更新
        print("\n🔧 配置更新...")
        start = time.time()
        
        # 更新价差阈值（兼容性）
        if threshold is not None:
            Config.PRICE_DIFF_THRESHOLD = float(threshold)
            updated_fields.append(f'价差阈值: {threshold}元')
        
        # 优化：跟踪是否需要重新处理数据
        need_reprocess = False
        
        # 更新价格区间
        if price_min is not None and price_max is not None:
            Config.update_price_range(float(price_min), float(price_max))
            updated_fields.append(f'价格区间: {price_min}-{price_max}元')
            need_reprocess = True
        
        # 更新Buff价格筛选区间
        if buff_price_min is not None and buff_price_max is not None:
            Config.update_buff_price_range(float(buff_price_min), float(buff_price_max))
            updated_fields.append(f'Buff价格筛选: {buff_price_min}-{buff_price_max}元')
            need_reprocess = True
        
        # 更新Buff最小在售数量
        if buff_sell_num_min is not None:
            Config.update_buff_sell_num_min(int(buff_sell_num_min))
            updated_fields.append(f'Buff最小在售数量: {buff_sell_num_min}个')
            need_reprocess = True
        
        # 更新最大输出数量
        if max_output_items is not None:
            Config.MAX_OUTPUT_ITEMS = int(max_output_items)
            updated_fields.append(f'最大输出数量: {max_output_items}个')
        
        print(f"✅ 配置更新耗时: {time.time() - start:.3f}秒")
        
        # 生成响应
        print("\n📤 生成响应...")
        start = time.time()
        
        if updated_fields:
            response_data = {
                'success': True,
                'message': f'设置已更新: {", ".join(updated_fields)}'
            }
            
            if need_reprocess:
                response_data['message'] += " (重新筛选已暂时禁用)"
                print("⚠️ 重新处理已暂时禁用，仅用于测试API响应速度")
            
            result = json.dumps(response_data)
        else:
            result = json.dumps({
                'success': False,
                'error': '没有提供有效的更新参数'
            })
        
        print(f"✅ 响应生成耗时: {time.time() - start:.3f}秒")
        print(f"📤 响应内容: {result}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    total_start = time.time()
    simulate_api_settings_post()
    total_end = time.time()
    print(f"\n⏱️ 总耗时: {total_end - total_start:.3f}秒") 