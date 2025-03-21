import { DragContainer } from './drag-container-dbman.js'

export class ModalDBMan {
    constructor(selector) {
        this.active = true;
        this.modal = document.querySelector(selector);
        if (!this.modal) {
            this.active = false;
            return;
        }
        this.bsModal = bootstrap.Modal.getOrCreateInstance(this.modal);
        if (!this.bsModal) {
            this.active = false;
            return;
        }
        // Add an extra handler when the modal is being hidden
        this.modal.addEventListener('hide.bs.modal', this._extraHandlerHide.bind(this));
        this.selector = selector;
    }
    
    show() {
        this.bsModal.show();
    }

    hide() {
        this._blurFocus();
        this.bsModal.hide();
    }

    /**
     * Remove focus from elements inside the modal to prevent aria-hidden warnings.
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
        if (!this.active) {
            return;
        }
        this.headerListgroup = this.modal.querySelector('.list-group');
        if (!this.headerListgroup) {
            this.active = false;
            return;
        }
        const headerLis = this.headerListgroup.querySelectorAll('li[data-dbman-sn]');
        if (headerLis.length === 0) {
            this.active = false;
            return;
        }
        const headerCboxes = this.headerListgroup.querySelectorAll('li[data-dbman-sn] [type="checkbox"]');
        if (headerCboxes.length === 0) {
            this.active = false;
            return;
        }
        // Save original checkbox order and checked states
        this._listOriginalStates = this._saveListStates();
        this._listInitialStates = [];

        // Add extra handler to save current checkbox order and states when showing the modal
        this.modal.addEventListener('show.bs.modal', this._extraHandlerSaveInitialStates.bind(this));
        // Add extra handler to restore initial checkbox order and states when hiding the modal
        this.modal.addEventListener('hide.bs.modal', this._extraHandlerRestoreInitialStates.bind(this));
        // Find the "Save Changes" button in the modal header config
        this._btnSaveChanges = this.modal.querySelector('[data-dbman-toggle="save-changes"]');
        if (!this._btnSaveChanges) {
            this.active = false;
            return;
        }
        this._btnSaveChanges.addEventListener('click', this._handlerSaveChanges.bind(this));

        // Find the "Restore Default" button in the modal header config
        this._btnRestoreDefault = this.modal.querySelector('[data-dbman-toggle="restore-default"]');
        if (!this._btnRestoreDefault) {
            this.active = false;
            return;
        }
        this._btnRestoreDefault.addEventListener('click', this._handlerRestoreDefault.bind(this));

        this._dragContainer = new DragContainer(this.headerListgroup, 'vertical');
        this.table = table;
        // When _saveChanges is true, hiding the modal will not restore the initial states
        this._saveChanges = false;
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
            const li = this.headerListgroup.querySelector('li[data-dbman-sn="' + listState[0] + '"]');
            const cb = li.querySelector('[type="checkbox"]');
            cb.checked = listState[1];
            this.headerListgroup.appendChild(li);
        });
    }

    _extraHandlerSaveInitialStates() {
        this._listInitialStates = this._saveListStates();
    }

    _extraHandlerRestoreInitialStates() {
        if (this._saveChanges) {
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
            
            // Move the selected header column in the data table
            theadRow.appendChild(theadRow.querySelector('th[data-dbman-sn="' + colNum + '"]'));
            tbodyRows.forEach((row) => {
                row.appendChild(row.querySelector('td[data-dbman-sn="' + colNum + '"]'));
            });

            // Show the column in the data table if checkbox is checked
            if (cb.checked) {
                th.classList.remove('d-none');
                tds.forEach((cell) => cell.classList.remove('d-none'));
            // Hide the column if checkbox is not checked
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
        if (!this.active) {
            return;
        }
        this.modalTitle = this.modal.querySelector('.modal-title');
        if (!this.modalTitle) {
            this.active = false;
            return;
        }
        this.modalBody = this.modal.querySelector('.modal-body');
        if (!this.modalBody) {
            this.active = false;
            return;
        }
        this.btnAcknowledge = this.modal.querySelector('[data-dbman-toggle="acknowledge"]');
        if (!this.btnAcknowledge) {
            this.active = false;
            return;
        }
        this.btnConfirm = this.modal.querySelector('[data-dbman-toggle="confirm"]');
        if (!this.btnConfirm) {
            this.active = false;
            return;
        }
        this.btnCancel = this.modal.querySelector('[data-dbman-toggle="cancel"]');
        if (!this.btnCancel) {
            this.active = false;
            return;
        }
        this.predefinedTexts = {};
        const spanElements = this.modal.querySelectorAll('span[data-dbman-key].d-none');
        spanElements.forEach(span => {
            const key = span.dataset.dbmanKey;
            const title = span.dataset.dbmanTitle;
            const text = span.innerText.trim();
            this.predefinedTexts[key] = [title, text];
        });
        this.confirmActionHandlers = [];
        this.validBtns = {
            'acknowledge': this.btnAcknowledge,
            'confirm': this.btnConfirm,
            'cancel': this.btnCancel
        };
        this.msg = this.modalBody.textContent;
        this.title = this.modalTitle.textContent;
    }

    update({ msgKey = null, message = '', buttonTypes = ['acknowledge'], confirmAction = null }) {
        if (!this.active)
            return;
        if (msgKey) {
            this.msg = '<div class="container"><div class="row">' +
                this.predefinedTexts[msgKey][1] + '</div><div class="row">' +
                message + '</div></div>';
            this.title = this.predefinedTexts[msgKey][0];
            this.modalBody.innerHTML = this.msg;
            this.modalTitle.textContent = this.title;
        }

        const validBtnNames = Object.keys(this.validBtns);
        // Show buttons specified in buttonTypes and hide the others
        buttonTypes.forEach(btnName => {
            if (validBtnNames.includes(btnName)) {
                const btn = this.validBtns[btnName];
                btn.classList.remove('d-none');
                const index = validBtnNames.indexOf(btnName);
                validBtnNames.splice(index, 1);
            }
        });

        validBtnNames.forEach(btnName => {
            const btn = this.validBtns[btnName];
            btn.classList.add('d-none');
        });
        
        this.removeAllHandlers();
        if (confirmAction &&
            typeof confirmAction === 'function' &&
            buttonTypes.includes('confirm')) {
            const confirmActionHandler = confirmAction;
            this._addHandler(confirmActionHandler);
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
        this.confirmActionHandlers = [];
    }

    removeHandler(handler) {
        if (handler && typeof handler === 'function' && this.confirmActionHandlers.includes(handler)) {
            this.btnConfirm.removeEventListener('click', handler);
            this.confirmActionHandlers = this.confirmActionHandlers.filter((h) => h !== handler);
        }
    }
}
