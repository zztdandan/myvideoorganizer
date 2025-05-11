/**
 * 视频文件组织系统 - 主要JavaScript文件
 */

// 在文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏提示框
    setupAlertAutoHide();
    
    // 注册侧边栏响应式切换功能
    setupSidebarToggle();
});

/**
 * 设置提示框自动隐藏
 */
function setupAlertAutoHide() {
    // 获取所有提示框
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    // 设置5秒后自动隐藏
    alerts.forEach(alert => {
        if (!alert.classList.contains('d-none')) {
            setTimeout(() => {
                alert.classList.add('fade-out');
                setTimeout(() => {
                    alert.classList.add('d-none');
                    alert.classList.remove('fade-out');
                }, 500);
            }, 5000);
        }
    });
}

/**
 * 设置侧边栏在移动设备上的切换功能
 */
function setupSidebarToggle() {
    // 检查是否是移动设备
    if (window.innerWidth < 768) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            // 添加切换按钮
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'btn btn-sm btn-dark d-md-none position-fixed top-0 start-0 mt-2 ms-2';
            toggleBtn.innerHTML = '<i class="bi bi-list"></i>';
            toggleBtn.onclick = function() {
                sidebar.classList.toggle('d-block');
            };
            document.body.appendChild(toggleBtn);
            
            // 点击外部自动收起
            document.addEventListener('click', function(event) {
                if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target) && sidebar.classList.contains('d-block')) {
                    sidebar.classList.remove('d-block');
                }
            });
        }
    }
}

/**
 * 格式化文件大小
 * @param {number} bytes 字节数
 * @returns {string} 格式化后的大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 显示加载中状态
 * @param {HTMLElement} element 要显示加载状态的元素
 * @param {string} message 加载提示信息
 */
function showLoading(element, message = '加载中...') {
    // 保存原始内容
    element.dataset.originalContent = element.innerHTML;
    
    // 设置加载提示
    element.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="loading me-2"></div>
            <span>${message}</span>
        </div>
    `;
    
    // 禁用元素
    if (element.tagName === 'BUTTON') {
        element.disabled = true;
    }
}

/**
 * 恢复加载前状态
 * @param {HTMLElement} element 恢复状态的元素
 */
function hideLoading(element) {
    // 恢复原始内容
    if (element.dataset.originalContent) {
        element.innerHTML = element.dataset.originalContent;
        delete element.dataset.originalContent;
    }
    
    // 启用元素
    if (element.tagName === 'BUTTON') {
        element.disabled = false;
    }
}

/**
 * 显示操作结果提示
 * @param {string} message 提示信息
 * @param {string} type 提示类型 (success/error)
 */
function showNotification(message, type = 'success') {
    // 创建提示元素
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed bottom-0 end-0 m-3`;
    alert.role = 'alert';
    alert.style.zIndex = '9999';
    
    alert.innerHTML = `
        ${type === 'success' ? '<i class="bi bi-check-circle-fill me-2"></i>' : '<i class="bi bi-exclamation-triangle-fill me-2"></i>'}
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // 添加到文档
    document.body.appendChild(alert);
    
    // 自动隐藏
    setTimeout(() => {
        alert.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(alert);
        }, 500);
    }, 5000);
}

/**
 * 记录调试日志
 * @param {string} component 组件名称
 * @param {string} message 日志消息
 * @param {any} data 日志数据
 */
function logDebug(component, message, data = null) {
    const timestamp = new Date().toISOString().substr(11, 8);
    console.group(`[${timestamp}] ${component}`);
    console.log(message);
    if (data !== null) {
        console.log(data);
    }
    console.groupEnd();
} 