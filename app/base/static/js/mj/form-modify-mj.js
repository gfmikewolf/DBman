// mj/form-modify-mj.js
import { ContainerMJ } from './container-mj.js';
import { ModalAlertMJ } from './modal-alert-mj.js';

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
    this.polybase_keys = fromTemplate['polybase_keys'];
    this.dependency_keys = fromTemplate['dependency_keys'];
    this.polymorphic_key = fromTemplate['polymorphic_key'];
    this.initialData = JSON.parse(fromTemplate['original_data']);
    this.modify_url = fromTemplate['modify_url'];
    this.pks = fromTemplate['pks'];
  }

  _initFunctions(container, modalAlert) {
    super._initFunctions && super._initFunctions(container, modalAlert);
    this.submitButtons.forEach(btn => {
      btn.addEventListener('click', this._submit.bind(this));
    });
    this.deleteButtons.forEach(btn => {
      btn.addEventListener('click', this._delete.bind(this));
    });
    this.dependency_keys.forEach(dk => {
      const dkEl = this.container.querySelector(`[name="${dk}"]`);
      if (dkEl) {
        dkEl.addEventListener('change', () => {
          const params = new URLSearchParams();
          const formData = new FormData(this.container);
          for (const [key, value] of formData.entries()) {
            // dk不是多态键的话，所有的表单键不会变化，可以传递参数
            // polybase_keys无键时，说明不是多态类，表单键不会变化，可以传递参数
            // key在多态基类键内，可以传递参数
            if (dk !== this.polymorphic_key && (this.polybase_keys.length === 0 || this.polybase_keys.includes(key) || this.dependency_keys.includes(key))) {
              if (
                value !== null 
                && value !== '' 
                && (
                  Object.keys(this.initialData) === 0
                  || (
                    key in this.initialData &&
                    value != this.initialData[key]
                  )
                  || !(key in this.initialData)
                )
              ) {
                params.set(key, value);
              }
            }
          }
          const table_name = formData.get(this.polymorphic_key).toLowerCase();
          const baseUrl = `${this.modify_url}/${table_name}/${this.pks}`;
          const queryString = params.toString();
          const url = queryString ? `${baseUrl}?${queryString}` : baseUrl;
          window.location.href = url;
        });
      }
    });
  }

  _dataModified(currentData = null) {
    if (currentData === null) {
      currentData = new FormData(this.container);
    }
    const dataModified = {}
    for (let [key, value] of currentData.entries()) {
      const originalValue = this.initialData[key];
      if ( (value || originalValue) && value !== originalValue) {
        dataModified[key] = value
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
    if (this.pks !== '_new') {
      const dataModified = this._dataModified();
      if (Object.keys(dataModified).length === 0) {
        this.modalAlert.update({
          msgKey: 'nochange',
          buttonTypes: ['acknowledge']
        });
        this.modalAlert.show();
        return;
      }
    }
    // Use the form's action as the URL. It will send the POST to the same page.
    fetch(this.container.action, {
      method: 'POST',
      headers: {},
      body: new FormData(this.container)
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
}

export { FormModifyMJ };
