// app/base/static/js/scripts.js
// Version: 1.0
// Date: 2025-09-01
// Description: This file contains the main JavaScript code for the project DBMan
// Author: Xiaolong Liu

import { ModalDBMan } from './dbman-modal.js';
// import { ModalAlert } from './modal.js';
import { ModalDatatableConfig } from './dbman-modal.js';
 
/*** 全局变量 block ***/
const msgTypes = ['success', 'error', 'warning-delete']; // 提示模态框的文字类型
var curSearchQuery = ''; // 存放当前搜索栏的内容
/*** 全局变量 block ends */

// 将json字符串转换为html表格
function tabulate(jsonData) {
    const jsonTable = document.createElement('table');
    jsonTable.className = 'table';
    const tbody = jsonTable.createTBody();
    const jsonObj = JSON.parse(jsonData);
    for (let key in jsonObj) {
        const value = jsonObj[key];
        const row = tbody.insertRow();
        const cellKey = row.insertCell();
        const cellValue = row.insertCell();
        cellKey.textContent = key;
        cellValue.textContent = value;
    }
    return jsonTable.outerHTML;
}
// 刷新当前页面
function reloadWindow() { 
    location.reload(true); 
}
// 显示提示模态框的文字（隐藏未选中的文字）
function setAlertMsg(alertModal, msgType, msg) {
    if(msgTypes.includes(msgType)) {
        msgTypes.forEach(function(mt) {
            const typeText = alertModal.querySelector('[data-' + mt + ']');
            if (mt == msgType) {
                typeText.classList.remove('d-none'); 
                const msgDiv = alertModal.querySelector('[data-msg]');
                msgDiv.innerHTML = msg;
            } else {
                typeText.classList.add('d-none');
            }
        });
    }
}
/*** utils block ends ***/

/*** 页面事件监听器 block begins: 当 DOM 加载完成时执行以下代码 ***/
document.addEventListener('DOMContentLoaded', function () {
    // 初始化所有的工具提示
    const tooltipList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipList.length > 0) {
        initializeTooltips(tooltipList);
    }

    const dataTable = document.getElementById('datatable-table-main');
    if (dataTable) {
        // 找全选框    
        const checkAll = dataTable.querySelector('[data-check-all]');
        // 找到容器内所有子复选框（check-item）
        const checkItems = dataTable.querySelectorAll('[data-check-item]');
        if (checkAll && checkItems.length > 0) {
            // 初始化全选按钮
            initializeCheckAll(checkAll, checkItems);
            // 初始化点击表格数据单元可选中表行选项卡的功能
            const dataCells = dataTable.querySelectorAll('[data-column-id]');
            if (dataCells.length > 0) {
                initializeRowClick(dataCells);
            }
        }
        // 初始化表格头、表格设置功能
        // dataTable在上面已经被定义
    //初始化唯一数据表格的选行功能
    
    const modalDatatableConfig =  new ModalDatatableConfig('#datatable-modal-config-main', dataTable);
    if (!modalDatatableConfig.active)
        console.log('Datatable config modal is not initialized');
        // 初始化表格下载功能
        const downloadButton = document.getElementById('downloadCSVButton');
        if (downloadButton) {
            initializeDownloadCSV(dataTable, downloadButton);
        }
        // 初始化全文搜索功能
        const tableSearchButton = document.getElementById('tableSearchButton');
        const tableSearchQuery = document.getElementById('tableSearchQuery');
        if (tableSearchQuery && tableSearchButton) {
            initializeSearch(dataTable, tableSearchQuery, tableSearchButton);
        }
        // 初始化查看表格数据页面的删除记录提示框
        const deleteButtons = document.querySelectorAll('[data-delete-record-url]');
        const alertModal = document.getElementById('alertModal');
        if(deleteButtons.length > 0 && alertModal) {
            initializeDeleteButtons(dataTable, deleteButtons, alertModal);   
        }
        const extensionButtons = document.querySelectorAll('[data-dbman-toggle="extension"]');
        if(extensionButtons.length > 0 && alertModal) {
            initializeExtension(dataTable, extensionButtons, alertModal);
        }
    }
    // 初始化修改和添加页面的提示框
    const modifyForm = document.getElementById('ModifyForm');
    if (modifyForm) {
        initializeModifyForm(modifyForm);
    }
    //初始化JSON显示的提示框
    //if(jsonviewButtons.length > 0 && jsonModal && jsonModalBody && jsonModalCloseButtons.length > 0) {
    //    initializeJSONview(jsonviewButtons, jsonModal, jsonModalBody, jsonModalCloseButtons);
    //}    
});

// 初始化所有的工具提示
function initializeTooltips(tooltipList) {
    // 提示栏只在悬停时触发
    tooltipList.forEach((tooltip) => {tooltip.dataset.bsTrigger = 'hover';});
    var tooltipTriggerList = [].slice.call(tooltipList);
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}
// 初始化提示模态框的关闭按钮，点击时隐藏现有提示信息并关闭模态框
function initializeAlertModal(alertModal) {
    alertModal.addEventListener('hide.bs.modal', () => {
        blurModalFocus(alertModal);
        msgTypes.forEach((msgType) => alertModal.querySelector('[data-' + msgType + ']').classList.add('d-none'));
    });
}
/*** #dataTable block begins：数据表关联函数集 ***/ 
// 初始化全选复选框功能
function initializeCheckAll(checkAll, checkItems) {
    // 当总开关的状态改变时，更新所有子复选框的状态
    checkAll.addEventListener('change', function () {
        checkItems.forEach(item => {
            item.checked = checkAll.checked;
        });
    });
    // 当子复选框的状态改变时，更新总开关的状态
    checkItems.forEach(item => {
        item.addEventListener('change', function () {
            const allChecked = Array.from(checkItems).every(item => item.checked);
            checkAll.checked = allChecked;
        });
    });
}
// 初始化表格行点击事件
function initializeRowClick(dataCells) {
    // 为表格的每个数据单元添加点击事件监听器
    dataCells.forEach(dataCell => dataCell.addEventListener('click', function (e) {
        const target = e.target.closest('tr'); // 找到最近的 <tr> 元素
        if (target) {
            const checkbox = target.querySelector('[data-check-item]'); // 找到该行的复选框
            if (checkbox) {
                checkbox.checked = !checkbox.checked; // 切换复选框的选中状态
                const event = new Event('change', { bubbles: true });
                checkbox.dispatchEvent(event);
            }
        }
    }));
}

// 初始化搜索框，添加事件监听器，监听回车键，按回车键等同于点击搜索按钮
function initializeSearch(dataTable, searchQuery, searchBtn) {
    const noFilterBtn = document.getElementById('tableSearchNoFilterButton');
    searchQuery.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchBtn.click();
        };
    });
    noFilterBtn.addEventListener('click', function(){
        searchQuery.value = '';
        searchBtn.click();
    });
    searchBtn.addEventListener('click', function() {
        const searchText = searchQuery.value;
        const dataRows = dataTable.querySelectorAll('tbody tr');
        if(searchText != curSearchQuery) {
            dataRows.forEach(function(dataRow) {
                var match = false || (searchText == '');
                if(match == false) {
                    const dataCells = dataRow.querySelectorAll('td[data-column-id]');
                    for(const dataCell of dataCells) {
                        if(dataCell.textContent.toLowerCase().includes(searchText.toLowerCase())) {
                            match = true;
                            break;
                        }
                    }; 
                }
                if(match == true) {
                    dataRow.classList.remove('d-none');
                } else {
                    dataRow.classList.add('d-none');
                }
            });  
            curSearchQuery = searchText;
        }
        if(curSearchQuery == '') {
            noFilterBtn.classList.add('d-none');
        } else {
            noFilterBtn.classList.remove('d-none');
        }
    });
}
// 初始化表格头、表格设置功能
function initializeTableConfig(dataTable, tableConfigButton, tableConfigModal) {
    // 保存原始复选框状态和顺序
    const tableConfigTHeadsList = document.getElementById('tableConfigTHeadsList');
    if(tableConfigTHeadsList) {
        function saveTHeadsState(orders, checkeds) {
            tableConfigTHeadsList.querySelectorAll('[data-tcm-cb]').forEach((cb) => {
                orders.push(cb.dataset.tcmCb);
                checkeds.push(cb.checked);
            });
        }
        function restoreTHeadsState(orders, checkeds) {
            orders.forEach((order, index) => {
                const li = tableConfigTHeadsList.querySelector('li[data-tcm-li="'+ order +'"]');
                const cb = li.querySelector('[data-tcm-cb]');
                cb.checked = checkeds[index];
                tableConfigTHeadsList.appendChild(li);
            });
        }
        const checkboxes = tableConfigTHeadsList.querySelectorAll('[data-tcm-cb]');
        if(checkboxes.length > 0) {
            const saveTableConfigButton = tableConfigModal.querySelector('#saveTableConfigButton'); 
            // 保存表头列表的原始节点，恢复默认时使用
            saveTHeadsState(originalTheadsOrder, originalTheadsChecked);
            // 表格设置按钮点击事件监听器
            tableConfigButton.addEventListener('click', function() {
                // 存储点击前的复选框状态和顺序  
                saveTHeadsState(initialTHeadsOrder, initialTHeadsChecked);
                saveTableConfigButton.classList.remove('data-tcm-saved');
                showModal(tableConfigModal);
            });
            // 定义保存当前状态按钮的事件
            
            if(saveTableConfigButton) {
                saveTableConfigButton.addEventListener('click', function(event) {
                    var newOrder = [];
                    // 这里必须重新选取所有复选框以实现正确的表头自定义顺序
                    tableConfigTHeadsList.querySelectorAll('[data-tcm-cb]').forEach(function(checkbox) {
                        var columnId = checkbox.dataset.tcmCb;
                        newOrder.push(columnId);
                        var column = dataTable.querySelector('th[data-column-id="' + columnId + '"]');
                        var cells = dataTable.querySelectorAll('td[data-column-id="' + columnId + '"]');
                        // 显示数据表中选中的表头对应的列
                        if (checkbox.checked) {
                            column.style.display = '';
                            cells.forEach(function(cell) {
                                cell.style.display = '';
                            });
                        // 隐藏数据表中未选中的的表头对应的列
                        } else {
                            column.style.display = 'none';
                            cells.forEach(function(cell) {
                                cell.style.display = 'none';
                            });
                        }
                    });
                    // 重新生成表
                    var theadRow = dataTable.querySelector('thead tr');
                    var tbodyRows = dataTable.querySelectorAll('tbody tr');
                    // appendChild 方法会将现有的元素从其当前父节点移动到新的父节点。
                    // 这意味着将一个元素 appendChild 到另一个父节点，它将从其原始位置移除并添加到新的位置。
                    newOrder.forEach(function(columnId) {
                        var column = dataTable.querySelector('th[data-column-id="' + columnId + '"]');
                        theadRow.appendChild(column);
                        tbodyRows.forEach(function(row) {
                            var cell = row.querySelector('td[data-column-id="' + columnId + '"]');
                            row.appendChild(cell);
                        });
                    });
                    saveTableConfigButton.classList.add('data-tcm-saved');
                    hideModal(tableConfigModal);
                });
            }
            // 定义恢复默认按钮的事件
            const restoreTableConfigDefaultButton = tableConfigModal.querySelector('#restoreTableConfigDefaultButton');
            if(restoreTableConfigDefaultButton) {
                restoreTableConfigDefaultButton.addEventListener('click', function() {
                    restoreTHeadsState(originalTheadsOrder, originalTheadsChecked);
                });
            }
            // 定义取消和关闭按钮的事件
            tableConfigModal.addEventListener('hide.bs.modal', () => {
                // 如果是保存配置触发的隐藏行为，不执行恢复点击前状态的动作
                if(!saveTableConfigButton.classList.contains('data-tcm-saved')) {
                    restoreTHeadsState(initialTHeadsOrder, initialTHeadsChecked);
                }
                blurModalFocus(tableConfigModal);
            });       
            // Drag and drop functionality for reordering columns
            // 找到拖动的标签下面的标签
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
            const draggables = document.querySelectorAll('#tableConfigTHeadsList .draggable');
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
                    const parentLi = tableConfigModal.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
                    // 记录鼠标按下时的相对位置
                    afterElement = getDragAfterElement(tableConfigTHeadsList, e.clientY)
                    if (afterElement == null) {
                        tableConfigTHeadsList.appendChild(parentLi);
                    } else {
                        tableConfigTHeadsList.insertBefore(parentLi, afterElement);
                    }
                }

                function onMouseUp() {
                    const parentLi = tableConfigTHeadsList.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
                    parentLi.classList.remove('dragging');
                    parentLi.classList.remove('active');
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                }

                function onTouchMove(e) {
                    const parentLi = tableConfigTHeadsList.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
                    const touch = e.touches[0];
                    const afterElement = getDragAfterElement(tableConfigTHeadsList, touch.clientY);

                    if (afterElement == null) {
                        tableConfigTHeadsList.appendChild(parentLi);
                    } else {
                        tableConfigTHeadsList.insertBefore(parentLi, afterElement);
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
        }
    }
}
// 初始化删除提示框
function initializeDeleteButtons(dataTable, deleteButtons, alertModal) {
    initializeAlertModal(alertModal);
    function initializeConfirmBtn() {
        const activeConfirmBtn = alertModal.querySelector('#AlertModalActiveConfirm');
        if(activeConfirmBtn) { activeConfirmBtn.remove();}
        const alertConfirmButton = alertModal.querySelector('[data-am-confirm]').cloneNode(true);
        alertConfirmButton.classList.remove('d-none');
        const alertFooter = alertModal.querySelector('.modal-footer');
        alertFooter.appendChild(alertConfirmButton);
        return alertConfirmButton;
    }
    deleteButtons.forEach(function(deleteButton) {
        deleteButton.addEventListener('click', function() {
            const alertConfirmButton = initializeConfirmBtn();
            setAlertMsg(alertModal, 'warning-delete', '');
            alertConfirmButton.dataset.deleteRecordUrl = deleteButton.dataset.deleteRecordUrl;
            alertConfirmButton.id = 'AlertModalActiveConfirm';
            alertConfirmButton.addEventListener('click', function() {
                this.classList.add('d-none');        
                $.ajax({
                    type: 'post',
                    url: alertConfirmButton.dataset.deleteRecordUrl,
                    success: function(response) {
                        setAlertMsg(alertModal, 'success', tabulate(response.message));
                        const dismissButtons = alertModal.querySelectorAll('[data-bs-dismiss]');
                        dismissButtons.forEach(function(dismissButton) {
                            dismissButton.addEventListener('click', reloadWindow); 
                        });
                    },
                    error: function(xhr, status, error) {
                        setAlertMsg(alertModal, 'error', error);
                    }
                });
            });
            showModal(alertModal);
        });
    });
    const deleteAllButton = document.getElementById('deleteAllButton');
    deleteAllButton.addEventListener('click', () => {
        const alertConfirmButton = initializeConfirmBtn();
        setAlertMsg(alertModal, 'warning-delete', '');
        alertConfirmButton.addEventListener('click', () => {
            const checkboxes = dataTable.querySelectorAll('[data-check-item]:checked');
            const promises = [];
            checkboxes.forEach((checkbox) => {
                const row = checkbox.parentElement.parentElement;
                const delBtn = row.querySelector('[data-delete-record-url]');
                const msg = {};
        
                const promise = new Promise((resolve, reject) => {
                    $.ajax({
                        type: 'post',
                        url: delBtn.dataset.deleteRecordUrl,
                        success: function(response) {
                            msg[checkbox.dataset.checkItem] = "successful";
                            resolve(msg);
                        },
                        error: function(xhr, status, error) {
                            msg[checkbox.dataset.checkItem] = "failed";
                            resolve(msg);
                        }
                    });
                });
                promises.push(promise);
            });
            Promise.all(promises).then((results) => {
                var finalMsg = '{';
                var flagError = false;
                results.forEach(result => {
                    for (const key in result) {
                        finalMsg += `"${key}": "${result[key]}",`;
                        flagError = flagError || key=='failed';                    }
                });
                finalMsg += '"id":"status"}';
                const msgType = 'success';
                if(flagError) { msgType = 'error'};
                setAlertMsg(alertModal, msgType, tabulate(finalMsg));
            });
        });
        showModal(alertModal);     
    });
}

// 初始化扩展表提示框
function initializeExtension(dataTable, extensionButtons, alertModal) {
    initializeAlertModal(alertModal);
    function initializeConfirmBtn(alertModal) {
        const activeConfirmBtn = alertModal.querySelector('#AlertModalActiveConfirm');
        if(activeConfirmBtn) { activeConfirmBtn.remove();}
        const alertConfirmButton = alertModal.querySelector('[data-am-confirm]').cloneNode(true);
        alertConfirmButton.classList.remove('d-none');
        alertConfirmButton.id = 'AlertModalActiveConfirm';
        const alertFooter = alertModal.querySelector('.modal-footer');
        alertFooter.appendChild(alertConfirmButton);
        return alertConfirmButton;
    }
    extensionButtons.forEach(function(deleteButton) {
        deleteButton.addEventListener('click', function() {
            const alertConfirmButton = initializeConfirmBtn();
            setAlertMsg(alertModal, 'warning-delete', '');
            alertConfirmButton.dataset.deleteRecordUrl = deleteButton.dataset.deleteRecordUrl;
            alertConfirmButton.id = 'AlertModalActiveConfirm';
            alertConfirmButton.addEventListener('click', function() {
                this.classList.add('d-none');        
                $.ajax({
                    type: 'post',
                    url: alertConfirmButton.dataset.deleteRecordUrl,
                    success: function(response) {
                        setAlertMsg(alertModal, 'success', tabulate(response.message));
                        const dismissButtons = alertModal.querySelectorAll('[data-bs-dismiss]');
                        dismissButtons.forEach(function(dismissButton) {
                            dismissButton.addEventListener('click', reloadWindow); 
                        });
                    },
                    error: function(xhr, status, error) {
                        setAlertMsg(alertModal, 'error', error);
                    }
                });
            });
            showModal(alertModal);
        });
    });
    const deleteAllButton = document.getElementById('deleteAllButton');
    deleteAllButton.addEventListener('click', () => {
        const alertConfirmButton = initializeConfirmBtn();
        setAlertMsg(alertModal, 'warning-delete', '');
        alertConfirmButton.addEventListener('click', () => {
            const checkboxes = dataTable.querySelectorAll('[data-check-item]:checked');
            const promises = [];
            checkboxes.forEach((checkbox) => {
                const row = checkbox.parentElement.parentElement;
                const delBtn = row.querySelector('[data-delete-record-url]');
                const msg = {};
        
                const promise = new Promise((resolve, reject) => {
                    $.ajax({
                        type: 'post',
                        url: delBtn.dataset.deleteRecordUrl,
                        success: function(response) {
                            msg[checkbox.dataset.checkItem] = "successful";
                            resolve(msg);
                        },
                        error: function(xhr, status, error) {
                            msg[checkbox.dataset.checkItem] = "failed";
                            resolve(msg);
                        }
                    });
                });
                promises.push(promise);
            });
            Promise.all(promises).then((results) => {
                var finalMsg = '{';
                var flagError = false;
                results.forEach(result => {
                    for (const key in result) {
                        finalMsg += `"${key}": "${result[key]}",`;
                        flagError = flagError || key=='failed';                    }
                });
                finalMsg += '"id":"status"}';
                const msgType = 'success';
                if(flagError) { msgType = 'error'};
                setAlertMsg(alertModal, msgType, tabulate(finalMsg));
            });
        });
        showModal(alertModal);     
    });
}
// 下载当前带筛选视图的CSV文件
function initializeDownloadCSV(dataTable, downloadButton) {
    downloadButton.addEventListener('click', function() {
        const headRow = dataTable.querySelector('thead tr');
        const dataRows = dataTable.querySelectorAll('tbody tr:not(.d-none)');
    
        // Extract header data
        const headers = [];
        headRow.querySelectorAll('th[data-column-id]').forEach(th => {
            headers.push(th.dataset.columnData.trim());
        });
    
        // Extract data row content
        const rows = [];
        dataRows.forEach(row => {
            const rowData = [];
            row.querySelectorAll('td[data-column-id]').forEach(td => {
                var data = td.textContent.trim();
                const colData = td.dataset.columnData
                if(colData) { data = colData }
                rowData.push(data);
            });
            rows.push(rowData);
        });
    
        // Create CSV string
        let csvContent = headers.join(',') + '\n';
        rows.forEach(row => {
            csvContent += row.join(',') + '\n';
        });
    
        // Create a Blob object with the CSV data
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    
        // Create a link element to trigger the download
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'data.csv';
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
    
        // Trigger the download
        link.click();
    
        // Clean up
        document.body.removeChild(link);
    });
}
/*** #dataTable block ends */

// 初始化修改、添加记录模态框
function initializeModifyForm(modifyForm) {
    var form = $(modifyForm);
    const alertModal = document.getElementById('alertModal');
    initializeAlertModal(alertModal);
    const backButton = alertModal.querySelector('[data-am-back]');
    backButton.classList.remove('d-none');
    if(backButton) {
        backButton.addEventListener('click', function() {
           const prevPageButton = document.getElementById('prevPage');
           location.href = prevPageButton.href; 
        });
    }
    form.on('submit', function(event) { // 直接绑定事件到 jQuery 对象
        event.preventDefault(); // 阻止默认提交行为
        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: function(response) {
                setAlertMsg(alertModal, 'success', response.message);
            },
            error: function(xhr, status, error) {
                setAlertMsg(alertModal, 'error', error);
            }
        });
        showModal(alertModal);    
    });
}

function initializeJSONview(jsonviewButtons, alertModal, alertBody, alertConfirm, alertCancel) {
    jsonviewButtons.forEach(function(jsonviewButton){
        jsonviewButton.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('#alertModal [data-bs-dismiss="modal"]').forEach(function(button) {
                const cbtn = button.cloneNode(true);
                cbtn.addEventListener('click', (e) => blurModalFocus(alertModal));
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
                hideModal(alertModal);
            });
            alertConfirm.parentNode.replaceChild(cbtn, alertConfirm);
            showModal(alertModal);
        });
    });

}
