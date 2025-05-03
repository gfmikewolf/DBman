// mj/modal-alert-mj.js

import { ModalMJ } from './modal-mj.js';

export class ModalAlertMJ extends ModalMJ {
  constructor(container) {
    super(container);
  }

  _findElements(container) {
    super._findElements && super._findElements(container);
    this.modalTitle = this.getValidElement('.modal-title');
    this.modalBody = this.getValidElement('.modal-body');
    this.btnAcknowledge = this.getValidElement('[data-dbman-toggle="acknowledge"]');
    this.btnConfirm = this.getValidElement('[data-dbman-toggle="confirm"]');
    this.btnCancel = this.getValidElement('[data-dbman-toggle="cancel"]');
  }

  _initProperties(container) {
    super._initProperties && super._initProperties(container);
    this.predefinedTexts = 
      Array.from(this.container.querySelectorAll('span[data-dbman-key].d-none')).reduce(
        (acc, span) => (
          acc[span.dataset.dbmanKey] = [span.dataset.dbmanTitle, span.innerText.trim()], 
          acc
        ), 
        {}
      );
    this.confirmActionHandlers = [];
    this.validBtns = {
      'acknowledge': this.btnAcknowledge,
      'confirm': this.btnConfirm,
      'cancel': this.btnCancel
    };
    this.msg = this.modalBody.textContent.trim();
    this.title = this.modalTitle.textContent.trim();
  }

  update({ msgKey = null, message = '', buttonTypes = ['acknowledge'], confirmAction = null }) {     
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

  show(timeout = 0) {
    super.show(timeout);
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
