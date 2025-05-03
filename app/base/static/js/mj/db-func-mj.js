// mj/db-func-mj.js
import { ContainerMJ } from './container-mj.js';
import { ModalAlertMJ } from './modal-alert-mj.js';
import { SelectpickerMJ } from './selectpicker-mj.js';

class DBFuncMJ extends ContainerMJ {
  constructor(container, modalAlert) {
    super(container, modalAlert);
  }

  _initArgs(container, modalAlert) {
    super._initArgs(container, modalAlert);
    this.modalAlert = ModalAlertMJ.getOrCreateInstance(modalAlert);
  }

  _findElements(container, modalAlert) {
    super._findElements && super._findElements(container, modalAlert);
    this.buttons = this.container.querySelectorAll('button[data-dbman-toggle="db-func"]');
    this.formContainer = document.getElementById('db-func-forms');
  }

  _initProperties(container, modalAlert) {
    super._initProperties && super._initProperties(container, modalAlert);
    this.funcInfo = fromTemplate['db_table_funcs'];
  }

  _initFunctions(container, modalAlert) {
    super._initFunctions && super._initFunctions(container, modalAlert);
    this.buttons.forEach((btn) => {
      const func_name = btn.dataset.dbmanName;
      console.log();
      if (Object.keys(this.funcInfo[func_name]['input_types']).length===0) {
        btn.addEventListener('click', () => {
          this._execute(btn.dataset.dbmanUrl, null)
        });
      } else {
        btn.addEventListener('click', () => {
          this._showForm(btn.dataset.dbmanName, btn.dataset.dbmanUrl);
        });
      }
    });
  }

  _showForm(func_name) {
    let form = this.formContainer.querySelector(`[data-dbman-target="${func_name}"`);
    this.modalAlert.update({
      msgKey: 'input_form',
      buttonTypes: ['acknowledge']
    });
    this.modalAlert.modalBody.appendChild(form.cloneNode(true));
    SelectpickerMJ.getOrCreateAll();
    form = this.modalAlert.modalBody.querySelector('form');
    form.querySelector('button[type="submit"]').addEventListener('click', (e)=> {
      e.preventDefault();
      e.stopPropagation();
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
    });
    this.modalAlert.show();
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
    window.location.reload(true);
  }
}

export { DBFuncMJ };
