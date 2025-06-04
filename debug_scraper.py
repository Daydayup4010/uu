#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Buff爬虫问题
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_buff_access():
    """测试Buff网站访问"""
    base_url = "https://buff.163.com"
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    try:
        print("🔍 测试Buff网站访问...")
        url = f"{base_url}/market/csgo"
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.content)} bytes")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        if response.status_code == 200:
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找页面标题
            title = soup.find('title')
            print(f"页面标题: {title.get_text() if title else '未找到'}")
            
            # 查找常见的饰品容器
            card_items = soup.find_all('div', class_='card-item')
            market_items = soup.find_all('div', class_='item')
            goods_items = soup.find_all('div', class_='goods-item')
            
            print(f"找到 .card-item: {len(card_items)} 个")
            print(f"找到 .item: {len(market_items)} 个")
            print(f"找到 .goods-item: {len(goods_items)} 个")
            
            # 如果没有找到预期的元素，显示页面结构
            if len(card_items) == 0 and len(market_items) == 0:
                print("\n📋 页面结构分析:")
                
                # 查找所有带class的div
                divs_with_class = soup.find_all('div', class_=True)[:10]
                for i, div in enumerate(divs_with_class, 1):
                    classes = ' '.join(div.get('class', []))
                    print(f"   {i}. <div class='{classes}'> (内容长度: {len(div.get_text())})")
            
            return True
        else:
            print(f"❌ 访问失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误，可能网络不通或网站限制访问")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def suggest_alternatives():
    """建议替代方案"""
    print("\n💡 建议的解决方案:")
    print("1. 使用演示数据模式（已实现）")
    print("2. 使用代理服务器")
    print("3. 使用Selenium浏览器自动化")
    print("4. 寻找公开的API接口")
    print("5. 使用本地缓存数据")

if __name__ == "__main__":
    print("🎯 Buff爬虫调试工具")
    print("="*40)
    
    success = test_buff_access()
    
    if not success:
        suggest_alternatives() 