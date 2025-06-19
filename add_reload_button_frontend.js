// 🔥 在前端token更新成功后调用此函数
async function reloadTokenConfig() {
    try {
        const response = await fetch('/api/tokens/reload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ Token配置已重新加载');
            alert('Token配置已更新！');
            // 可以在这里刷新token状态显示
            updateTokenStatus();
        } else {
            console.error('❌ 重载配置失败:', result.error);
            alert('重载配置失败: ' + result.error);
        }
    } catch (error) {
        console.error('❌ 重载配置异常:', error);
        alert('重载配置异常: ' + error.message);
    }
}

// 🔥 修改现有的token更新函数，在成功后自动重载
async function updateYoupinToken(tokenData) {
    try {
        // 1. 更新token配置
        const updateResponse = await fetch('/api/tokens/youpin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tokenData)
        });
        
        const updateResult = await updateResponse.json();
        
        if (updateResult.success) {
            console.log('✅ Token更新成功');
            
            // 2. 🔥 自动重新加载配置
            await reloadTokenConfig();
            
            return true;
        } else {
            console.error('❌ Token更新失败:', updateResult.error);
            return false;
        }
    } catch (error) {
        console.error('❌ Token更新异常:', error);
        return false;
    }
}

// 🔥 添加手动重载按钮的HTML示例
/*
<button onclick="reloadTokenConfig()" class="btn btn-warning">
    <i class="fas fa-sync-alt"></i> 重新加载配置
</button>
*/ 