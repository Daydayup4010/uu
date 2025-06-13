"""
异步工具模块 - 用于解决事件循环生命周期管理问题
"""
import asyncio
import logging
import warnings
from typing import Optional

logger = logging.getLogger(__name__)

def suppress_asyncio_warnings():
    """抑制异步相关的警告信息"""
    # 抑制特定的RuntimeError警告
    warnings.filterwarnings("ignore", message=".*Event loop is closed.*", category=RuntimeWarning)
    warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*", category=RuntimeWarning)

async def safe_close_session(session):
    """安全关闭aiohttp session"""
    if session and not session.closed:
        try:
            await session.close()
            # 等待连接器完全关闭
            if hasattr(session, 'connector') and session.connector:
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.debug(f"关闭session时出错: {e}")

def safe_close_loop(loop: Optional[asyncio.AbstractEventLoop] = None):
    """安全关闭事件循环"""
    if loop is None:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return
    
    if loop.is_closed():
        return
    
    try:
        # 取消所有挂起的任务
        pending = asyncio.all_tasks(loop)
        if pending:
            logger.debug(f"取消 {len(pending)} 个挂起的任务...")
            for task in pending:
                task.cancel()
            
            # 等待任务完成或被取消
            try:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                logger.debug(f"等待任务完成时出错: {e}")
    
    except Exception as e:
        logger.debug(f"清理任务时出错: {e}")
    
    finally:
        try:
            loop.close()
        except Exception as e:
            logger.debug(f"关闭事件循环时出错: {e}")

class SafeEventLoop:
    """安全的事件循环上下文管理器"""
    
    def __init__(self):
        self.loop = None
        
    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        return self.loop
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        safe_close_loop(self.loop)

# 初始化时抑制警告
suppress_asyncio_warnings() 