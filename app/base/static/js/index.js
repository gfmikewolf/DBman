// app/base/static/js/scripts.js
// Version: 1.0
// Date: 2025-09-01
// Description: This file contains the main JavaScript code for the project DBMan
// Author: Xiaolong Liu

import { ModalAlertMJ } from './mj/modal-alert-mj.js';
import { DatatableMJ } from './mj/datatable-mj.js';
import { FormModifyMJ } from './mj/form-modify-mj.js';
import { FormFuncMJ } from './mj/form-func-mj.js';
import { SelectpickerMJ } from './mj/selectpicker-mj.js';

document.addEventListener('DOMContentLoaded', () => {
  // init bs tooltips
  initTooltips();

  // init selectpickers
  SelectpickerMJ.getOrCreateAll();

  // init modules on demand
  initModules();
});

function initModules() {
  const metaModules = document.querySelector('meta[name="modules"]');
  
  if (metaModules) {
    const strModules = metaModules.content.trim();
    if (strModules) {
      const moduleNames = strModules.split(',');
      let modalAlert, datatable, formModify, formFunc;
      if (moduleNames.includes('modal-alert')) {
        modalAlert = new ModalAlertMJ('#dbman-alert-main');
      }
      if (moduleNames.includes('datatable')) {
        datatable = new DatatableMJ('main', modalAlert);
      } 
      if (moduleNames.includes('form-modify')) {
        formModify = new FormModifyMJ('#dbman-modify-main', modalAlert);
      }
      if (moduleNames.includes('form-func')) {
        formFunc = new FormFuncMJ('#dbman-func-main', modalAlert);
      }
    }
  }
}

function initTooltips() {
  const tooltipList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipList.forEach((tooltip) => {
    tooltip.dataset.bsTrigger = 'hover';
  });
  const tooltipTriggerList = [].slice.call(tooltipList);
  tooltipTriggerList.map((tooltipTriggerEl) => {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });
}
