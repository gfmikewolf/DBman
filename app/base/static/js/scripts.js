// app/base/static/js/scripts.js

/*** utils block ***/
function showModal(modal) {
    objModal = new bootstrap.Modal(modal)
    if (objModal) {
        objModal.show();
    }
}

function hideModal(modal) {
    objModal = new bootstrap.Modal(modal)
    if (objModal) {
        objModal.hide();
    }
}

function modalClose(event, modal, modalId) {
    event.preventDefault();
    if (document.activeElement && document.activeElement.closest('#'+ modalId)) {
        document.activeElement.blur();
    }
    hideModal(modal);
}
/*** utils block ends ***/

// 添加事件监听器，当 DOM 加载完成时执行以下代码
document.addEventListener('DOMContentLoaded', function () {
    // 全选
    
    
    const saveTableConfigButton = document.getElementById('saveTableConfig');
    const restoreDefaultButton = document.getElementById('restoreDefault');
    const downloadButton = document.getElementById('download_csv');
    const tooltipList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const search_query = document.getElementById('search_query');
    const search_btn = document.getElementById('search');
    const elementsToToggle = document.querySelectorAll('[data-toggleable]');
    
    const modifyForm = document.getElementById('ModifyForm');
    const deleteButtons = document.querySelectorAll('[data-delete-record-url]');
    const alertModal = document.getElementById('alertModal');
    const alertBody = document.getElementById('alertModalBody');
    const alertConfirm = document.getElementById('alertConfirm');
    const alertCancel = document.getElementById('alertCancel');
    const jsonviewButtons = document.querySelectorAll('[data-json-view]');
    const jsonModal = document.getElementById('jsonModal');
    const jsonModalBody = document.getElementById('jsonModalBody');
    const jsonModalCloseButtons = document.querySelectorAll('[data-json-modal-dismiss]');
    
    //初始化唯一数据表格的选行功能
    const dataTable = document.getElementById('dataTable');
    if (dataTable) {
        // 找全选框    
        const checkAll = dataTable.querySelector('[data-check-all]');
        // 找到容器内所有子复选框（check-item）
        const checkItems = dataTable.querySelectorAll('[data-check-item]');
        // 初始化全选按钮
        if (checkAll && checkItems.length > 0) {
            initializeCheckAll(checkAll, checkItems);
            // 初始化点击表格行可选中表行选项卡的功能
            const dataTbody = dataTable.querySelector('tbody');
            if (dataTbody) {
                initializeRowClick(dataTbody, checkItems);
            }
        }
    }

    // 初始化表格头、表格设置功能
    // dataTable在上面已经被定义
    const tableConfigModal = document.getElementById('tableConfigModal');
    const tableConfigButton = document.getElementById('tableConfigButton');
    if (tableConfigButton, tableConfigModal) {
        initializeTableConfig(tableConfigButton, tableConfigModal);
    }
    
    // 初始化下载 CSV 文件功能
    if (downloadButton) {
        initializeDownloadCSV(downloadButton);
    }
    
    // 初始化所有的工具提示
    if (tooltipList.length > 0) {
        initializeTooltips(tooltipList);
    }
    
    // 初始化搜索框功能
    if ( search_query && search_btn) {
        initializeSearch(search_query, search_btn);
    }
    
    // 初始化数据表格面板最大化功能
    const toggleMaximizeButton = document.getElementById('toggleMaximize');
    
    if (toggleMaximizeButton && elementsToToggle.length > 0) {
        initializeToggleMaximize(toggleMaximizeButton, elementsToToggle);
    }

    // 初始化修改和添加页面的提示框
    if (modifyForm) {
        initializeModifyForm(modifyForm);
    }

    // 初始化查看表格数据页面的删除记录提示框
    
    if(deleteButtons.length > 0 && alertModal && alertBody && alertConfirm && alertCancel) {
        if(deleteButtons.length > 0){
            initializeDeleteButtons(deleteButtons, alertModal, alertBody, alertConfirm, alertCancel);
        }
    }

    //初始化JSON显示的提示框
    if(jsonviewButtons.length > 0 && jsonModal && jsonModalBody && jsonModalCloseButtons.length > 0) {
        initializeJSONview(jsonviewButtons, jsonModal, jsonModalBody, jsonModalCloseButtons);
    }    
});

/*** 初始化组件 ***/
// initializeToggleMaximize() 初始化函数用于最大化或最小化数据表格面板
function initializeToggleMaximize(toggleMaximizeButton, elementsToToggle) {
    toggleMaximizeButton.addEventListener('click', function() {
        elementsToToggle.forEach(function(element) {
            element.classList.toggle('d-none');
        });
        toggleMaximizeButton.classList.toggle('active');
    });   
}

// initializeSearch() 函数用于对搜索框添加事件监听器，监听回车键，按回车键等同于点击搜索按钮
function initializeSearch(search_query, search_btn) {
    search_query.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            search_btn.click();
        };
    });
    search_btn.addEventListener('click', function() {
        //待完善全文搜索功能
    });
}

// initializeCheckAll() 函数用于初始化全选复选框功能
function initializeCheckAll(checkAll, checkItems) {
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
        });
    });
}

// initializeRowClick() 函数用于初始化表格行点击事件
function initializeRowClick(tbody, checkItems) {
    // 为表格的每一行添加点击事件监听器
    tbody.addEventListener('click', function (e) {
        const target = e.target.closest('tr'); // 找到最近的 <tr> 元素
        if (target) {
            const checkbox = target.querySelector('[data-check-item]'); // 找到该行的复选框
            if (checkbox) {
                checkbox.checked = !checkbox.checked; // 切换复选框的选中状态
                const event = new Event('change', { bubbles: true });
                checkbox.dispatchEvent(event);
            }
        }
    });
    // 为复选框添加点击事件监听器，阻止事件冒泡
    checkItems.forEach(element => {
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
        originalOrder.push(checkbox.parentElement);
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
            initialOrder.push(checkbox.parentElement);
        });
        myModal.show();
    });

    // Event listener for saving the table configuration
    saveTableConfigButton.addEventListener('click', function(event) {
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
        var theadRow = document.querySelector('#dataTable thead tr');
        var tbodyRows = document.querySelectorAll('#dataTable tbody tr');
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
            tableConfigTHeadsList.appendChild(element.parentElement);
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
                tableConfigTHeadsList.appendChild(element.parentElement);
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
            parentLi.classList.add('active');
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });

        draggable.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const parentLi = draggable.parentElement; // 获取手柄的父元素 <li>
            parentLi.classList.add('dragging');
            parentLi.classList.add('active');
            document.addEventListener('touchmove', onTouchMove);
            document.addEventListener('touchend', onTouchEnd);
        });

        function onMouseMove(e) {
            const parentLi = document.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
            // 记录鼠标按下时的相对位置
            afterElement = getDragAfterElement(container, e.clientY)
            if (afterElement == null) {
                container.appendChild(parentLi);
            } else {
                container.insertBefore(parentLi, afterElement);
            }
        }

        function onMouseUp() {
            const parentLi = document.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
            parentLi.classList.remove('dragging');
            parentLi.classList.remove('active');
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }

        function onTouchMove(e) {
            const parentLi = document.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
            const touch = e.touches[0];
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
            parentLi.classList.remove('active');
            document.removeEventListener('touchmove', onTouchMove);
            document.removeEventListener('touchend', onTouchEnd);
        }
    });

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

function initializeModifyForm(modifyForm) {
    var form = $(modifyForm);
    const cancelButton = document.getElementById('alertCancel');
    cancelButton.addEventListener('click', e => modalClose(e, cancelButton));
    form.on('submit', function(event) { // 直接绑定事件到 jQuery 对象
        event.preventDefault(); // 阻止默认提交行为
        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: function(response) {
                $('#alertModalBody').text(response.message);
                $('#alertModal').modal('show');
            },
            error: function(xhr, status, error) {
                $('#alertModalBody').text(error);
                $('#alertModal').modal('show');
            }
        });
    });
}

function initializeDeleteButtons(deleteButtons, alertModal, alertBody, alertConfirm, alertCancel) {
    deleteButtons.forEach(function(deleteButton) {
        deleteButton.addEventListener('click', function(e) {
            e.preventDefault();
            alertBody.textContent = alertBody.dataset.msgWarning;
            alertCancel.addEventListener('click', (event) => modalClose(event, alertModal));
            alertConfirm.addEventListener('click', function() {
                alertConfirm.style.visibility = 'hidden';
                alertCancel.textContent = alertConfirm.textContent;
                $.ajax({
                    type: 'post',
                    url: deleteButton.dataset.deleteRecordUrl,
                    success: function(response) {
                        alertBody.textContent = response.message;
                        alertCancel.addEventListener('click', function(event) {
                            modalClose(event, alertModal);
                            location.reload(true);
                        });
                        showModal(alertModal);
                    },
                    error: function(xhr, status, error) {
                        alertBody.textContent = error;
                        alertCancel.addEventListener('click', function(event) {
                            modalClose(event, alertModal);
                        });
                        showModal(alertModal);
                    }
                });    
            });
            showModal(alertModal);
        });
    });
}

function initializeJSONview(jsonviewButtons, alertModal, alertBody, alertConfirm, alertCancel) {
    jsonviewButtons.forEach(function(jsonviewButton){
        jsonviewButton.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('#alertModal [data-bs-dismiss="modal"]').forEach(function(button) {
                const cbtn = button.cloneNode(true);
                cbtn.addEventListener('click', (e) => modalClose(e, alertModal));
                button.parentNode.replaceChild(cbtn, button);
            });
            const jsonData = jsonviewButton.dataset.jsonView;
            alertBody.textContent = jsonData;
            alertCancel.style.visibility = 'hidden';
            const cbtn = alertConfirm.cloneNode(true);
            cbtn.addEventListener('click', function(e) {
                e.preventDefault();
                alertBody.textContent = '';
                alertCancel.style.visibility = '';
                modalClose(e, alertModal);
            });
            alertConfirm.parentNode.replaceChild(cbtn, alertConfirm);
            showModal(alertModal);
        });
    });

}
