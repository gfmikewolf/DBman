// mj/form-modify-mj.js
import { ContainerMJ } from './container-mj.js';
import { ModalAlertMJ } from './modal-alert-mj.js';
import { DatajsonMJ } from './datajson-mj.js';

class FormModifyMJ extends ContainerMJ {
  constructor(container, modalAlert) {
    super(container, modalAlert);
  }

  _initArgs(container, modalAlert) {
    super._initArgs(container, modalAlert);
    this.modalAlert = ModalAlertMJ.getOrCreateInstance(modalAlert);
  }

  _findElements(container, modalAlert) {
    super._findElements && super._findElements(container, modalAlert);
    this.submitButton = this.getValidElement('button[type="submit"]');
  }

  _initProperties(container, modalAlert) {
    super._initProperties && super._initProperties(container, modalAlert);
    this.initialData = new FormData(this.container);
    this.datajsonRefMap = fromTemplate['datajson_ref_map'];
    if (typeof this.datajsonRefMap !== 'object') {
      throw new TypeError(`${varDatajsonRefMapFromTemplate} is not object.`);
    }
  }

  _initFunctions(container, modalAlert) {
    super._initFunctions && super._initFunctions(container, modalAlert);
    this.submitButton.addEventListener('click', this._submit.bind(this));
    this._initDatajson();
  }

  _isModified(currentData = null) {
    if (currentData === null) {
      currentData = new FormData(this.container);
    }
    for (let [key, origValue] of this.initialData.entries()) {
      if (currentData.get(key) !== origValue) {
        return true;
      }
    }
    return false;
  }

  _submit(event) {
    event.preventDefault();
    event.stopPropagation();
    // back to previous page when the form is submitted successfully


    this.container.querySelectorAll('select[required]').forEach(select => {
      if (select.value === '') {
        select.classList.add('is-invalid');
        return;
      }
    });
    this.container.classList.add('was-validated');
    if (!this.container.checkValidity()) {
        return;            
    }
    
    // Create FormData object from the current form.
    const formData = new FormData(this.container);
    if (!this._isModified(formData)) {
      this.modalAlert.update({
        msgKey: 'nochange',
        buttonTypes: ['cancel']
      });
      this.modalAlert.show();
      return;
    }
    
    // Use the form's action as the URL. It will send the POST to the same page.
    fetch(this.container.action, {
      method: 'POST',
      body: formData
    })
    .then(async response => {
      if (response.ok) {
        return response.json();
      } else {
        const errData = await response.json();
        throw new Error(errData.error || response.statusText);
      }
    })
    .then(() => {
      this.modalAlert.update({
        msgKey: 'success',
        buttonTypes: ['confirm'],
        confirmAction: () => {
          document.querySelector('a[data-dbman-toggle="prev-page"]').click();
        }
      });
      this.modalAlert.container.addEventListener('hidden.bs.modal', () => {
        document.querySelector('a[data-dbman-toggle="prev-page"]').click();
      }, { once: true });
      this.modalAlert.show(3000);
    })
    .catch(error => {
      console.error('Error submitting form:', error);
      this.modalAlert.update({
        msgKey: 'error',
        message: error.message,
        buttonTypes: ['acknowledge']
      });
      this.modalAlert.show();
    });
  }

  _initDatajson() {
    Object.entries(this.datajsonRefMap).forEach(([key, value]) => {
      const idElement = this.getValidElement(`[name="${value}"]`);
      const targetElement = this.getValidElement(`#${key}`);
      const inputElement = this.getValidElement(`#dbman-datajson-${key}`);
      const djObj = new DatajsonMJ(
        inputElement,
        targetElement, 
        idElement.value, 
        targetElement.value
      );
      idElement.addEventListener('change', async () => {
        await djObj.update(idElement.value);
      });
    });
  }
}

export { FormModifyMJ };
