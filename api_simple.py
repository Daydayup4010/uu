#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版API - Buff差价饰品监控系统

不启动复杂的监控服务，直接使用演示数据
"""

import logging
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import Config
from models import PriceDiffItem
from analyzer import PriceDiffAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Buff差价饰品监控系统",
    description="自动监控Buff和悠悠有品平台的饰品价差，发现套利机会",
    version="1.0.0"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

class ApiResponse(BaseModel):
    """API响应模型"""
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: str = datetime.now().isoformat()

# 全局数据存储
current_diff_items: List[PriceDiffItem] = []

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("启动Buff差价监控系统（简化版）...")
    
    # 加载演示数据
    try:
        analyzer = PriceDiffAnalyzer()
        global current_diff_items
        current_diff_items = analyzer.load_diff_data()
        logger.info(f"加载了 {len(current_diff_items)} 个差价饰品数据")
    except Exception as e:
        logger.warning(f"加载数据失败，将使用空数据: {e}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回主页面"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Buff差价监控系统</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>🎯 Buff差价饰品监控系统</h1>
            <p>系统正在初始化...</p>
            <p>请访问 <a href="/api/items">/api/items</a> 查看API数据</p>
        </body>
        </html>
        """)

@app.get("/api/items", response_model=ApiResponse)
async def get_diff_items(
    limit: Optional[int] = 100,
    min_diff: Optional[float] = None,
    sort_by: Optional[str] = "price_diff"
):
    """
    获取差价饰品列表
    
    - limit: 返回数量限制
    - min_diff: 最小价差过滤
    - sort_by: 排序方式 (price_diff, profit_margin)
    """
    try:
        global current_diff_items
        diff_items = current_diff_items.copy()
        
        # 应用过滤条件
        if min_diff is not None:
            diff_items = [item for item in diff_items if item.price_diff >= min_diff]
        
        # 排序
        if sort_by == "profit_margin":
            diff_items.sort(key=lambda x: x.profit_rate, reverse=True)
        else:
            diff_items.sort(key=lambda x: x.price_diff, reverse=True)
        
        # 限制数量
        diff_items = diff_items[:limit]
        
        # 转换为字典格式
        items_data = []
        for item in diff_items:
            items_data.append({
                "id": item.skin_item.id,
                "name": item.skin_item.name,
                "buff_price": item.skin_item.buff_price,
                "youpin_price": item.skin_item.youpin_price,
                "price_diff": item.price_diff,
                "profit_margin": item.profit_rate,
                "buff_buy_url": item.buff_buy_url,
                "image_url": item.skin_item.image_url,
                "category": getattr(item.skin_item, 'category', '未知')
            })
        
        return ApiResponse(
            success=True,
            message=f"成功获取 {len(items_data)} 个差价饰品",
            data={
                "items": items_data,
                "total_count": len(items_data)
            }
        )
        
    except Exception as e:
        logger.error(f"获取差价饰品失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status", response_model=ApiResponse)
async def get_monitor_status():
    """获取系统状态"""
    try:
        return ApiResponse(
            success=True,
            message="成功获取系统状态",
            data={
                'is_running': True,
                'last_update': datetime.now().isoformat(),
                'current_items_count': len(current_diff_items),
                'threshold': Config.PRICE_DIFF_THRESHOLD,
                'mode': 'demo'
            }
        )
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics", response_model=ApiResponse)
async def get_statistics():
    """获取统计信息"""
    try:
        analyzer = PriceDiffAnalyzer()
        stats = analyzer.get_statistics(current_diff_items)
        
        return ApiResponse(
            success=True,
            message="成功获取统计信息",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/refresh", response_model=ApiResponse)
async def refresh_data():
    """刷新数据"""
    try:
        analyzer = PriceDiffAnalyzer()
        global current_diff_items
        current_diff_items = analyzer.load_diff_data()
        
        return ApiResponse(
            success=True,
            message=f"数据已刷新，共 {len(current_diff_items)} 个差价饰品"
        )
        
    except Exception as e:
        logger.error(f"刷新数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config", response_model=ApiResponse)
async def get_config():
    """获取当前配置"""
    try:
        return ApiResponse(
            success=True,
            message="成功获取配置信息",
            data={
                "threshold": Config.PRICE_DIFF_THRESHOLD,
                "request_delay": getattr(Config, 'REQUEST_DELAY', 1),
                "max_retries": Config.MAX_RETRIES,
                "mode": "demo"
            }
        )
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/item/{item_id}", response_model=ApiResponse)
async def get_item_detail(item_id: str):
    """获取单个饰品详情"""
    try:
        # 查找指定饰品
        target_item = None
        for item in current_diff_items:
            if item.skin_item.id == item_id:
                target_item = item
                break
        
        if not target_item:
            raise HTTPException(status_code=404, detail="未找到指定饰品")
        
        item_data = {
            "id": target_item.skin_item.id,
            "name": target_item.skin_item.name,
            "buff_price": target_item.skin_item.buff_price,
            "youpin_price": target_item.skin_item.youpin_price,
            "price_diff": target_item.price_diff,
            "profit_margin": target_item.profit_rate,
            "buff_buy_url": target_item.buff_buy_url,
            "youpin_url": getattr(target_item.skin_item, 'youpin_url', ''),
            "image_url": target_item.skin_item.image_url,
            "category": getattr(target_item.skin_item, 'category', '未知'),
            "last_updated": datetime.now().isoformat()
        }
        
        return ApiResponse(
            success=True,
            message="成功获取饰品详情",
            data=item_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取饰品详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 