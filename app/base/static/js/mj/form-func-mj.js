// mj/form-modify-mj.js
import { ContainerMJ } from './container-mj.js';
import { ModalAlertMJ } from './modal-alert-mj.js';

class FormFuncMJ extends ContainerMJ {
  constructor(container, modalAlert) {
    super(container, modalAlert);
  }

  _initArgs(container, modalAlert) {
    super._initArgs(container, modalAlert);
    this.modalAlert = ModalAlertMJ.getOrCreateInstance(modalAlert);
  }

  _findElements(container, modalAlert) {
    super._findElements && super._findElements(container, modalAlert);
    this.forms = this.container.querySelectorAll('form[data-dbman-toggle="db-func"]');
    this.links = this.container.querySelectorAll('button[data-dbman-toggle="db-func"]');
  }

  _initProperties(container, modalAlert) {
    super._initProperties && super._initProperties(container, modalAlert);
  }

  _initFunctions(container, modalAlert) {
    super._initFunctions && super._initFunctions(container, modalAlert);
    this.forms.forEach(form => {
      const submitBtn = this.getValidElement('button[type="submit"]', form);
      submitBtn.addEventListener('click', this._submit.bind(this));
    });
    this.links.forEach(link => {
      const url = link.dataset.dbmanUrl;
      link.addEventListener('click', () => this._execute(url, null));
    });
  }

  _submit(event) {
    event.preventDefault();
    event.stopPropagation();
    // back to previous page when the form is submitted successfully
    const form = event.target.closest('form[data-dbman-toggle="db-func"]');
    form.querySelectorAll('select[required]').forEach(select => {
      if (select.value === '') {
        select.classList.add('is-invalid');
        return;
      }
    });
    // Add Bootstrap validation class to visually indicate the form has been validated
    form.classList.add('was-validated');
    if (!form.checkValidity()) {
      return;            
    }
    this._execute(form.action, new FormData(form));
  }

  async _execute(url, inputs) {
    // Use the form's action as the URL. It will send the POST to the same page.
    const requestInit = {
      method: 'POST',
      headers: {}
    };
    if (inputs) {
      requestInit.body = inputs;  
    } else {
      requestInit.method = 'GET';
    }
    let response, responseJson;
    try {  
      response = await fetch(url, requestInit);
      responseJson = await response.json();
    } catch (error) {
      console.error('Error submitting form:', error);
      this.modalAlert.update({
        msgKey: 'error',
        message: error.message,
        buttonTypes: ['acknowledge']
      });
      this.modalAlert.show();
      return;
    }
    if (response.ok) {
      this.modalAlert.update({
        msgKey: 'success',
        message: responseJson.data,
        buttonTypes: ['acknowledge'],
      });
    } else {
      this.modalAlert.update({
        msgKey: 'error',
        message: responseJson.error,
        buttonTypes: ['acknowledge'],
      });
    }
    this.modalAlert.show(3000);
  }
}

export { FormFuncMJ };
