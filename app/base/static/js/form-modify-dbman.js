import { ModalAlert } from './modal-dbman.js';
export class FormModify {
    constructor(selector, alertModal) {
        this.active = true;
        this.alertModal = alertModal;
        if (!alertModal || !(alertModal instanceof ModalAlert) || !alertModal.active ) {
            console.log('Failed to initialize ModalAlert instance.');
            this.active = false;
            return;
        }
        this.form = document.querySelector(selector);
        if (!this.form) {
            console.log('Container not found for selector:', selector);
            this.active = false;
            return;
        }
        // Use "this.form" instead of "form" to refer to the selected element.
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (!submitButton) {
            console.log('No submit button found in the form.');
            this.active = false;
            return;
        }
        submitButton.addEventListener('click', this._submit.bind(this));
    }
    _submit(event) {
        event.preventDefault();
        event.stopPropagation();       
        // Check if the form is valid.
        this.form.classList.add('was-validated');
        if (!this.form.checkValidity()) {
            return;            
        }
        
        // Create FormData object from the current form.
        const formData = new FormData(this.form);

        // Use the form's action as the URL. It will send the POST to the same page.
        fetch(this.form.action, {
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
            console.log('Form submitted successfully.');
            this.alertModal.update({
                msgKey: 'success',
                buttonTypes: ['confirm'],
                confirmAction: () => {
                    const prevPage = document.querySelector('a[data-dbman-toggle="prev-page"]');
                    if (!prevPage) {
                        console.log('No previous page link found.');
                        throw new Error('No previous page link found.');
                    }
                    prevPage.click();
                }
            });
            this.alertModal.show();
        })
        .catch(error => {
            // 这里可以读取 error.message 获取详细的错误信息
            console.error('Error submitting form:', error);
            this.alertModal.update({
                msgKey: 'error',
                message: error.message,
                buttonTypes: ['acknowledge']
            });
            this.alertModal.show();
        });
    }
}