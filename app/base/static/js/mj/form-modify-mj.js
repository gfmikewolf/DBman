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
    this.deleteButtons = this.getValidElements('button[data-dbman-toggle="delete-record"]')
    this.submitButtons = this.getValidElements('button[type="submit"]');
  }

  _initProperties(container, modalAlert) {
    super._initProperties && super._initProperties(container, modalAlert);
    this.initialData = new FormData(this.container);
    this.datajsonElementIdMap = fromTemplate['datajson_element_id_map'];
    if (typeof this.datajsonElementIdMap !== 'object') {
      throw new TypeError(`${this.datajsonElementIdMap} is not object.`);
    }
  }

  _initFunctions(container, modalAlert) {
    super._initFunctions && super._initFunctions(container, modalAlert);
    this.submitButtons.forEach(btn => {
      btn.addEventListener('click', this._submit.bind(this));
    });
    this.deleteButtons.forEach(btn => {
      btn.addEventListener('click', this._delete.bind(this));
    });
    this._initDatajson();
  }

  _dataModified(currentData = null) {
    if (currentData === null) {
      currentData = new FormData(this.container);
    }
    const dataModified = {}
    for (let [key, origValue] of this.initialData.entries()) {
      const currentValue = currentData.get(key)
      if ( currentValue !== origValue) {
        dataModified[key] = currentValue
      }
    }
    return dataModified;
  }

  _delete(event) {
    event.preventDefault();
    event.stopPropagation();
    const deleteButton = event.currentTarget;
    if (deleteButton.dataset.dbmanUrl) {
      this.modalAlert.update({
        msgKey: 'warning_delete',
        buttonTypes: ['confirm', 'cancel'],
        confirmAction: this._deleteRecord.bind(this, deleteButton.dataset.dbmanUrl)
      });
      this.modalAlert.show();
    }
  }

  _deleteRecord(deleteUrl) {
    fetch(deleteUrl, {
      method: 'DELETE'
    })
    .then(response => {
      if (response.ok) {
        // On successful deletion, update the alert modal and refresh the page when confirmed.
        this.modalAlert.update({
          msgKey: 'success',
          buttonTypes: ['confirm'],
          confirmAction: () => {
            document.querySelector('a[data-dbman-toggle="prev-page"]').click();
          }
        });
      } else {
        // On failure, update the alert modal with an error message.
        this.modalAlert.update({
          msgKey: 'error',
          buttonTypes: ['acknowledge']
        });
      }
    })
    .catch(() => {
      // On network error, update the alert modal with an error message.
      this.modalAlert.update({
        msgKey: 'error',
        buttonTypes: ['acknowledge']
      });
    });
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
  
    const dataModified = this._dataModified();
    if (Object.keys(dataModified).length === 0) {
      this.modalAlert.update({
        msgKey: 'nochange',
        buttonTypes: ['acknowledge']
      });
      this.modalAlert.show();
      return;
    }
    
    // Use the form's action as the URL. It will send the POST to the same page.
    fetch(this.container.action, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(dataModified)
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
    Object.entries(this.datajsonElementIdMap).forEach(([key, value]) => {
      let idElement = null;
      let idValue = `${fromTemplate['table_name']}_${key}`;
      if (value) {
        idElement = this.getValidElement(`[name="${value}"]`);
        idValue = idElement.value;
      }
      const targetElement = this.getValidElement(`#${key}`);
      const inputElement = this.getValidElement(`#dbman-datajson-${key}`);
      const djObj = new DatajsonMJ(
        inputElement,
        targetElement, 
        idValue, 
        targetElement.value
      );
      if (idElement) {
        idElement.addEventListener('change', async () => {
          await djObj.update(idElement.value);
        });
      }
    });
  }
}

export { FormModifyMJ };
