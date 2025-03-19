import {DragContainer} from './dragcontainer-dbman.js'
export class ModalDBMan {
    constructor(selector) {
        this.active = false;
        this.modal = document.querySelector(selector);
        if(!this.modal)
            return;
        this.bsModal = bootstrap.Modal.getOrCreateInstance(this.modal);
        if(!this.bsModal)
            return;
        this.modal.addEventListener('hide.bs.modal', this._extraHandlerHide.bind(this));
        this.selector = selector;
        this._saveChanges = false;
        this.active = true;
    }
    
    show() {
        this.bsModal.show();
    }

    hide() {
        this._blurFocus();
        this.bsModal.hide();
    }

    /**
     * 让模态框内部失去聚焦，防止浏览器aria-hidden警告
     */
    _blurFocus() {
        if (document.activeElement && document.activeElement.closest(this.selector)) {
            document.activeElement.blur();
        }
    }

    _extraHandlerHide() {
        this._blurFocus();
    }
}

export class ModalDatatableConfig extends ModalDBMan {
    constructor(selector, table) {
        super(selector);
        if(!this.active) 
            return;
        this.active = false;
        this.headerListgroup = this.modal.querySelector('.list-group');
        if(!this.headerListgroup)
            return; 
        const headerLis = this.headerListgroup.querySelectorAll('li[data-dbman-sn]');
        if(headerLis.length === 0)
            return;
        const headerCboxes = this.headerListgroup.querySelectorAll('li[data-dbman-sn] [type="checkbox"]');
        if(headerCboxes.length === 0)
            return;
        // save original checkbox orders and checked states
        this._listOriginalStates = this._saveListStates();
        this._listInitialStates = [];

        // add extra handler to save initial checkbox orders and checked states
        this.modal.addEventListener('show.bs.modal', this._extraHandlerSaveInitialStates.bind(this));
        // add extra handler to restore initial checkbox orders and checked states
        this.modal.addEventListener('hide.bs.modal', this._extraHandlerRestoreInitialStates.bind(this));
        // add extra handler to save changes in headers config
        
        this._btnSaveChanges = this.modal.querySelector('[data-dbman-toggle="save-changes"]');
        if(!this._btnSaveChanges)
            return;
        this._btnSaveChanges.addEventListener('click', this._handlerSaveChanges.bind(this));

        this._btnRestoreDefault = this.modal.querySelector('[data-dbman-toggle="restore-default"]');
        if(!this._btnRestoreDefault)
            return;
        this._btnRestoreDefault.addEventListener('click', this._handlerRestoreDefault.bind(this));
        this._dragContainer = new DragContainer(this.headerListgroup, 'vertical')
        this.table = table;
        this.active = true;
    }

    _saveListStates() {
        const liStates = [];
        this.headerListgroup.querySelectorAll('li[data-dbman-sn]').forEach((li) => {
            const cb = li.querySelector('[type="checkbox"]');
            const liState = [li.dataset.dbmanSn, cb.checked];
            liStates.push(liState);
        });
        return liStates;
    }

    _restoreListStates(listStates) {
        listStates.forEach((listState) => {
            const li = this.headerListgroup.querySelector('li[data-dbman-sn="'+ listState[0] +'"]');
            const cb = li.querySelector('[type="checkbox"]');
            cb.checked = listState[1];
            this.headerListgroup.appendChild(li)
        });
    }

    _extraHandlerSaveInitialStates() {
        this._listInitialStates = this._saveListStates();
    }

    _extraHandlerRestoreInitialStates() {
        if(this._saveChanges) {
            this._saveChanges = false;
            return;
        }
        this._restoreListStates(this._listInitialStates);
    }

    _handlerSaveChanges() {
        const theadRow = this.table.querySelector('thead tr');
        const tbodyRows = this.table.querySelectorAll('tbody tr');
        this.headerListgroup.querySelectorAll('li[data-dbman-sn]').forEach((li) => {
            const cb = li.querySelector('[type="checkbox"]');
            const colNum = li.dataset.dbmanSn;

            const th = this.table.querySelector('th[data-dbman-sn="' + colNum + '"]');
            const tds = this.table.querySelectorAll('td[data-dbman-sn="' + colNum + '"]');
            
            // 移动数据表中选中的表头对应的列
            theadRow.appendChild(theadRow.querySelector('th[data-dbman-sn="' + colNum + '"]'));
            tbodyRows.forEach((row) => {
                row.appendChild(row.querySelector('td[data-dbman-sn="' + colNum + '"]'));
            });

            // 显示数据表中选中的表头对应的列
            if (cb.checked) {
                th.classList.remove('d-none');
                tds.forEach((cell) => cell.classList.remove('d-none'));
            // 隐藏数据表中未选中的的表头对应的列
            } else {
                th.classList.add('d-none');
                tds.forEach((cell) => cell.classList.add('d-none'));
            }
        });
        this._saveChanges = true;
        this.hide();
    }

    _handlerRestoreDefault() {
        this._restoreListStates(this._listOriginalStates);
    }
}

export class ModalAlert extends ModalDBMan {
    constructor(selector) {
        super(selector);
        if(!this.active) 
            return;
        this.active = false;
        this.modalTitle = this.modal.querySelector('.modal-title');
        if(!this.modalTitle)
            return;
        this.modalBody = this.modal.querySelector('.modal-body');
        if(!this.modalBody)
            return;
        this.btnAcknowledge = this.modal.querySelector('[data-dbman-toggle="acknowledge"]');
        if(!this.btnConfirm)
            return;
        this.btnConfirm = this.modal.querySelector('[data-dbman-toggle="confirm"]');
        if(!this.btnConfirm)
            return;
        this.btnCancel = this.modal.querySelector('[data-dbman-toggle="cancel"]');
        if(!this.btnCancel)
            return;
        this.confirmActionHandlers = [];
        this.validBtns = {
            'acknowledge': this.btnAcknowledge,
            'confirm': this.btnConfirm,
            'cancel': this.btnCancel
        }
        this.msg = this.modalBody.textContent;
        this.title = this.modalTitle.textContent;
        this.active = true;
    }

    update({msg = this.msg, title = this.title, buttonTypes = 'acknowledge', confirmAction = null}) {
        if (!this.active) 
            return;
        if (msg) {
            this.msg = msg;
            this.modalBody.textContent = msg;
        }
        if (title) {
            this.title = title;
            this.modalTitle.textContent = title;
        }
        let buttonTypesList = [];
        if (buttonTypes) {
            buttonTypesList = buttonTypes.split(',');
            const validBtnNames = Object.keys(this.validBtns);
            buttonTypesList.forEach(btnName => {
                if (validBtnNames.includes(btnName)) {
                    btn = this.validBtns[btnName];
                    btn.classList.remove('d-none');
                    validBtnNames.pop(btnName);
                }
            });
            validBtnNames.forEach(btnName => {
                btn = this.validBtns[btnName];
                btn.classList.add('d-none');
            });
        }
        if(confirmAction && typeof confirmAction === 'function' && buttonTypesList.includes('confirm')) {
            const confirmActionHandler = confirmAction;
            this.removeAllHandlers();
            this.btnConfirm.addEventListener('click', confirmActionHandler);
            this.confirmActionHandlers.push(confirmActionHandler);
        }
    }

    _addHandler(handler) {
        this.btnConfirm.addEventListener('click', handler);
        this.confirmActionHandlers.push(handler);
    }

    removeAllHandlers() {
        this.confirmActionHandlers.forEach((handler) => {
            this.btnConfirm.removeEventListener('click', handler);
        });
    }

    removeHandler(handler) {
        if(handler && typeof handler === 'function' && this.confirmActionHandlers.includes(handler)) {
            this.btnConfirm.removeEventListener('click', handler);
            this.confirmActionHandlers = this.confirmActionHandlers.filter((h) => h !== handler);
        }
    }
}
