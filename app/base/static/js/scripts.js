// app/base/static/js/scripts.js

// 添加事件监听器，当 DOM 加载完成时执行以下代码
document.addEventListener('DOMContentLoaded', function () {
    const containers = document.querySelectorAll('[data-enable-check-all], .enable-check-all');
    if (containers) {
        initializeCheckAll(containers);
    }
    
    const data_table = document.getElementById('data_table');
    const data_tbody = data_table.querySelector('tbody');
    if (data_table, data_tbody) {
        initializeRowClick(data_table, data_tbody);
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
function initializeCheckAll(containers) {
    // 获取所有包含 enable-check-all 的容器
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
function initializeRowClick(table, tbody) {
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
    var draggables = document.querySelectorAll('#tableConfigTHeadsList .draggable');
    var container = document.querySelector('#tableConfigTHeadsList');

    draggables.forEach(draggable => {
        draggable.addEventListener('mousedown', (e) => {
            e.preventDefault();
            const parentLi = draggable.parentElement; // 获取手柄的父元素 <li>
            parentLi.classList.add('dragging');
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });

        draggable.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const parentLi = draggable.parentElement; // 获取手柄的父元素 <li>
            parentLi.classList.add('dragging');
            const touch = e.touches[0];
            const rect = parentLi.getBoundingClientRect();
            const offsetX = touch.clientX - rect.left;
            const offsetY = touch.clientY - rect.top;
            parentLi.style.position = 'absolute';
            parentLi.style.zIndex = '1000';
            parentLi.dataset.offsetX = offsetX;
            parentLi.dataset.offsetY = offsetY;
            document.addEventListener('touchmove', onTouchMove);
            document.addEventListener('touchend', onTouchEnd);
        });

        function onMouseMove(e) {
            const parentLi = document.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
            const rect = parentLi.getBoundingClientRect();
            parentLi.style.left = `${e.clientX - rect.width / 2}px`;
            parentLi.style.top = `${e.clientY - rect.height / 2}px`;
            const afterElement = getDragAfterElement(container, e.clientY);
            console.log(container);
            console.log(parentLi);
            if (afterElement == null) {
                container.appendChild(parentLi);
            } else {
                container.insertBefore(parentLi, afterElement);
            }
        }

        function onMouseUp() {
            const parentLi = document.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
            parentLi.classList.remove('dragging');
            parentLi.style.position = '';
            parentLi.style.zIndex = '';
            parentLi.style.left = '';
            parentLi.style.top = '';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }

        function onTouchMove(e) {
            const parentLi = document.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
            const touch = e.touches[0];
            const offsetX = parseFloat(parentLi.dataset.offsetX);
            const offsetY = parseFloat(parentLi.dataset.offsetY);
            parentLi.style.left = `${touch.clientX - offsetX}px`;
            parentLi.style.top = `${touch.clientY - offsetY}px`;
            const afterElement = getDragAfterElement(container, touch.clientY);

            if (afterElement == null) {
                container.appendChild(parentLi);
            } else {
                container.insertBefore(parentLi, afterElement);
            }
        }

        function onTouchEnd() {
            const parentLi = document.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
            parentLi.classList.remove('dragging');
            parentLi.style.position = '';
            parentLi.style.zIndex = '';
            parentLi.style.left = '';
            parentLi.style.top = '';
            document.removeEventListener('touchmove', onTouchMove);
            document.removeEventListener('touchend', onTouchEnd);
        }
    });

    /*
    container.addEventListener('dragover', e => {
        e.preventDefault();
        const afterElement = getDragAfterElement(container, e.clientY);
        const draggable = document.querySelector('.dragging');
        console.log(draggable);
        console.log(afterElement);
        console.log(draggable.parentNode);
        if (draggable !== null) {
            afterElement === null ? container.appendChild(draggable.parentNode) : container.insertBefore(draggable.parentNode, afterElement);
        }
    });
*/
    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.draggableList:not(.dragging)')];

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