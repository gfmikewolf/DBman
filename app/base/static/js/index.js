// app/base/static/js/scripts.js
// Version: 1.0
// Date: 2025-09-01
// Description: This file contains the main JavaScript code for the project DBMan
// Author: Xiaolong Liu

import { ModalAlertMJ } from './mj/modal-alert-mj.js';
import { DatatableMJ } from './mj/datatable-mj.js';
import { FormModifyMJ } from './mj/form-modify-mj.js';
import { DBFuncMJ } from './mj/db-func-mj.js';
import { SelectpickerMJ } from './mj/selectpicker-mj.js';

document.addEventListener('DOMContentLoaded', () => {
  // init bs tooltips
  initTooltips();
  initCopyButtons();

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
      if (moduleNames.includes('db-func')) {
        formFunc = new DBFuncMJ('#db-func-main', modalAlert);
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

function initCopyButtons() {
  const copyButtons = document.querySelectorAll('[data-dbman-toggle="copy"]');
  copyButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.dbmanTarget;
      const msg = btn.dataset.dbmanMsg;
      const text = document.getElementById(target).textContent.trim();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
          showTemporaryTooltip(btn, msg);
        });
      }
    });
  });
}

function showTemporaryTooltip(el, message) {
  el.setAttribute('title', message);
  // 手动触发 bootstrap tooltip
  const tooltip = new bootstrap.Tooltip(el, { trigger: 'manual', placement: 'top' });
  tooltip.show();
  // 鼠标移出时隐藏
  const hideHandler = () => {
    tooltip.hide();
    el.removeEventListener('mouseleave', hideHandler);
  };
  el.addEventListener('mouseleave', hideHandler);
  // 2 秒后自动隐藏
  setTimeout(() => tooltip.hide(), 2000);
}
