#!/usr/bin/env python3
"""
移除前端刷新数据按钮的脚本
"""

def remove_refresh_button():
    """移除前端的刷新数据按钮"""
    
    # 读取HTML文件
    with open('static/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 移除刷新按钮HTML
    old_buttons = '''                <div class="flex items-center space-x-4">
                    <button id="refreshBtn" class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition duration-200">
                        <i class="fas fa-sync-alt mr-2"></i>
                        刷新数据
                    </button>
                    <button id="settingsBtn" class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition duration-200">
                        <i class="fas fa-cog mr-2"></i>
                        设置
                    </button>
                </div>'''
    
    new_buttons = '''                <div class="flex items-center space-x-4">
                    <button id="settingsBtn" class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition duration-200">
                        <i class="fas fa-cog mr-2"></i>
                        设置
                    </button>
                </div>'''
    
    content = content.replace(old_buttons, new_buttons)
    
    # 2. 移除刷新按钮的事件监听器
    old_listener = '''            // 绑定事件监听器
            initEventListeners() {
                // 刷新按钮
                const refreshBtn = document.getElementById('refreshBtn');
                if (refreshBtn) {
                    refreshBtn.addEventListener('click', () => this.forceUpdate());
                }
                
                // 设置按钮'''
    
    new_listener = '''            // 绑定事件监听器
            initEventListeners() {
                // 设置按钮'''
    
    content = content.replace(old_listener, new_listener)
    
    # 3. 移除forceUpdate方法
    # 查找方法开始和结束
    start_marker = "async forceUpdate() {"
    end_marker = "            }"
    
    start_pos = content.find(start_marker)
    if start_pos != -1:
        # 找到方法结束位置
        pos = start_pos
        brace_count = 0
        in_method = False
        
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
                in_method = True
            elif content[pos] == '}':
                brace_count -= 1
                if in_method and brace_count == 0:
                    # 找到方法结束
                    method_end = pos + 1
                    # 查找到下一行的开始
                    while method_end < len(content) and content[method_end] != '\n':
                        method_end += 1
                    method_end += 1  # 包含换行符
                    
                    # 删除整个方法
                    method_text = content[start_pos:method_end]
                    content = content.replace(method_text, "")
                    break
            pos += 1
    
    # 4. 更新无数据时的提示信息
    old_message = '''请点击右上角的"刷新数据"按钮开始分析'''
    new_message = '''系统会自动在后台进行增量分析，请稍等片刻'''
    
    content = content.replace(old_message, new_message)
    
    # 5. 移除注释中对刷新数据的引用
    content = content.replace('// 只有在非流式分析状态下才刷新数据', '// 只有在非流式分析状态下才更新显示')
    
    # 写回文件
    with open('static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 前端刷新数据按钮已成功移除")
    print("📝 修改内容:")
    print("  - 移除了顶部导航栏的刷新数据按钮")
    print("  - 移除了相关的JavaScript事件监听器")
    print("  - 移除了forceUpdate方法")
    print("  - 更新了无数据时的提示信息")

if __name__ == "__main__":
    remove_refresh_button() 