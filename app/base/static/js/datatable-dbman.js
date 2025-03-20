import { ModalDatatableConfig } from "./modal-dbman.js";
import { ModalAlert } from "./modal-dbman.js";
/** 
 * Datatable to exhit the data in a structured style
 * - constructor Datatable(selector)
 *   - create all objects related to datatable
 *   - attributes:
 *     - active: true is construction is successful else false
 *     - table: <table> DOM element
 *     - name: identifier that relates to all elements of datatable
 *     - modalConfig: modal instance of table config
 * @class Datatable
 * @param {string} selector - 'datatable-{type}-{name}', e.g. 'datatable-table-main'
 */
export class Datatable {
    constructor(selector, alertModal) {
        this.active = false;
        // Initialize all attributes
        if (!alertModal || !(alertModal instanceof ModalAlert) || !alertModal.active) {
            console.log('Failed to initialize alert modal');
            return;
        }
        this.alertModal = alertModal;
        this.table = document.querySelector(selector);
        if (!this.table) {
            console.log('Failed to initialize datatable');
            return;
        }
        this.name = selector.substring(selector.lastIndexOf('-') + 1);
        if (!this.name) {
            console.log('Invalid datatable id. Should be ...-name');
            return;
        }
        this.cboxCheckAll = this.table.querySelector('[data-dbman-toggle="check-all"]');
        if (!this.cboxCheckAll) {
            console.log('Failed to initialize check all checkbox');
            return;
        }
        this.cboxCheckItems = this.table.querySelectorAll('[data-dbman-toggle="check-item"]');
        this.searchBtngroup = document.querySelector('#datatable-search-' + this.name);
        if (!this.searchBtngroup) {
            console.log('Failed to initialize search button group');
            return;
        }
        this.searchInput = this.searchBtngroup.querySelector('[type="search"]');
        if (!this.searchInput) {
            console.log('Failed to initialize search input');
            return;
        }
        this.searchBtn = this.searchBtngroup.querySelector('[data-dbman-toggle="search"]');
        if (!this.searchBtn) {
            console.log('Failed to initialize search button');
            return;
        }
        this.searchNoFilterBtn = this.searchBtngroup.querySelector('[data-dbman-toggle="no-filter"]');
        if (!this.searchNoFilterBtn) {
            console.log('Failed to initialize no filter button');
            return;
        }
        this.btnDownloadCSV = document.querySelector('#datatable-downloadCSV-' + this.name);
        if (!this.btnDownloadCSV) {
            console.log('Failed to initialize download CSV button');
            return;
        }
        this.btnBatchDelete = document.querySelector('#datatable-batch-delete-' + this.name); 
        if (!this.btnBatchDelete) {
            console.log('Failed to initialize batch delete button');
            return;
        }
        this.deleteBtns = this.table.querySelectorAll('[data-dbman-toggle="delete-record"]');
        this.modalConfig = new ModalDatatableConfig('#datatable-modal-config-' + this.name, this.table);
        if (!this.modalConfig.active) {
            console.log('Failed to initialize datatable config modal');
            return;
        }
        this.curSearchQuery = '';

        // Initialize all event function modules
        this._initSearch();
        this._initCheckAll();
        this._initCheckItems();
        this._initRowClickCheck();
        this._initDownloadCSV();
        this._initDeleteRecord();
        this.active = true;
    }
    _initCheckAll() {
        this.cboxCheckAll.addEventListener('change', () => {
            this.cboxCheckItems.forEach(item => {
                item.checked = this.cboxCheckAll.checked;
            });
        });
    }
    _initCheckItems() {
        this.cboxCheckItems.forEach(item => {
            item.addEventListener('change', () => {
                const allChecked = Array.from(this.cboxCheckItems).every(item => item.checked);
                this.cboxCheckAll.checked = allChecked;
            });
        });
    }
    _initRowClickCheck() {
        const dataCells = this.table.querySelectorAll('[data-dbman-sn]');
        dataCells.forEach(dataCell => dataCell.addEventListener('click', (e) => {
            const target = e.target.closest('tr');
            if (target) {
                const checkbox = target.querySelector('[data-dbman-toggle="check-item"]');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked; // 切换复选框的选中状态
                    const event = new Event('change', { bubbles: true });
                    checkbox.dispatchEvent(event);
                }
            }
        }));
    }
    _initSearch() {
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchBtn.click();
            };
        });
        this.searchNoFilterBtn.addEventListener('click', () => {
            this.searchInput.value = '';
            this.searchBtn.click();
        });
        this.searchBtn.addEventListener('click', () => {
            const searchText = this.searchInput.value;
            const dataRows = this.table.querySelectorAll('tbody tr');
            if(searchText != this.curSearchQuery) {
                dataRows.forEach((dataRow) => {
                    var match = false || (searchText === '');
                    if(match === false) {
                        const dataCells = dataRow.querySelectorAll('td[data-dbman-sn]');
                        for(const dataCell of dataCells) {
                            if(dataCell.textContent.toLowerCase().includes(searchText.toLowerCase())) {
                                match = true;
                                break;
                            }
                        }; 
                    }
                    if(match === true) {
                        dataRow.classList.remove('d-none');
                    } else {
                        dataRow.classList.add('d-none');
                    }
                });  
                this.curSearchQuery = searchText;
            }
            if(this.curSearchQuery === '') {
                this.searchNoFilterBtn.classList.add('d-none');
            } else {
                this.searchNoFilterBtn.classList.remove('d-none');
            }
        });
    }
    _initDownloadCSV() {
        this.btnDownloadCSV.addEventListener('click', () => {
            const headRow = this.table.querySelector('thead tr');
            const dataRows = this.table.querySelectorAll('tbody tr:not(.d-none)');
        
            // Extract header data
            const headers = [];
            headRow.querySelectorAll('th[data-dbman-sn]:not(.d-none)').forEach(th => {
                if(th.dataset.dbmanData) {
                    headers.push(th.dataset.dbmanData.trim());
                } else {
                    headers.push(th.textContent.trim());
                }
            });
        
            // Extract data row content
            const rows = [];
            dataRows.forEach(row => {
                const rowData = [];
                row.querySelectorAll('td[data-dbman-sn]:not(.d-none)').forEach(td => {
                    if(td.dataset.dbmanData) {
                        rowData.push(td.dataset.dbmanData.trim());
                    } else {
                        rowData.push(td.textContent.trim());
                    }
                });
                rows.push(rowData);
            });
        
            // Create CSV string
            let csvContent = headers.join(',') + '\n';
            rows.forEach(row => {
                csvContent += row.join(',') + '\n';
            });
            csvContent = '\uFEFF' + csvContent;

            // Create a Blob object with the CSV data
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        
            // Create a link element to trigger the download
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'data.csv';
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
        
            // Trigger the download
            link.click();
        
            // Clean up
            document.body.removeChild(link);
        });
    }
    _initDeleteRecord() {
        this.deleteBtns.forEach(deleteBtn => {
            
            deleteBtn.addEventListener('click', () => {
                const tr = deleteBtn.closest('tr');
                const ths = this.table.querySelectorAll('th[data-dbman-sn]:not(.d-none)');
                const headers = Array.from(ths).map(th => th.dataset.dbmanData ? th.dataset.dbmanData : th.textContent.trim());
                const tds = tr.querySelectorAll('td[data-dbman-sn]:not(.d-none)');
                let message = '<div class="container-fluid mt-3">';
                tds.forEach(td => {
                    message += '<div class="row">';
                    const content = td.dataset.dbmanData ? td.dataset.dbmanData.trim() : td.innerText.trim();
                    message += headers[0] + ': ' + content;
                    message += '</div>';
                    headers.shift();
                });
                message += '</div>';

                if(deleteBtn.dataset.dbmanUrl) {
                    this.alertModal.update({
                        msgKey: 'warning_delete',
                        message: message,
                        buttonTypes: ['confirm', 'cancel'],
                        confirmAction: this.deleteRecord.bind(this, deleteBtn.dataset.dbmanUrl)
                    });
                    this.alertModal.show();
                }
            });
        });
    }

    deleteRecord(deleteUrl) {
        if(this.active && this.alertModal.active) {
            fetch(deleteUrl, {
                method: 'DELETE'
            })
            .then(response => {
                if(response.ok) {
                    this.alertModal.update({
                        msgKey: 'success',
                        buttonTypes: ['confirm'],
                        confirmAction: () => {
                            window.location.reload();
                        }
                    });
                } else {
                    this.alertModal.update({
                        msgKey: 'error',
                        buttonTypes: ['acknowledge']
                    });
                }
            })
            .catch(error => {
                this.alertModal.update({
                    msgKey: 'error',
                    buttonTypes: ['acknowledge']
                });
            });
        }
    }    
}
