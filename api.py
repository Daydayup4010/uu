#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import time
import asyncio
import logging
import threading
import subprocess
import platform
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from flask import Flask, jsonify, request, render_template_string, Response

# 🔥 新增：使用增强的日志配置
try:
    from log_config import quick_setup
    logger = quick_setup('INFO')  # 设置日志输出到文件和控制台
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# 导入系统组件
from integrated_price_system import IntegratedPriceAnalyzer, PriceDiffItem, save_price_diff_data, load_price_diff_data
from update_manager import get_update_manager
from youpin_working_api import YoupinWorkingAPI
from integrated_price_system import BuffAPIClient
from token_manager import TokenManager, token_manager  # 🔥 导入全局实例
from config import Config

# 导入流式分析器和分析管理器
from streaming_analyzer import StreamingAnalyzer
from analysis_manager import get_analysis_manager

# 🔥 导入异步工具以抑制警告
import asyncio_utils

app = Flask(__name__)

def create_cross_platform_subprocess_env():
    """创建跨平台的子进程环境变量"""
    env = os.environ.copy()
    env.update({
        'PYTHONIOENCODING': 'utf-8',
        'LANG': 'en_US.UTF-8',
        'LC_ALL': 'en_US.UTF-8'
    })
    
    # Windows特定设置
    if platform.system() == 'Windows':
        env['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    
    return env

def create_encoding_setup_code():
    """创建跨平台编码设置代码"""
    return '''
import sys
import os
import locale
import platform
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 跨平台编码设置
def setup_encoding():
    """设置跨平台的UTF-8编码"""
    try:
        # 设置标准输入输出编码
        if hasattr(sys.stdout, 'reconfigure'):
            # Python 3.7+
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        else:
            # 兼容旧版本Python
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach(), errors='replace')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach(), errors='replace')
            if hasattr(sys.stdin, 'detach'):
                sys.stdin = codecs.getreader('utf-8')(sys.stdin.detach(), errors='replace')
        
        # 设置locale（按优先级尝试）
        locale_options = ['en_US.UTF-8', 'C.UTF-8', 'en_US.utf8', 'C.utf8']
        if platform.system() == 'Windows':
            locale_options = ['English_United States.utf8', 'C'] + locale_options
        
        for loc in locale_options:
            try:
                locale.setlocale(locale.LC_ALL, loc)
                break
            except locale.Error:
                continue
                
    except Exception as e:
        # 编码设置失败时记录但不中断执行
        print(f"Warning: Failed to setup encoding: {e}", file=sys.stderr)

# 执行编码设置
setup_encoding()
'''

def run_subprocess_with_encoding(validation_code, timeout=60):
    """使用跨平台编码设置运行子进程"""
    import sys
    import subprocess
    
    env = create_cross_platform_subprocess_env()
    encoding_setup = create_encoding_setup_code()
    
    # 组合编码设置和验证代码
    full_code = encoding_setup + '\n' + validation_code
    
    return subprocess.run([
        sys.executable, '-c', full_code
    ], capture_output=True, text=True, timeout=timeout, env=env,
    encoding='utf-8', errors='replace')

def _clear_hashname_cache():
    """清理hashname缓存并触发增量更新（优化版本）"""
    try:
        update_manager = get_update_manager()
        if hasattr(update_manager, 'hashname_cache'):
            update_manager.hashname_cache.hashnames.clear()
            update_manager.hashname_cache.last_update = None
            logger.info("🔄 已清理hashname缓存")
        else:
            logger.warning("⚠️ UpdateManager中未找到hashname_cache")
        
        # 🔥 优化：触发增量更新而不是全量更新，减少阻塞
        logger.info("🔄 启动增量更新重新构建缓存")
        update_manager.force_incremental_update()
        
    except Exception as e:
        logger.error(f"❌ 清理hashname缓存失败: {e}")

def _trigger_reprocess_from_saved_data(reason: str = "筛选条件更新"):
    """🔥 优先从保存数据重新筛选，避免重新调用API"""
    try:
        from saved_data_processor import get_saved_data_processor
        
        processor = get_saved_data_processor()
        
        # 检查是否有有效的全量数据文件
        if not processor.has_valid_full_data():
            logger.warning(f"⚠️ {reason}：没有找到有效的全量数据文件，回退到增量更新")
            # 🔥 优化：不调用force_full_update，改为增量更新
            update_manager = get_update_manager()
            update_manager.force_incremental_update()
            return
        
        # 从保存数据重新筛选
        logger.info(f"🔄 {reason}：从保存数据重新筛选...")
        diff_items, stats = processor.reprocess_with_current_filters()
        
        if diff_items is not None:
            # 更新UpdateManager的数据
            update_manager = get_update_manager()
            update_manager.current_diff_items = diff_items
            update_manager._save_current_data()
            
            logger.info(f"✅ {reason}：重新筛选完成，找到{len(diff_items)}个符合条件的商品")
            logger.info(f"📂 使用文件: {stats.get('buff_file', '未知')}, {stats.get('youpin_file', '未知')}")
        else:
            logger.warning(f"⚠️ {reason}：重新筛选失败，启动增量更新")
            # 🔥 优化：不调用force_full_update，改为增量更新
            update_manager = get_update_manager()
            update_manager.force_incremental_update()
            
    except Exception as e:
        logger.error(f"❌ {reason}：从保存数据重新筛选失败: {e}，启动增量更新")
        # 🔥 优化：不调用force_full_update，改为增量更新
        try:
            update_manager = get_update_manager()
            update_manager.force_incremental_update()
        except Exception as fallback_error:
            logger.error(f"❌ 增量更新启动也失败: {fallback_error}")

# 手动添加CORS支持
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def get_html_template():
    """读取HTML模板"""
    try:
        with open('static/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CS:GO价差分析系统</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>CS:GO价差分析系统</h1>
            <p>未找到模板文件 static/index.html</p>
        </body>
        </html>
        """

@app.route('/')
def index():
    """主页"""
    return render_template_string(get_html_template())

@app.route('/api/status')
def api_status():
    """获取系统状态"""
    try:
        update_manager = get_update_manager()
        status = update_manager.get_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data')
def api_data():
    """获取价差数据"""
    try:
        update_manager = get_update_manager()
        diff_items = update_manager.get_current_data()
        
        # 🔥 修改：更温和的处理方式，避免频繁触发全量更新
        if not diff_items:
            status = update_manager.get_status()
            # 只有在以下情况才触发全量更新：
            # 1. 有hashname缓存但没有数据
            # 2. 且初始全量更新未完成
            # 3. 且不是正在运行分析
            if (status.get('cached_hashnames_count', 0) > 0 and 
                not status.get('initial_full_update_completed', False) and
                not status.get('is_running', False)):
                
                logger.warning("🔄 检测到数据为空但有缓存，自动触发全量更新")
                update_manager.force_full_update()
                # 返回提示信息
                return jsonify({
                    'success': True,
                    'data': {
                        'items': [],
                        'total_count': 0,
                        'message': '检测到数据异常，已自动触发全量更新，请稍后刷新页面',
                        'auto_update_triggered': True,
                        'last_updated': None
                    }
                })
            else:
                # 返回空数据但不触发更新
                message = "数据收集中，请稍候" if status.get('is_running', False) else "暂无数据"
                return jsonify({
                    'success': True,
                    'data': {
                        'items': [],
                        'total_count': 0,
                        'message': message,
                        'auto_update_triggered': False,
                        'last_updated': status.get('last_full_update')
                    }
                })
        
        # 转换为字典格式
        items_data = []
        for item in diff_items:
            items_data.append({
                'id': item.id,
                'name': item.name,
                'buff_price': item.buff_price,
                'youpin_price': item.youpin_price,
                'price_diff': item.price_diff,
                'profit_rate': item.profit_rate,
                'buff_url': item.buff_url,
                'youpin_url': item.youpin_url,
                'image_url': item.image_url,
                'category': item.category,
                'last_updated': item.last_updated.isoformat() if item.last_updated else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'items': items_data,
                'total_count': len(items_data),
                'last_updated': update_manager.last_full_update.isoformat() if update_manager.last_full_update else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/items')
def api_items():
    """获取差价饰品列表（兼容性路由）"""
    try:
        update_manager = get_update_manager()
        diff_items = update_manager.get_current_data()
        
        # 转换为字典格式
        items_data = []
        for item in diff_items:
            items_data.append({
                'id': item.id,
                'name': item.name,
                'buff_price': item.buff_price,
                'youpin_price': item.youpin_price,
                'price_diff': item.price_diff,
                'profit_margin': item.profit_rate,  # 使用profit_margin以保持兼容性
                'buff_buy_url': item.buff_url,
                'image_url': item.image_url,
                'category': item.category,
                'youpin_url': item.youpin_url,
                'last_updated': item.last_updated.isoformat() if item.last_updated else None
            })
        
        return jsonify({
            'success': True,
            'message': f"成功获取 {len(items_data)} 个差价饰品",
            'data': {
                'items': items_data,
                'total_count': len(items_data)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/force_update', methods=['POST'])
def api_force_update():
    """强制更新数据"""
    try:
        update_manager = get_update_manager()
        update_manager.force_full_update()
        
        return jsonify({
            'success': True,
            'message': '全量更新任务已启动'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate_data', methods=['GET'])
def api_validate_data():
    """验证数据状态并自动修复"""
    try:
        update_manager = get_update_manager()
        diff_items = update_manager.get_current_data()
        status = update_manager.get_status()
        
        # 检查是否需要修复数据
        needs_repair = False
        repair_action = None
        
        if len(diff_items) == 0:
            if status.get('cached_hashnames_count', 0) > 0:
                # 有缓存但无数据，需要强制全量更新
                needs_repair = True
                repair_action = 'force_full_update'
                logger.warning("🔧 检测到数据异常：有hashname缓存但无价差数据，将执行强制全量更新")
                update_manager.force_full_update()
            elif not status.get('initial_full_update_completed', False):
                # 未完成初始全量更新
                needs_repair = True
                repair_action = 'wait_initial_update'
                logger.info("⏳ 系统正在执行初始全量更新，请稍候")
        
        return jsonify({
            'success': True,
            'data': {
                'has_data': len(diff_items) > 0,
                'items_count': len(diff_items),
                'is_running': status['is_running'],
                'initial_full_update_completed': status.get('initial_full_update_completed', False),
                'last_full_update': status.get('last_full_update'),
                'cached_hashnames_count': status.get('cached_hashnames_count', 0),
                'needs_repair': needs_repair,
                'repair_action': repair_action,
                'status_message': _get_status_message(diff_items, status, needs_repair, repair_action)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_status_message(diff_items, status, needs_repair, repair_action):
    """获取状态消息"""
    if len(diff_items) > 0:
        return f"数据正常，共有{len(diff_items)}个价差商品"
    elif repair_action == 'force_full_update':
        return "检测到数据异常，已自动触发全量更新，请2-3分钟后刷新页面"
    elif repair_action == 'wait_initial_update':
        return "系统正在执行初始数据收集，请等待2-3分钟后刷新页面"
    elif not status.get('is_running', False):
        return "更新管理器未运行，请检查系统状态"
    else:
        return "数据收集中，请稍候"

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """获取/更新设置"""
    if request.method == 'GET':
        try:
            return jsonify({
                'success': True,
                'data': {
                    'threshold': Config.PRICE_DIFF_THRESHOLD,
                    'price_range': {
                        'min': Config.PRICE_DIFF_MIN,
                        'max': Config.PRICE_DIFF_MAX
                    },
                    'buff_price_range': {
                        'min': Config.BUFF_PRICE_MIN,
                        'max': Config.BUFF_PRICE_MAX
                    },
                    'buff_sell_num': {
                        'min': Config.get_buff_sell_num_min()
                    },
                    'max_output_items': Config.MAX_OUTPUT_ITEMS,
                    'update_intervals': {
                        'full_update_hours': Config.FULL_UPDATE_INTERVAL_HOURS,
                        'incremental_update_minutes': Config.INCREMENTAL_UPDATE_INTERVAL_MINUTES
                    }
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            threshold = data.get('threshold')
            price_min = data.get('price_min')
            price_max = data.get('price_max')
            buff_price_min = data.get('buff_price_min')
            buff_price_max = data.get('buff_price_max')
            buff_sell_num_min = data.get('buff_sell_num_min')
            max_output_items = data.get('max_output_items')
            
            updated_fields = []
            
            # 更新价差阈值（兼容性）
            if threshold is not None:
                Config.PRICE_DIFF_THRESHOLD = float(threshold)
                updated_fields.append(f'价差阈值: {threshold}元')
            
            # 🔥 优化：跟踪是否需要重新处理数据
            need_reprocess = False
            
            # 更新价格区间
            if price_min is not None and price_max is not None:
                Config.update_price_range(float(price_min), float(price_max))
                updated_fields.append(f'价格区间: {price_min}-{price_max}元')
                need_reprocess = True
            
            # 更新Buff价格筛选区间
            if buff_price_min is not None and buff_price_max is not None:
                Config.update_buff_price_range(float(buff_price_min), float(buff_price_max))
                updated_fields.append(f'Buff价格筛选: {buff_price_min}-{buff_price_max}元')
                need_reprocess = True
            
            # 更新Buff最小在售数量
            if buff_sell_num_min is not None:
                Config.update_buff_sell_num_min(int(buff_sell_num_min))
                updated_fields.append(f'Buff最小在售数量: {buff_sell_num_min}个')
                need_reprocess = True
            
            # 更新最大输出数量
            if max_output_items is not None:
                Config.MAX_OUTPUT_ITEMS = int(max_output_items)
                updated_fields.append(f'最大输出数量: {max_output_items}个')
            
            if updated_fields:
                # 🔥 极速响应：先返回成功，后台处理数据
                response_data = {
                    'success': True,
                    'message': f'设置已更新: {", ".join(updated_fields)}'
                }
                
                # 🔥 后台异步重新处理，不阻塞响应
                if need_reprocess:
                    response_data['message'] += " (数据将在后台重新筛选)"
                    
                    def async_reprocess():
                        """完全异步的重新处理"""
                        try:
                            import time
                            # 等待响应发送完毕
                            time.sleep(0.2)
                            
                            logger.info("🔄 [后台] 开始数据重新筛选...")
                            _trigger_reprocess_from_saved_data("筛选条件批量更新")
                            logger.info("✅ [后台] 数据重新筛选完成")
                        except Exception as e:
                            logger.error(f"❌ [后台] 数据重新筛选失败: {e}")
                    
                    # 启动异步处理
                    threading.Thread(target=async_reprocess, daemon=True).start()
                
                # 🔥 立即返回响应，不等待任何处理
                return jsonify(response_data)
            else:
                return jsonify({
                    'success': False,
                    'error': '没有提供有效的更新参数'
                }), 400
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/api/price_range', methods=['GET', 'POST'])
def api_price_range():
    """价格区间管理API"""
    if request.method == 'GET':
        try:
            return jsonify({
                'success': True,
                'data': {
                    'min': Config.PRICE_DIFF_MIN,
                    'max': Config.PRICE_DIFF_MAX,
                    'current_range': f'{Config.PRICE_DIFF_MIN}-{Config.PRICE_DIFF_MAX}元'
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            min_diff = data.get('min')
            max_diff = data.get('max')
            
            if min_diff is None or max_diff is None:
                return jsonify({
                    'success': False,
                    'error': '需要提供min和max参数'
                }), 400
            
            min_diff = float(min_diff)
            max_diff = float(max_diff)
            
            if min_diff >= max_diff:
                return jsonify({
                    'success': False,
                    'error': '最小价差必须小于最大价差'
                }), 400
            
            if min_diff < 0:
                return jsonify({
                    'success': False,
                    'error': '价差不能为负数'
                }), 400
            
            # 更新价格区间
            Config.update_price_range(min_diff, max_diff)
            
            return jsonify({
                'success': True,
                'message': f'价格差异区间已更新为 {min_diff}-{max_diff}元',
                'data': {
                    'min': Config.PRICE_DIFF_MIN,
                    'max': Config.PRICE_DIFF_MAX
                }
            })
            
        except ValueError:
            return jsonify({
                'success': False,
                'error': '价格参数必须是有效数字'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/api/buff_price_range', methods=['GET', 'POST'])
def api_buff_price_range():
    """Buff价格筛选区间管理API"""
    if request.method == 'GET':
        try:
            return jsonify({
                'success': True,
                'data': {
                    'min': Config.BUFF_PRICE_MIN,
                    'max': Config.BUFF_PRICE_MAX,
                    'current_range': f'{Config.BUFF_PRICE_MIN}-{Config.BUFF_PRICE_MAX}元'
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            min_price = data.get('min')
            max_price = data.get('max')
            
            if min_price is None or max_price is None:
                return jsonify({
                    'success': False,
                    'error': '需要提供min和max参数'
                }), 400
            
            min_price = float(min_price)
            max_price = float(max_price)
            
            if min_price >= max_price:
                return jsonify({
                    'success': False,
                    'error': '最小价格必须小于最大价格'
                }), 400
            
            if min_price < 0:
                return jsonify({
                    'success': False,
                    'error': '价格不能为负数'
                }), 400
            
            # 更新Buff价格筛选区间
            Config.update_buff_price_range(min_price, max_price)
            
            return jsonify({
                'success': True,
                'message': f'Buff价格筛选区间已更新为 {min_price}-{max_price}元',
                'data': {
                    'min': Config.BUFF_PRICE_MIN,
                    'max': Config.BUFF_PRICE_MAX
                }
            })
            
        except ValueError:
            return jsonify({
                'success': False,
                'error': '价格参数必须是有效数字'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/api/buff_sell_num', methods=['GET', 'POST'])
def api_buff_sell_num():
    """Buff在售数量筛选API"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': {
                'min_sell_num': Config.get_buff_sell_num_min()
            }
        })
    
    # POST方法：更新在售数量筛选
    try:
        data = request.get_json() or {}
        min_sell_num = data.get('min_sell_num')
        
        if min_sell_num is None:
            return jsonify({
                'success': False,
                'error': '需要提供min_sell_num参数'
            }), 400
        
        min_sell_num = int(min_sell_num)
        
        if min_sell_num < 0:
            return jsonify({
                'success': False,
                'error': '在售数量不能为负数'
            }), 400
        
        # 更新Buff在售数量筛选
        Config.update_buff_sell_num_min(min_sell_num)
        
        # 🔥 关键：更新配置后清理hashname缓存
        _clear_hashname_cache()
        
        return jsonify({
            'success': True,
            'message': f'Buff最小在售数量已更新为 {min_sell_num}个',
            'data': {
                'min_sell_num': Config.get_buff_sell_num_min()
            }
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': '在售数量参数必须是有效整数'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/force_incremental_update', methods=['POST'])
def api_force_incremental_update():
    """强制增量更新"""
    try:
        update_manager = get_update_manager()
        update_manager.force_incremental_update()
        
        return jsonify({
            'success': True,
            'message': '增量更新任务已启动'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/enhanced_incremental_update', methods=['POST'])
def api_enhanced_incremental_update():
    """🔥 新增：增强增量更新（支持价格更新和完成标识）"""
    try:
        from enhanced_update_manager import get_enhanced_updater
        
        updater = get_enhanced_updater()
        
        # 检查是否已在运行
        status = updater.get_status()
        if status['is_running']:
            return jsonify({
                'success': False,
                'message': '增量更新正在进行中，请稍后再试',
                'data': status
            }), 409
        
        # 在后台执行增强增量更新
        def run_update():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(updater.run_enhanced_incremental_update())
                loop.close()
                logger.info(f"增强增量更新完成: {result['message']}")
            except Exception as e:
                logger.error(f"增强增量更新异常: {e}")
        
        # 启动后台线程
        import threading
        thread = threading.Thread(target=run_update, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '🚀 增强增量更新已启动，可通过状态接口查看进度',
            'data': {
                'status': 'started',
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"启动增强增量更新失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/incremental_update_status', methods=['GET'])
def api_get_incremental_update_status():
    """🔥 新增：获取增量更新状态"""
    try:
        from enhanced_update_manager import get_enhanced_updater
        
        updater = get_enhanced_updater()
        status = updater.get_status()
        
        return jsonify({
            'success': True,
            'message': '状态获取成功',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"获取增量更新状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear_cache', methods=['POST'])
def api_clear_cache():
    """清理hashname缓存"""
    try:
        update_manager = get_update_manager()
        if hasattr(update_manager, 'hashname_cache'):
            update_manager.hashname_cache.hashnames.clear()
            update_manager.hashname_cache.last_update = None
            logger.info("🔄 手动清理hashname缓存完成")
            
            return jsonify({
                'success': True,
                'message': 'hashname缓存已清理，下次分析将重新构建'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'UpdateManager中未找到hashname_cache'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """触发价差分析 - 集成全局并发控制"""
    try:
        data = request.get_json() or {}
        max_items = data.get('max_items', 50)
        
        # 获取全局分析管理器
        manager = get_analysis_manager()
        analysis_id = f"traditional_{int(datetime.now().timestamp())}"
        
        # 检查是否已有分析在运行
        if not manager.start_analysis('traditional', analysis_id):
            return jsonify({
                'success': False,
                'error': f'已有分析在运行，请稍后再试。当前运行: {manager.current_analysis_type}',
                'current_analysis': manager.current_analysis_type
            }), 409
        
        try:
            # 使用集成分析器进行异步分析
            async def run_analysis():
                async with IntegratedPriceAnalyzer() as analyzer:
                    return await analyzer.analyze_price_differences(max_items=max_items)
            
            # 在新的事件循环中运行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                diff_items = loop.run_until_complete(run_analysis())
            finally:
                loop.close()
            
            if diff_items:
                # 保存结果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/manual_analysis_{timestamp}.json"
                save_price_diff_data(diff_items, filename)
                
                # 转换为API响应格式
                items_data = []
                for item in diff_items:
                    items_data.append({
                        'id': item.id,
                        'name': item.name,
                        'buff_price': item.buff_price,
                        'youpin_price': item.youpin_price,
                        'price_diff': item.price_diff,
                        'profit_rate': item.profit_rate,
                        'buff_url': item.buff_url,
                        'youpin_url': item.youpin_url,
                        'image_url': item.image_url,
                        'category': item.category
                    })
                
                # 更新管理器缓存
                manager.finish_analysis(analysis_id, diff_items)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'items': items_data,
                        'total_count': len(items_data),
                        'filename': filename
                    },
                    'message': f'分析完成，发现 {len(diff_items)} 个价差商品'
                })
            else:
                manager.finish_analysis(analysis_id, [])
                return jsonify({
                    'success': True,
                    'data': {
                        'items': [],
                        'total_count': 0
                    },
                    'message': '未发现有价差的商品'
                })
        
        except Exception as e:
            # 分析失败，清理管理器状态
            manager.finish_analysis(analysis_id)
            raise e
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Token管理相关API端点
@app.route('/api/tokens/status', methods=['GET'])
def get_tokens_status():
    """获取Token状态"""
    try:
        token_manager = TokenManager()
        
        # 获取基本状态
        basic_status = token_manager.get_status()
        
        # 获取详细状态摘要（包含验证缓存）
        detailed_status = token_manager.get_token_status_summary()
        
        # 🔥 修复：确保数据格式与前端期望一致
        def format_token_status(basic, detailed):
            """格式化Token状态数据"""
            return {
                # 基本配置信息
                'configured': detailed.get('configured', False),
                'last_updated': detailed.get('last_updated'),
                'status': detailed.get('status', '未配置'),
                
                # 验证缓存信息（前端期望的字段）
                'last_validation': detailed.get('last_validation'),
                'cached_valid': detailed.get('cached_valid'),
                'cached_error': detailed.get('cached_error'),
                
                # 兼容性字段
                'has_cookies': basic.get('has_cookies', False),
                'has_csrf': basic.get('has_csrf', False),
                'has_device_id': basic.get('has_device_id', False),
                'has_uk': basic.get('has_uk', False)
            }
        
        # 合并并格式化状态信息
        combined_status = {
            'buff': format_token_status(basic_status['buff'], detailed_status['buff']),
            'youpin': format_token_status(basic_status['youpin'], detailed_status['youpin'])
        }
        
        logger.info(f"📊 Token状态查询: Buff配置={combined_status['buff']['configured']}, "
                   f"Buff有效={combined_status['buff']['cached_valid']}, "
                   f"悠悠有品配置={combined_status['youpin']['configured']}, "
                   f"悠悠有品有效={combined_status['youpin']['cached_valid']}")
        
        return jsonify({
            'success': True,
            'data': combined_status
        })
    except Exception as e:
        logger.error(f"❌ 获取Token状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tokens/buff', methods=['GET', 'POST'])
def manage_buff_token():
    """管理Buff Token"""
    token_manager = TokenManager()
    
    if request.method == 'GET':
        try:
            config = token_manager.load_buff_config()
            # 隐藏敏感信息
            safe_config = {k: ('***' if 'token' in k.lower() or 'cookie' in k.lower() else v) 
                          for k, v in config.items()}
            return jsonify({
                'success': True,
                'data': safe_config
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            # 🔥 修复：使用正确的方法名
            cookies = data.get('cookies', {})
            headers = data.get('headers', {})
            success = token_manager.update_buff_tokens(cookies, headers)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Buff配置已保存'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '保存Buff配置失败'
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/api/tokens/youpin', methods=['GET', 'POST'])
def manage_youpin_token():
    """管理悠悠有品Token"""
    token_manager = TokenManager()
    
    if request.method == 'GET':
        try:
            # 🔥 修复：使用正确的方法名
            config = token_manager.get_youpin_config()
            # 隐藏敏感信息
            safe_config = {k: ('***' if any(x in k.lower() for x in ['token', 'cookie', 'authorization', 'uk', 'device']) else v) 
                          for k, v in config.items()}
            return jsonify({
                'success': True,
                'data': safe_config
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            # 🔥 修复：使用正确的方法名
            device_info = {
                'device_id': data.get('device_id', ''),
                'device_uk': data.get('device_uk', ''),
                'uk': data.get('uk', ''),
                'b3': data.get('b3', ''),
                'authorization': data.get('authorization', '')
            }
            headers = data.get('headers', {})
            success = token_manager.update_youpin_tokens(device_info, headers)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '悠悠有品配置已保存'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '保存悠悠有品配置失败'
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/api/test/buff', methods=['POST'])
def test_buff_connection():
    """测试Buff连接"""
    try:
        # 在独立线程中运行异步测试
        import threading
        from concurrent.futures import ThreadPoolExecutor
        
        def run_async_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def test():
                    async with BuffAPIClient() as client:
                        goods = await client.get_all_goods()
                        return len(goods) if goods else 0
                return loop.run_until_complete(test())
            except Exception as e:
                raise e
            finally:
                loop.close()
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_test)
            result = future.result(timeout=30)  # 30秒超时
        
        return jsonify({
            'success': True,
            'message': f'Buff连接成功，获取到 {result} 个商品',
            'data': {'item_count': result}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Buff连接测试失败: {str(e)}'
        }), 500

@app.route('/api/test/youpin', methods=['POST'])
def test_youpin_connection():
    """测试悠悠有品连接"""
    try:
        # 在独立线程中运行异步测试
        import threading
        from concurrent.futures import ThreadPoolExecutor
        
        def run_async_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def test():
                    async with YoupinWorkingAPI() as client:
                        items = await client.get_all_items()
                        return len(items) if items else 0
                return loop.run_until_complete(test())
            except Exception as e:
                raise e
            finally:
                loop.close()
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_test)
            result = future.result(timeout=30)  # 30秒超时
        
        return jsonify({
            'success': True,
            'message': f'悠悠有品连接成功，获取到 {result} 个商品',
            'data': {'item_count': result}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'悠悠有品连接测试失败: {str(e)}'
        }), 500

@app.route('/api/tokens/validate', methods=['POST'])
def validate_tokens():
    """验证所有Token状态（优化版本）"""
    try:
        # 获取请求参数
        request_data = request.get_json() or {}
        force_check = request_data.get('force_check', False)
        
        logger.info(f"🔍 开始Token验证，强制检查: {force_check}")
        start_time = time.time()
        
        # 🔥 修复：使用全局token_manager实例
        tm = token_manager
        
        # 检查缓存（除非强制检查）
        if not force_check and tm.is_cache_valid():
            cached_result = tm.get_cached_validation_result()
            if cached_result:
                elapsed = time.time() - start_time
                logger.info(f"🚀 使用缓存的Token验证结果，耗时: {elapsed:.2f}秒")
                return jsonify({
                    'success': True,
                    'data': cached_result,
                    'cached': True,
                    'validation_time': round(elapsed, 2)
                })
        
        # 执行验证
        logger.info("🔄 开始执行Token验证...")
        
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(tm.validate_all_tokens(force_check))
                elapsed = time.time() - start_time
                result['validation_time'] = round(elapsed, 2)
                
                logger.info(f"✅ Token验证完成，耗时: {elapsed:.2f}秒")
                
                return jsonify({
                    'success': True,
                    'data': result,
                    'cached': False
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Token验证失败，耗时: {elapsed:.2f}秒，错误: {e}")
            
            return jsonify({
                'success': False,
                'error': f'Token验证失败: {str(e)}',
                'validation_time': round(elapsed, 2)
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Token验证API异常: {e}")
        return jsonify({
            'success': False,
            'error': f'验证失败: {str(e)}'
        }), 500

@app.route('/api/tokens/validate/buff', methods=['POST'])
def validate_buff_token():
    """验证Buff Token状态"""
    try:
        import subprocess
        import sys
        import json
        
        # 在主线程中获取请求数据，避免上下文问题
        request_data = request.get_json() or {}
        force_check = request_data.get('force_check', False)
        
        # 使用子进程隔离执行Token验证
        validation_code = f'''
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

def validate_buff_token_isolated(force_check={force_check}):
    """完全隔离的Buff Token验证"""
    
    def run_in_clean_env():
        async def validate():
            import importlib
            
            # 导入TokenManager
            token_manager_module = importlib.import_module('token_manager')
            TokenManager = token_manager_module.TokenManager
            
            # 创建新实例
            tm = TokenManager()
            
            # 验证Buff Token
            return await tm.validate_buff_token(force_check=force_check)
        
        # 在新的事件循环中运行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(validate())
        finally:
            loop.close()
    
    # 在线程池中运行
    with ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_clean_env)
        return future.result(timeout=30)

# 执行验证
try:
    result = validate_buff_token_isolated()
    print(json.dumps({{"success": True, "data": result}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
'''
        
        # 使用跨平台编码处理运行子进程验证

        result = run_subprocess_with_encoding(validation_code)
        
        if result.returncode == 0:
            try:
                # 🔥 修复：只提取最后一行的JSON数据，忽略日志输出
                output_lines = result.stdout.strip().split('\n')
                json_line = None
                
                # 从后往前找第一个有效的JSON行
                for line in reversed(output_lines):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            json.loads(line)  # 验证是否为有效JSON
                            json_line = line
                            break
                        except json.JSONDecodeError:
                            continue
                
                if json_line:
                    data = json.loads(json_line)
                    if data.get('success'):
                        return jsonify({
                            'success': True,
                            'data': data['data']
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': data.get('error', '验证失败')
                        }), 500
                else:
                    return jsonify({
                        'success': False,
                        'error': f'未找到有效的JSON响应: {result.stdout}'
                    }), 500
                    
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': f'验证结果解析失败: {result.stdout}'
                }), 500
        else:
            error_msg = result.stderr if result.stderr else '子进程执行失败'
            return jsonify({
                'success': False,
                'error': f'Buff Token验证失败: {error_msg}'
            }), 500
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Buff Token验证超时'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Buff Token验证失败: {str(e)}'
        }), 500

@app.route('/api/tokens/validate/youpin', methods=['POST'])
def validate_youpin_token():
    """验证悠悠有品Token状态"""
    try:
        import subprocess
        import sys
        import json
        
        # 在主线程中获取请求数据，避免上下文问题
        request_data = request.get_json() or {}
        force_check = request_data.get('force_check', False)
        
        # 使用子进程隔离执行Token验证
        validation_code = f'''
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

def validate_youpin_token_isolated(force_check={force_check}):
    """完全隔离的悠悠有品Token验证"""
    
    def run_in_clean_env():
        async def validate():
            import importlib
            
            # 导入TokenManager
            token_manager_module = importlib.import_module('token_manager')
            TokenManager = token_manager_module.TokenManager
            
            # 创建新实例
            tm = TokenManager()
            
            # 验证悠悠有品Token
            return await tm.validate_youpin_token(force_check=force_check)
        
        # 在新的事件循环中运行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(validate())
        finally:
            loop.close()
    
    # 在线程池中运行
    with ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_clean_env)
        return future.result(timeout=30)

# 执行验证
try:
    result = validate_youpin_token_isolated()
    print(json.dumps({{"success": True, "data": result}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
'''
        
        # 使用跨平台编码处理运行子进程验证

        result = run_subprocess_with_encoding(validation_code)
        
        if result.returncode == 0:
            try:
                # 🔥 修复：只提取最后一行的JSON数据，忽略日志输出
                output_lines = result.stdout.strip().split('\n')
                json_line = None
                
                # 从后往前找第一个有效的JSON行
                for line in reversed(output_lines):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            json.loads(line)  # 验证是否为有效JSON
                            json_line = line
                            break
                        except json.JSONDecodeError:
                            continue
                
                if json_line:
                    data = json.loads(json_line)
                    if data.get('success'):
                        return jsonify({
                            'success': True,
                            'data': data['data']
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': data.get('error', '验证失败')
                        }), 500
                else:
                    return jsonify({
                        'success': False,
                        'error': f'未找到有效的JSON响应: {result.stdout}'
                    }), 500
                    
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': f'验证结果解析失败: {result.stdout}'
                }), 500
        else:
            error_msg = result.stderr if result.stderr else '子进程执行失败'
            return jsonify({
                'success': False,
                'error': f'悠悠有品Token验证失败: {error_msg}'
            }), 500
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': '悠悠有品Token验证超时'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'悠悠有品Token验证失败: {str(e)}'
        }), 500

@app.route('/api/tokens/alerts', methods=['GET'])
def get_token_alerts():
    """获取Token警报"""
    try:
        # 延迟导入，避免Flask上下文问题
        import importlib
        token_validation_module = importlib.import_module('token_validation_service')
        token_validation_service = token_validation_module.token_validation_service
        token_alert_handler = token_validation_module.token_alert_handler
        
        active_alerts = token_validation_service.get_active_alerts()
        notifications = token_alert_handler.get_notifications()
        stats = token_validation_service.get_stats()
        
        alerts_data = []
        for i, alert in enumerate(active_alerts):
            alerts_data.append({
                'id': i,
                'platform': alert.platform,
                'alert_type': alert.alert_type,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'resolved': alert.resolved
            })
        
        return jsonify({
            'success': True,
            'data': {
                'active_alerts': alerts_data,
                'notifications': notifications,
                'stats': stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取Token警报失败: {str(e)}'
        }), 500

@app.route('/api/tokens/alerts/clear', methods=['POST'])
def clear_token_notifications():
    """清除Token通知"""
    try:
        # 延迟导入，避免Flask上下文问题
        import importlib
        token_validation_module = importlib.import_module('token_validation_service')
        token_alert_handler = token_validation_module.token_alert_handler
        
        token_alert_handler.clear_notifications()
        
        return jsonify({
            'success': True,
            'message': '通知已清除'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'清除通知失败: {str(e)}'
        }), 500

@app.route('/api/tokens/validation-service', methods=['GET', 'POST'])
def manage_validation_service():
    """管理Token验证服务"""
    try:
        # 延迟导入，避免Flask上下文问题
        import importlib
        token_validation_module = importlib.import_module('token_validation_service')
        token_validation_service = token_validation_module.token_validation_service
        
        if request.method == 'GET':
            # 获取服务状态
            stats = token_validation_service.get_stats()
            return jsonify({
                'success': True,
                'data': stats
            })
        
        elif request.method == 'POST':
            # 控制服务启动/停止
            data = request.get_json() or {}
            action = data.get('action', 'status')
            
            if action == 'start':
                token_validation_service.start()
                return jsonify({
                    'success': True,
                    'message': 'Token验证服务已启动'
                })
            elif action == 'stop':
                token_validation_service.stop()
                return jsonify({
                    'success': True,
                    'message': 'Token验证服务已停止'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '不支持的操作'
                }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'管理验证服务失败: {str(e)}'
        }), 500

@app.route('/api/stream_analyze', methods=['POST'])
def api_stream_analyze():
    """
    流式价差分析 - 支持Server-Sent Events
    边获取边分析，实时推送结果
    """
    try:
        data = request.get_json() or {}
        max_items = data.get('max_items', None)  # 不限制项目数量，全量分析
        
        def generate_stream():
            """生成SSE数据流"""
            # 在新线程中运行异步分析
            def run_analysis():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    results = []
                    
                    async def collect_results():
                        analyzer = StreamingAnalyzer()
                        async for update in analyzer.start_streaming_analysis():
                            results.append(update)
                    
                    loop.run_until_complete(collect_results())
                    return results
                finally:
                    loop.close()
            
            # 启动分析任务
            try:
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(run_analysis)
                    
                    # 等待结果并流式返回
                    for update in future.result():
                        # 格式化为SSE数据
                        yield f"data: {json.dumps(update, ensure_ascii=False)}\n\n"
                        
            except Exception as e:
                error_data = {
                    'type': 'error',
                    'error': str(e),
                    'message': '分析过程出现错误'
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze_incremental', methods=['POST'])
def api_analyze_incremental():
    """
    增量分析API - 立即返回缓存数据，后台更新全量数据
    集成全局并发控制
    """
    try:
        data = request.get_json() or {}
        force_refresh = data.get('force_refresh', False)
        
        # 获取全局分析管理器
        manager = get_analysis_manager()
        
        # 首先返回缓存数据
        cached_results = manager.get_cached_results()
        
        response_data = {
            'success': True,
            'data': {
                'items': cached_results,
                'total_count': len(cached_results),
                'cached': True,
                'last_updated': datetime.now().isoformat()
            },
            'message': f'返回缓存数据: {len(cached_results)}个商品'
        }
        
        # 检查是否需要启动后台更新
        if force_refresh or not cached_results:
            analysis_id = f"incremental_{int(datetime.now().timestamp())}"
            
            # 尝试启动后台分析（非阻塞）
            if manager.start_analysis('incremental', analysis_id):
                # 启动后台分析任务（不等待完成）
                def background_analysis():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        async def run_background():
                            analyzer = StreamingAnalyzer()
                            async for update in analyzer.start_streaming_analysis():
                                # 后台静默更新
                                if update.get('type') == 'completed':
                                    logger.info(f"后台增量分析完成: {update.get('total_found', 0)}个商品")
                                    break
                        
                        loop.run_until_complete(run_background())
                    except Exception as e:
                        logger.error(f"后台增量分析出错: {e}")
                        manager.finish_analysis(analysis_id)
                    finally:
                        loop.close()
                
                # 启动后台线程
                background_thread = threading.Thread(target=background_analysis)
                background_thread.daemon = True
                background_thread.start()
                
                response_data['background_update'] = True
                response_data['message'] += '，后台更新已启动'
            else:
                # 已有分析在运行
                response_data['background_update'] = False
                response_data['message'] += f'，已有分析在运行({manager.current_analysis_type})'
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/demo')
def streaming_demo():
    """流式分析演示页面"""
    try:
        with open('static/stream_demo.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>演示页面不存在</h1>
        <p>请确保 static/stream_demo.html 文件存在</p>
        """

@app.route('/api/reprocess_from_saved', methods=['POST'])
def api_reprocess_from_saved():
    """🔥 新增：从已保存数据重新筛选API"""
    try:
        from saved_data_processor import get_saved_data_processor
        
        processor = get_saved_data_processor()
        
        # 检查是否有有效的全量数据文件
        if not processor.has_valid_full_data():
            return jsonify({
                'success': False,
                'error': '没有找到有效的全量数据文件，请先执行全量更新'
            }), 404
        
        # 重新筛选
        diff_items, stats = processor.reprocess_with_current_filters()
        
        if diff_items is not None:
            # 更新UpdateManager的数据
            update_manager = get_update_manager()
            update_manager.current_diff_items = diff_items
            update_manager._save_current_data()
            
            return jsonify({
                'success': True,
                'message': f'重新筛选完成，找到 {len(diff_items)} 个符合条件的商品',
                'data': {
                    'items_count': len(diff_items),
                    'buff_file': stats.get('buff_file'),
                    'youpin_file': stats.get('youpin_file'),
                    'statistics': stats,
                    'filters_applied': stats.get('filters_applied', {})
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': '重新筛选失败'
            }), 500
            
    except Exception as e:
        logger.error(f"从保存数据重新筛选失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # 🔥 启动更新管理器 - 只启动一次
    from update_manager import get_update_manager
    
    update_manager = None
    token_service = None
    try:
        # 启动Token验证服务
        print("🔐 启动Token验证服务...")
        from token_validation_service import token_validation_service
        token_service = token_validation_service
        token_service.start()
        
        print("📊 启动数据更新管理器...")
        update_manager = get_update_manager()
        update_manager.start()
        
        print("🚀 启动Web应用...")
        print("💻 访问地址: http://localhost:5000")
        print("🔐 Token失效检查: 每5分钟自动验证")
        print("按 Ctrl+C 停止服务")
        
        # 禁用自动重启避免重复启动UpdateManager
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n📴 收到停止信号...")
    finally:
        if update_manager:
            print("🛑 停止更新管理器...")
            update_manager.stop()
        if token_service:
            print("🛑 停止Token验证服务...")
            token_service.stop()
        print("✅ 服务已停止") 