#!/usr/bin/env python3
"""修复子进程编码问题"""

def fix_subprocess_encoding():
    """修复api.py中的子进程编码问题"""
    
    # 读取api.py文件
    with open('api.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有子进程调用，添加编码设置
    old_pattern = '''        # 在子进程中运行验证
        result = subprocess.run([
            sys.executable, '-c', validation_code
        ], capture_output=True, text=True, timeout=60)'''
    
    new_pattern = '''        # 在子进程中运行验证，设置UTF-8编码避免emoji字符问题
        import os
        result = subprocess.run([
            sys.executable, '-c', validation_code
        ], capture_output=True, text=True, timeout=60,
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})'''
    
    # 执行替换
    new_content = content.replace(old_pattern, new_pattern)
    
    # 检查是否有替换
    if new_content != content:
        # 写回文件
        with open('api.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ 已修复api.py中的子进程编码问题")
        
        # 统计替换次数
        count = content.count(old_pattern)
        print(f"📊 共修复了 {count} 处子进程调用")
    else:
        print("⚠️ 未找到需要修复的子进程调用")

if __name__ == "__main__":
    fix_subprocess_encoding() 