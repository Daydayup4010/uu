#!/usr/bin/env python3
"""追踪Flask上下文访问的调试脚本"""
import sys
import traceback
import threading
from datetime import datetime

# 拦截Flask request访问
original_import = __import__

def trace_import(name, globals=None, locals=None, fromlist=(), level=0):
    """追踪模块导入"""
    if 'flask' in name:
        print(f"🔍 导入Flask模块: {name}")
        print(f"📍 调用堆栈:")
        for line in traceback.format_stack()[:-1]:
            print(f"   {line.strip()}")
        print()
    
    return original_import(name, globals, locals, fromlist, level)

def trace_flask_request_access():
    """追踪Flask request对象的访问"""
    print("🔍 开始追踪Flask上下文访问")
    print("=" * 60)
    
    # 拦截import
    import builtins
    builtins.__import__ = trace_import
    
    try:
        # 导入Flask并创建一个钩子
        import flask
        
        # 保存原始的request对象
        original_request_class = flask.Request
        
        class TrackedRequest(original_request_class):
            def __getattribute__(self, name):
                if name not in ['__class__', '__dict__']:
                    print(f"🚨 访问request.{name}")
                    print(f"🧵 线程: {threading.current_thread().name}")
                    print(f"📍 调用堆栈:")
                    for line in traceback.format_stack()[:-1]:
                        print(f"   {line.strip()}")
                    print()
                return super().__getattribute__(name)
        
        flask.Request = TrackedRequest
        
        # 测试TokenManager导入
        print("📦 测试TokenManager导入...")
        from token_manager import TokenManager
        print("✅ TokenManager导入成功")
        
        # 测试TokenManager实例化
        print("🏗️ 测试TokenManager实例化...")
        tm = TokenManager()
        print("✅ TokenManager实例化成功")
        
        # 测试异步方法
        print("🔄 测试异步方法调用...")
        import asyncio
        
        async def test_async():
            try:
                result = await tm.validate_youpin_token(force_check=True)
                print(f"✅ 异步调用成功: {result}")
                return True
            except Exception as e:
                print(f"❌ 异步调用失败: {e}")
                print("完整错误堆栈:")
                traceback.print_exc()
                return False
        
        # 在新的事件循环中运行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(test_async())
            if success:
                print("✅ 所有测试通过")
            else:
                print("❌ 测试失败")
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ 追踪过程异常: {e}")
        traceback.print_exc()
    finally:
        # 恢复原始import
        import builtins
        builtins.__import__ = original_import
    
    print("=" * 60)
    print("🏁 追踪完成")

def test_in_thread():
    """在线程中测试"""
    print(f"🧵 线程测试开始 - {threading.current_thread().name}")
    
    try:
        from concurrent.futures import ThreadPoolExecutor
        
        def isolated_test():
            print(f"🔬 隔离测试 - 线程: {threading.current_thread().name}")
            
            # 尝试重新加载模块
            import sys
            import importlib
            
            # 清理可能的Flask模块
            flask_modules = [name for name in sys.modules.keys() if 'flask' in name.lower()]
            print(f"📋 已加载的Flask模块: {flask_modules}")
            
            try:
                # 重新导入token_manager
                if 'token_manager' in sys.modules:
                    importlib.reload(sys.modules['token_manager'])
                
                from token_manager import TokenManager
                tm = TokenManager()
                
                # 测试异步调用
                import asyncio
                
                async def validate():
                    return await tm.validate_youpin_token(force_check=True)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(validate())
                    print(f"✅ 隔离测试成功: {result}")
                    return True
                finally:
                    loop.close()
                    
            except Exception as e:
                print(f"❌ 隔离测试失败: {e}")
                print("错误堆栈:")
                traceback.print_exc()
                return False
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(isolated_test)
            result = future.result(timeout=30)
            
            if result:
                print("✅ 线程测试成功")
            else:
                print("❌ 线程测试失败")
                
    except Exception as e:
        print(f"❌ 线程测试异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print(f"🚀 开始追踪分析 - {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # 1. 基本追踪
    trace_flask_request_access()
    
    print()
    print("=" * 60)
    print()
    
    # 2. 线程测试
    test_in_thread()
    
    print()
    print("🎯 分析完成") 