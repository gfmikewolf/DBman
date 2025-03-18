import * as bootstrap from 'bootstrap';

export class ModalDBMan {
    constructor(selector) {
        this.modal = document.querySelector(selector);
        if(!this.modal) { 
            this.status = 'error';
            return; 
        }
        this.bsModal = new bootstrap.Modal(this.modal);
        this.selector = selector;
        this.status = 'initialized';
    }
    show() {
        this.bsModal.show();
        this.status = 'shown';
    }
    // 让模态框内部失去聚焦，防止浏览器警告
    blurFocus() {
        if (document.activeElement && document.activeElement.closest(this.selector)) {
            document.activeElement.blur();
        }
    }
    // 隐藏模态框
    hide() {
        this.blurFocus();
        this.bsModal.hide();
        this.status = 'hidden';
    }
}

export class ModalDatatableConfig extends DBManModal {
    constructor(selector) {
        super(selector);
        this.headerListgroup = this.modal.querySelector('.list-group');
        if(!this.headerListgroup) { 
            this.status = 'error'; 
            return; 
        }
        this.headerLis = this.headerListgroup.querySelectorAll('li[data-dbman-sn]')
        if(this.headerLis.length == 0) {
            this.status = 'error';
            return;
        }
        this.headerCboxes = this.headerLis.querySelectorAll('[type="checkbox"]');
        if(this.headerCboxes.length == 0) {
            this.status = 'error';
            return;
        }
        this.cboxOriginalStates = this.saveCboxState();
        this.cboxInitialStates = this.cboxOriginalStates;
        this.status = 'initialized';
    }
    saveCboxState() {
        return Array.from(this.headerCboxes).map(
            cb => [cb.dataset.dbmanSn, cb.checked]
        );
    }
    restoreCboxState(orders, checkeds) {
        orders.forEach((order, index) => {
            const li = this.headerLis.querySelector('[data-dbman-sn="'+ order +'"]');
            const cb = li.querySelector('[type="checkbox"]');
            cb.checked = checkeds[index];

            
        function initializeTableConfig(dataTable, tableConfigButton, tableConfigModal) {
            // 保存原始复选框状态和顺序
            const tableConfigTHeadsList = document.getElementById('tableConfigTHeadsList');
            if(tableConfigTHeadsList) {
                
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
    }
}
class ModalAlert extends DBManModal {
    constructor(selector) {
        super(selector);
        this.msgTypes = this.modal.querySelectorAll('')
        this.modal.addEventListener('hide.bs.modal', () => {
            super.blurFocus();
            this.msgTypes.forEach((msgType) => 
                this.model.querySelector('[data-' + msgType + ']').classList.add('d-none'));
        });
    }
    getConfirmBtn(id_confirm='alertmodal') {
        const activeConfirmBtn = modal.querySelector('#'+id_confirm);
        if(activeConfirmBtn) { activeConfirmBtn.remove();}
        const alertConfirmButton = modal.querySelector('[data-am-confirm]').cloneNode(true);
        alertConfirmButton.classList.remove('d-none');
        alertConfirmButton.id = id_confirm;
        const alertFooter = modal.querySelector('.modal-footer');
        alertFooter.appendChild(alertConfirmButton);
        return alertConfirmButton;
    }    
}
