#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复api.py中的缓存清理问题
手动添加缓存清理逻辑到配置更新接口
"""

def clear_hashname_cache():
    """清理hashname缓存"""
    try:
        from update_manager import get_update_manager
        import logging
        logger = logging.getLogger(__name__)
        
        update_manager = get_update_manager()
        if hasattr(update_manager, 'hashname_cache'):
            update_manager.hashname_cache.hashnames.clear()
            update_manager.hashname_cache.last_update = None
            logger.info("🔄 已清理hashname缓存，将在下次分析时重新构建")
            return True
        else:
            logger.warning("⚠️ UpdateManager中未找到hashname_cache")
            return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ 清理hashname缓存失败: {e}")
        return False

# 需要在api.py中的以下位置添加缓存清理调用：

# 1. /api/settings POST方法中，在Config.update_price_range()之后
# 2. /api/settings POST方法中，在Config.update_buff_price_range()之后  
# 3. /api/price_range POST方法中，在Config.update_price_range()之后
# 4. /api/buff_price_range POST方法中，在Config.update_buff_price_range()之后

print("""
🔧 需要手动修复的位置：

1. 在api.py开头添加缓存清理函数：
   
def _clear_hashname_cache():
    try:
        update_manager = get_update_manager()
        if hasattr(update_manager, 'hashname_cache'):
            update_manager.hashname_cache.hashnames.clear()
            update_manager.hashname_cache.last_update = None
            logger.info("🔄 已清理hashname缓存")
    except Exception as e:
        logger.warning(f"清理hashname缓存失败: {e}")

2. 在/api/settings POST方法中添加：
   
   # 更新价格区间后
   if price_min is not None and price_max is not None:
       Config.update_price_range(float(price_min), float(price_max))
       updated_fields.append(f'价格区间: {price_min}-{price_max}元')
       _clear_hashname_cache()  # 🔥 添加这行
   
   # 更新Buff价格区间后  
   if buff_price_min is not None and buff_price_max is not None:
       Config.update_buff_price_range(float(buff_price_min), float(buff_price_max))
       updated_fields.append(f'Buff价格筛选: {buff_price_min}-{buff_price_max}元')
       _clear_hashname_cache()  # 🔥 添加这行

3. 在/api/price_range POST方法中添加：
   
   Config.update_price_range(min_diff, max_diff)
   _clear_hashname_cache()  # 🔥 添加这行

4. 在/api/buff_price_range POST方法中添加：
   
   Config.update_buff_price_range(min_price, max_price)  
   _clear_hashname_cache()  # 🔥 添加这行

这样修复后，每次更新筛选条件时都会清理缓存，确保新的筛选条件立即生效！
""")

if __name__ == "__main__":
    # 测试缓存清理函数
    result = clear_hashname_cache()
    if result:
        print("✅ 缓存清理测试成功")
    else:
        print("❌ 缓存清理测试失败") 