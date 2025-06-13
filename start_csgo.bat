@echo off
chcp 65001
echo.
echo ============================================
echo 🚀 启动CS:GO饰品价差监控系统
echo ============================================
echo.

echo 📁 进入项目目录...
cd /d %~dp0

echo 🔧 检查Python环境...
python --version

echo 📦 检查依赖...
if not exist "logs" mkdir logs

echo 🌐 启动CS:GO饰品价差监控系统...
echo 🔗 访问地址: https://www.2333tv.top/csgo/
echo 🔗 本地测试: http://localhost:5000/csgo/
echo.
echo ⌨️  按 Ctrl+C 停止服务
echo ============================================
echo.

python start_csgo.py

pause 