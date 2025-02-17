// app/base/static/js/scripts.js

// 添加事件监听器，当 DOM 加载完成时执行以下代码
document.addEventListener('DOMContentLoaded', function () {
    
    if (document.querySelector('[data-enable-check-all], .enable-check-all')) {
        initializeCheckAll();
    }
    
    if (document.getElementById('data_table')) {
        initializeRowClick();
    }
    
    // 初始化表格头、表格设置功能
    const tableConfigModal = document.getElementById('tableConfigModal');
    const tableConfigButton = document.getElementById('table_config');
    const saveTableConfigButton = document.getElementById('saveTableConfig');
    const restoreDefaultButton = document.getElementById('restoreDefault');
    if (tableConfigModal && tableConfigButton && saveTableConfigButton && restoreDefaultButton) {
        initializeTableConfig(tableConfigButton, tableConfigModal, saveTableConfigButton, restoreDefaultButton);
    }
    
    // 初始化下载 CSV 文件功能
    const downloadButton = document.getElementById('download_csv');
    if (downloadButton) {
        initializeDownloadCSV(downloadButton);
    }
    
    // 初始化所有的工具提示
    const tooltipList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipList.length > 0) {
        initializeTooltips(tooltipList);
    }
    
    // 初始化搜索框功能
    const search_query = document.getElementById('search_query');
    const search_btn = document.getElementById('search');
    if ( search_query && search_btn) {
        initializeSearch(search_query, search_btn);
    }
    
    // 初始化数据表格面板最大化或最小化功能
    const elementsToToggle = document.querySelectorAll('[data-toggleable]');
    const toggleMaximizeButton = document.getElementById('toggle_maximize');
    if (toggleMaximizeButton && elementsToToggle.length > 0) {
        initializeToggleMaximize(toggleMaximizeButton, elementsToToggle);
    }
});

// initializeToggleMaximize() 初始化函数用于最大化或最小化数据表格面板
function initializeToggleMaximize(toggleMaximizeButton, elementsToToggle) {
    toggleMaximizeButton.addEventListener('click', function() {
        elementsToToggle.forEach(function(element) {
            element.classList.toggle('d-none');
        });
        document.querySelector('#data-table-panel').classList.toggle('maximized');
        document.getElementById('toggle_maximize').classList.toggle('active');
    });   
}

// initializeSearch() 函数用于对搜索框添加事件监听器，监听回车键，按回车键等同于点击搜索按钮
function initializeSearch(search_query, search_btn) {
    search_query.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            search_btn.click();
        }
    });
}

// initializeCheckAll() 函数用于初始化全选复选框功能
function initializeCheckAll() {
    // 获取所有包含 enable-check-all 的容器
    const containers = document.querySelectorAll('[data-enable-check-all], .enable-check-all');
    containers.forEach(container => {
        // 找到容器内的总开关（check-all）
        const checkAll = container.querySelector('[data-check-all], .check-all');

        // 找到容器内所有子复选框（check-item）
        const checkItems = container.querySelectorAll('[data-check-item], .check-item');

        // 如果找到总开关和子复选框，则绑定事件
        if (checkAll && checkItems.length > 0) {
            // 当总开关的状态改变时，更新所有子复选框的状态
            checkAll.addEventListener('change', function () {
                checkItems.forEach(item => {
                    item.checked = checkAll.checked;
                });
            });

            // 当子复选框的状态改变时，更新总开关的状态
            checkItems.forEach(item => {
                item.addEventListener('change', function (e) {
                    const allChecked = Array.from(checkItems).every(item => item.checked);
                    checkAll.checked = allChecked;
                    e.stopPropagation(); // 阻止事件冒泡
                });
            });
        }
    });
}

// initializeRowClick() 函数用于初始化表格行点击事件
function initializeRowClick() {
    const table = document.getElementById('data_table');
    const tbody = table.querySelector('tbody');
    // 为表格的每一行添加点击事件监听器
    tbody.addEventListener('click', function (e) {
        const target = e.target.closest('tr'); // 找到最近的 <tr> 元素
        if (target) {
            const checkbox = target.querySelector('input[type="checkbox"]'); // 找到该行的复选框
            if (checkbox) {
                checkbox.checked = !checkbox.checked; // 切换复选框的选中状态
                const event = new Event('change', { bubbles: true });
                checkbox.dispatchEvent(event);
            }
        }
    });

    // 为复选框添加点击事件监听器，阻止事件冒泡
    tbody.querySelectorAll('input[type="checkbox"], button, a').forEach(element => {
        element.addEventListener('click', function (e) {
            e.stopPropagation(); // 阻止事件冒泡
        });
    });
}

// initializeTableConfig() 函数用于初始化表格头、表格设置功能
function initializeTableConfig(tableConfigButton, tableConfigModal, saveTableConfigButton, restoreDefaultButton) {
    // 存储原始复选框状态和顺序
    var originalCheckboxState = [];
    var originalOrder = [];

    // 保存原始复选框状态和顺序
    document.querySelectorAll('#tableConfigTHeadsList .form-check-input').forEach(function(checkbox) {
        originalOrder.push(checkbox.parentNode);
        originalCheckboxState.push({ id: checkbox.id, checked: checkbox.checked });
    });

    // 存储点击前的复选框状态和顺序
    var initialCheckboxState = [];
    var initialOrder = [];

    // 创建模态框实例
    var myModal = new bootstrap.Modal(tableConfigModal, {
        keyboard: false
    });

    // 表格设置按钮点击事件监听器
    tableConfigButton.addEventListener('click', function() {
        // Save the initial state of the checkboxes and their order
        initialCheckboxState = [];
        initialOrder = [];
        document.querySelectorAll('#tableConfigTHeadsBody .form-check-input').forEach(function(checkbox) {
            initialCheckboxState.push({ id: checkbox.id, checked: checkbox.checked });
            initialOrder.push(checkbox.parentNode);
        });
        myModal.show();
    });

    // Event listener for saving the table configuration
    saveTableConfigButton.addEventListener('click', function() {
        var checkboxes = document.querySelectorAll('#tableConfigTHeadsBody .form-check-input');
        var newOrder = [];
        checkboxes.forEach(function(checkbox) {
            var columnId = checkbox.id.replace('column_', '');
            newOrder.push(columnId);
            var column = document.querySelector('th[data-column-id="' + columnId + '"]');
            var cells = document.querySelectorAll('td[data-column-id="' + columnId + '"]');
            if (checkbox.checked) {
                column.style.display = '';
                cells.forEach(function(cell) {
                    cell.style.display = '';
                });
            } else {
                column.style.display = 'none';
                cells.forEach(function(cell) {
                    cell.style.display = 'none';
                });
            }
        });

        // Reorder columns based on newOrder
        var theadRow = document.querySelector('#data_table thead tr');
        var tbodyRows = document.querySelectorAll('#data_table tbody tr');
        newOrder.forEach(function(columnId) {
            var column = document.querySelector('th[data-column-id="' + columnId + '"]');
            theadRow.appendChild(column);
            tbodyRows.forEach(function(row) {
                var cell = row.querySelector('td[data-column-id="' + columnId + '"]');
                row.appendChild(cell);
            });
        });

        // Blur the currently focused element before hiding the modal
        if (document.activeElement && document.activeElement.closest('#tableConfigModal')) {
            document.activeElement.blur();
        }
        myModal.hide();
    });

    // Event listener for restoring the default order
    restoreDefaultButton.addEventListener('click', function() {
        originalCheckboxState.forEach(function(state) {
            var checkbox = document.getElementById(state.id);
            if (checkbox) {
                checkbox.checked = state.checked;
            }
        });
        var tableConfigTHeadsList = document.getElementById('tableConfigTHeadsList');
        tableConfigTHeadsList.innerHTML = '';
        originalOrder.forEach(function(element) {
            tableConfigTHeadsList.appendChild(element);
        });
    });

    // Ensure the close button works correctly
    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(function(button) {
        button.addEventListener('click', function() {
            // Restore the initial state of the checkboxes and their order
            initialCheckboxState.forEach(function(state) {
                var checkbox = document.getElementById(state.id);
                if (checkbox) {
                    checkbox.checked = state.checked;
                }
            });
            var tableConfigTHeadsList = document.getElementById('tableConfigTHeadsList');
            tableConfigTHeadsList.innerHTML = '';
            initialOrder.forEach(function(element) {
                tableConfigTHeadsList.appendChild(element);
            });

            // Blur the currently focused element before hiding the modal
            if (document.activeElement && document.activeElement.closest('#tableConfigModal')) {
                document.activeElement.blur();
            }
            myModal.hide();
        });
    });

    // Drag and drop functionality for reordering columns
    const draggables = document.querySelectorAll('#tableConfigTHeadsList .draggable');
    const container = document.querySelector('#tableConfigTHeadsList');

    draggables.forEach(draggable => {
        draggable.addEventListener('dragstart', () => {
            draggable.classList.add('dragging');
        });

        draggable.addEventListener('dragend', () => {
            draggable.classList.remove('dragging');
        });

        // Add touch event listeners for mobile support
        draggable.addEventListener('touchstart', (e) => {
            draggable.classList.add('dragging'); // 添加拖拽中的样式
            const touch = e.touches[0]; // 获取第一个触摸点
            const rect = draggable.getBoundingClientRect(); // 获取拖拽元素的边界矩形
            draggable.style.position = 'absolute'; // 设置拖拽元素的定位方式为绝对定位
            draggable.style.zIndex = '1000'; // 确保拖拽元素在最上层
            draggable.style.left = `${touch.clientX - rect.width / 2}px`; // 设置拖拽元素的水平位置，使其中心在触摸点
            draggable.style.top = `${touch.clientY - rect.height / 2}px`; // 设置拖拽元素的垂直位置，使其中心在触摸点
            document.body.appendChild(draggable); // 将拖拽元素附加到 body 以避免裁剪
        });

        draggable.addEventListener('touchmove', (e) => {
            const touch = e.touches[0]; // 获取第一个触摸点
            draggable.style.left = `${touch.clientX - draggable.offsetWidth / 2}px`; // 更新拖拽元素的水平位置，使其中心在触摸点
            draggable.style.top = `${touch.clientY - draggable.offsetHeight / 2}px`; // 更新拖拽元素的垂直位置，使其中心在触摸点
            const afterElement = getDragAfterElement(container, touch.clientY); // 获取拖拽元素应该插入的位置
            if (afterElement == null) {
                container.appendChild(draggable); // 如果没有找到插入位置，则将拖拽元素附加到容器末尾
            } else {
                container.insertBefore(draggable, afterElement); // 否则，将拖拽元素插入到正确的位置
            }
        });

        draggable.addEventListener('touchend', () => {
            draggable.classList.remove('dragging'); // 移除拖拽中的样式
            draggable.style.position = ''; // 重置拖拽元素的定位方式
            draggable.style.zIndex = ''; // 重置 z-index
            draggable.style.left = ''; // 重置水平位置
            draggable.style.top = ''; // 重置垂直位置
            container.appendChild(draggable); // 将拖拽元素重新附加到容器中以保持顺序
        });
    });

    container.addEventListener('dragover', e => {
        e.preventDefault();
        const afterElement = getDragAfterElement(container, e.clientY);
        const draggable = document.querySelector('.dragging');
        if (afterElement == null) {
            container.appendChild(draggable);
        } else {
            container.insertBefore(draggable, afterElement);
        }
    });

    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.draggable:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
}

// initializeDownloadCSV() 函数用于初始化下载 CSV 文件功能
function initializeDownloadCSV(downloadButton) {
    downloadButton.addEventListener('click', function() {
        var checkboxes = document.querySelectorAll('#tableConfigForm .form-check-input');
        var selectedColumns = [];
        checkboxes.forEach(function(checkbox) {
            if (checkbox.checked) {
                var columnId = checkbox.id.replace('column_', '');
                selectedColumns.push(columnId);
            }
        });

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/download_csv', true);
        xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
        xhr.responseType = 'blob';
        xhr.onload = function() {
            if (xhr.status === 200) {
                var blob = new Blob([xhr.response], { type: 'text/csv' });
                var link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.download = 'data.csv';
                link.click();
            }
        };
        xhr.send(JSON.stringify({ columns: selectedColumns }));
    });
}

// initializeTooltips() 函数用于初始化所有的工具提示
function initializeTooltips(tooltipList) {
    var tooltipTriggerList = [].slice.call(tooltipList);
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}