// app/base/static/js/scripts.js
// Version: 1.0
// Date: 2025-09-01
// Description: This file contains the main JavaScript code for the project DBMan
// Author: Xiaolong Liu

import { ModalAlert } from './modal-dbman.js';
import { Datatable } from './datatable-dbman.js';
import { FormModify } from './form-modify-dbman.js';

document.addEventListener('DOMContentLoaded', () => {
    // init bs tooltips
    const tooltipList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipList.length > 0) {
        initializeTooltips(tooltipList);
    }
    // init modules on demand
    const metaModules = document.querySelector('meta[name="modules"]');
    
    if (metaModules) {
        const strModules = metaModules.content;
        if (strModules) {
            const moduleNames = strModules.split(',');
            let alertModal;
            if (moduleNames.includes('modal-alert')) {
                alertModal = new ModalAlert('#modal-alert');
                if(!alertModal.active) {
                    console.log('Failed to initialize ModalAlert instance.');
                }
            }
            let datatable;
            if (moduleNames.includes('datatable')) {
                datatable = new Datatable('#datatable-table-main', alertModal);
                if(!datatable.active) {
                    console.log('Failed to initialize Datatable instance.');
                }
            } 
            if (moduleNames.includes('form-modify')) {
                const formModify = new FormModify('#form-modify-main', alertModal);
                if(!formModify.active) {
                    console.log('Failed to initialize FormModify instance.');
                }
            }
        }
    }
});

function initializeTooltips(tooltipList) {
    // 提示栏只在悬停时触发
    tooltipList.forEach((tooltip) => {tooltip.dataset.bsTrigger = 'hover';});
    var tooltipTriggerList = [].slice.call(tooltipList);
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}
