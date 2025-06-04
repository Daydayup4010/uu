@echo off
chcp 65001 >nul
echo 🎯 Buff差价饰品监控系统 - Windows启动脚本
echo ==================================================

REM 检查Python是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ 检测到Python环境

REM 运行Python启动脚本
python start.py

pause 