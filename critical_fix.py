#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紧急修复脚本 - 停止重复的分析任务
"""

import sys
import os
import asyncio
import time

# 添加项目路径
sys.path.append('.')

from analysis_manager import get_analysis_manager
from update_manager import get_update_manager

def force_stop_all_analysis():
    """强制停止所有分析"""
    print("🛑 紧急修复：强制停止所有分析...")
    
    # 强制停止分析管理器
    analysis_manager = get_analysis_manager()
    analysis_manager.force_stop_all()
    
    # 强制停止更新管理器
    update_manager = get_update_manager()
    update_manager.stop()
    
    print("✅ 所有分析已停止")
    
    # 等待一下
    time.sleep(3)
    
    # 重新启动更新管理器
    print("🚀 重新启动更新管理器...")
    update_manager.start()
    
    print("✅ 修复完成！")

def check_status():
    """检查当前状态"""
    print("📊 检查当前状态...")
    
    analysis_manager = get_analysis_manager()
    status = analysis_manager.get_status()
    
    print(f"分析状态: {status}")
    
    update_manager = get_update_manager()
    update_status = update_manager.get_status()
    
    print(f"更新状态: {update_status}")

if __name__ == "__main__":
    print("🚨 重复分析修复工具")
    print("="*50)
    
    check_status()
    print()
    force_stop_all_analysis()
    print()
    check_status() 