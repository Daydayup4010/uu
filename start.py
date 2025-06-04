#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键启动脚本 - Buff差价饰品监控系统

该脚本提供最简单的启动方式：
1. 检查环境
2. 安装依赖
3. 生成演示数据
4. 启动系统
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误：需要Python 3.8或更高版本")
        print(f"当前版本：{sys.version}")
        return False
    else:
        print(f"✅ Python版本检查通过：{sys.version.split()[0]}")
        return True

def install_dependencies():
    """安装依赖包"""
    print("\n📦 正在安装依赖包...")
    try:
        # 升级pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 安装依赖
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败：{e}")
        return False

def check_files():
    """检查必要文件"""
    required_files = [
        "main.py",
        "run_demo.py", 
        "requirements.txt",
        "config.py",
        "models.py"
    ]
    
    print("\n📋 检查系统文件...")
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - 缺失")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ 缺少必要文件：{', '.join(missing_files)}")
        return False
    return True

def start_system():
    """启动系统"""
    print("\n🚀 启动Buff差价饰品监控系统...")
    print("="*50)
    
    try:
        # 运行演示模式
        subprocess.run([sys.executable, "run_demo.py"])
    except KeyboardInterrupt:
        print("\n\n👋 系统已停止")
    except Exception as e:
        print(f"\n❌ 启动失败：{e}")

def main():
    """主函数"""
    print("🎯 Buff差价饰品监控系统 - 一键启动")
    print("="*50)
    
    # 1. 检查Python版本
    if not check_python_version():
        input("\n按回车键退出...")
        return
    
    # 2. 检查系统文件
    if not check_files():
        input("\n按回车键退出...")
        return
    
    # 3. 安装依赖
    if not install_dependencies():
        print("\n可以尝试手动安装：pip install -r requirements.txt")
        input("\n按回车键退出...")
        return
    
    # 4. 启动系统
    start_system()

if __name__ == "__main__":
    main() 