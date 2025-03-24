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
    this.datajsonRefMapContainer = this.getValidElement('div.dbman-datajson-refmap');
    this.submitButton = this.getValidElement('button[type="submit"]');
  }

  _initProperties(container, modalAlert) {
    super._initProperties && super._initProperties(container, modalAlert);
    this.datajsonRefMap = Array.from(
      this.datajsonRefMapContainer.querySelectorAll('div.dbman-item')
    ).reduce(
      (records, element) => (
        records[element.dataset.dbmanKey] = element.dataset.dbmanValue, 
        records
      ), 
      {}
    );
  }
  _initFunctions(container, modalAlert) {
    super._initFunctions && super._initFunctions(container, modalAlert);
    this.submitButton.addEventListener('click', this._submit.bind(this));
    this._initDatajson();
  }

  _submit(event) {
    event.preventDefault();
    event.stopPropagation();

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

    // Use the form's action as the URL. It will send the POST to the same page.
    fetch(this.container.action, {
      method: 'POST',
      body: formData
    })
    .then(async response => {
      if (response.ok) {
        return response.json();
      } else {
        // 解析返回的错误信息，再抛出
        const errData = await response.json();
        throw new Error(errData.error || response.statusText);
      }
    })
    .then(data => {
      this.modalAlert.update({
        msgKey: 'success',
        buttonTypes: ['confirm'],
        confirmAction: () => {
          const prevPage = document.querySelector('a[data-dbman-toggle="prev-page"]');
          if (!prevPage) {
            throw new Error('No previous page link found.');
          }
          prevPage.click();
        }
      });
      this.modalAlert.show(2000);
    })
    .catch(error => {
      // 这里可以读取 error.message 获取详细的错误信息
      console.error('Error submitting form:', error);
      this.modalAlert.update({
        msgKey: 'error',
        message: error.message,
        buttonTypes: ['acknowledge']
      });
      this.modalAlert.show(2000);
    });
  }

  _initDatajson() {
    Object.entries(this.datajsonRefMap).forEach(([key, value]) => {
      const idElement = this.getValidElement(`[name="${value}"]`);
      idElement.addEventListener('change', () => {
        const cacheKey = idElement.value;
        const targetElem = this.getValidElement(`[name="${key}"]`);
        if (this.datajsonCache[cacheKey]) {
          targetElem.innerHTML = this.datajsonCache[cacheKey].info || '';
        } else {
          fetch(`/api/get-datajson?value=${encodeURIComponent(cacheKey)}`)
            .then(response => response.json())
            .then(datajson => {
              this.datajsonCache[cacheKey] = datajson; // 保存缓存
              targetElem.innerHTML = datajson.info || '';
            })
            .catch(error => console.error('Error fetching Datajson:', error));
        }
      });
    });
  }
}

export { FormModifyMJ };
