import { ModalDatatableConfig } from "./modal-dbman.js";
import { ModalAlert } from "./modal-dbman.js";

/** 
 * Datatable displays data in a structured style.
 * 
 * Constructor Datatable(selector, alertModal)
 *   - Creates and initializes all datatable-related objects.
 *   - Attributes:
 *       active: Boolean flag; true if initialization is successful, false otherwise.
 *       table: DOM element for the <table>.
 *       name: Identifier extracted from the selector (e.g. "table-main" in "datatable-table-main").
 *       modalConfig: Instance of ModalDatatableConfig for configuring columns.
 *
 * @class Datatable
 * @param {string} selector - Format: 'datatable-{type}-{name}', e.g. 'datatable-table-main'
 * @param {ModalAlert} alertModal - An instance of ModalAlert for displaying alerts.
 */
export class Datatable {
    constructor(selector, alertModal) {
        // Initially set active to true. If any initialization error occurs,
        // set active to false and return early.
        this.active = true;

        // Validate the alertModal parameter
        if (!alertModal || !(alertModal instanceof ModalAlert) || !alertModal.active) {
            console.log('Failed to initialize alert modal');
            this.active = false;
            return;
        }
        this.alertModal = alertModal;

        // Get the table element from the DOM
        this.table = document.querySelector(selector);
        if (!this.table) {
            console.log('Failed to initialize datatable');
            this.active = false;
            return;
        }

        // Extract the datatable name from the selector
        this.name = selector.substring(selector.lastIndexOf('-') + 1);
        if (!this.name) {
            console.log('Invalid datatable id. Should be ...-name');
            this.active = false;
            return;
        }

        // Initialize check-all checkbox and individual checkboxes
        this.cboxCheckAll = this.table.querySelector('[data-dbman-toggle="check-all"]');
        if (!this.cboxCheckAll) {
            console.log('Failed to initialize check all checkbox');
            this.active = false;
            return;
        }
        this.cboxCheckItems = this.table.querySelectorAll('[data-dbman-toggle="check-item"]');

        // Initialize search components
        this.searchBtngroup = document.querySelector('#datatable-search-' + this.name);
        if (!this.searchBtngroup) {
            console.log('Failed to initialize search button group');
            this.active = false;
            return;
        }
        this.searchInput = this.searchBtngroup.querySelector('[type="search"]');
        if (!this.searchInput) {
            console.log('Failed to initialize search input');
            this.active = false;
            return;
        }
        this.searchBtn = this.searchBtngroup.querySelector('[data-dbman-toggle="search"]');
        if (!this.searchBtn) {
            console.log('Failed to initialize search button');
            this.active = false;
            return;
        }
        this.searchNoFilterBtn = this.searchBtngroup.querySelector('[data-dbman-toggle="no-filter"]');
        if (!this.searchNoFilterBtn) {
            console.log('Failed to initialize no filter button');
            this.active = false;
            return;
        }

        // Initialize CSV download button and batch delete button
        this.btnDownloadCSV = document.querySelector('#datatable-downloadCSV-' + this.name);
        if (!this.btnDownloadCSV) {
            console.log('Failed to initialize download CSV button');
            this.active = false;
            return;
        }
        this.btnBatchDelete = document.querySelector('#datatable-batch-delete-' + this.name);
        if (!this.btnBatchDelete) {
            console.log('Failed to initialize batch delete button');
            this.active = false;
            return;
        }

        // Initialize individual delete buttons from the table rows
        this.deleteBtns = this.table.querySelectorAll('[data-dbman-toggle="delete-record"]');

        // Initialize the modal for datatable configuration
        this.modalConfig = new ModalDatatableConfig('#datatable-modal-config-' + this.name, this.table);
        if (!this.modalConfig.active) {
            console.log('Failed to initialize datatable config modal');
            this.active = false;
            return;
        }

        this.curSearchQuery = '';

        // Initialize all event handler modules
        this._initSearch();
        this._initCheckAll();
        this._initCheckItems();
        this._initRowClickCheck();
        this._initDownloadCSV();
        this._initDeleteRecord();

        // If all initialization steps pass, active remains true.
    }

    // Set up "check all" functionality: when the main checkbox changes, update all item checkboxes.
    _initCheckAll() {
        this.cboxCheckAll.addEventListener('change', () => {
            this.cboxCheckItems.forEach(item => {
                item.checked = this.cboxCheckAll.checked;
            });
        });
    }

    // When individual checkboxes change, determine if the "check all" should be checked.
    _initCheckItems() {
        this.cboxCheckItems.forEach(item => {
            item.addEventListener('change', () => {
                const allChecked = Array.from(this.cboxCheckItems).every(item => item.checked);
                this.cboxCheckAll.checked = allChecked;
            });
        });
    }

    // Toggle checkbox state when a row is clicked.
    _initRowClickCheck() {
        const dataCells = this.table.querySelectorAll('[data-dbman-sn]');
        dataCells.forEach(dataCell => dataCell.addEventListener('click', (e) => {
            const targetRow = e.target.closest('tr');
            if (targetRow) {
                const checkbox = targetRow.querySelector('[data-dbman-toggle="check-item"]');
                if (checkbox) {
                    // Toggle the checkbox's checked state
                    checkbox.checked = !checkbox.checked;
                    // Dispatch a change event to update "check all" status if needed
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

    // Set up the CSV download functionality.
    _initDownloadCSV() {
        this.btnDownloadCSV.addEventListener('click', () => {
            const headRow = this.table.querySelector('thead tr');
            const dataRows = this.table.querySelectorAll('tbody tr:not(.d-none)');

            // Extract header data from the visible table headers
            const headers = [];
            headRow.querySelectorAll('th[data-dbman-sn]:not(.d-none)').forEach(th => {
                if (th.dataset.dbmanData) {
                    headers.push(th.dataset.dbmanData.trim());
                } else {
                    headers.push(th.textContent.trim());
                }
            });

            // Extract content from each data row
            const rows = [];
            dataRows.forEach(row => {
                const rowData = [];
                row.querySelectorAll('td[data-dbman-sn]:not(.d-none)').forEach(td => {
                    if (td.dataset.dbmanData) {
                        rowData.push(td.dataset.dbmanData.trim());
                    } else {
                        rowData.push(td.textContent.trim());
                    }
                });
                rows.push(rowData);
            });

            // Create a CSV string from header and row data
            let csvContent = headers.join(',') + '\n';
            rows.forEach(row => {
                csvContent += row.join(',') + '\n';
            });
            // Prepend BOM to support Excel encoding
            csvContent = '\uFEFF' + csvContent;

            // Create a Blob object with the CSV data and trigger a download
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'data.csv';
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }

    // Initialize the delete record functionality
    _initDeleteRecord() {
        this.deleteBtns.forEach(deleteBtn => {
            deleteBtn.addEventListener('click', () => {
                // Get the closest table row for the delete button
                const tr = deleteBtn.closest('tr');
                // Get headers from visible table header cells
                const ths = this.table.querySelectorAll('th[data-dbman-sn]:not(.d-none)');
                const headers = Array.from(ths).map(th => {
                    return th.dataset.dbmanData ? th.dataset.dbmanData : th.textContent.trim();
                });
                // Get all visible cells from the selected row
                const tds = tr.querySelectorAll('td[data-dbman-sn]:not(.d-none)');
                let message = '<div class="container-fluid mt-3">';
                // Build a message content by iterating over each cell
                tds.forEach(td => {
                    message += '<div class="row border-bottom">';
                    const content = td.dataset.dbmanData ? td.dataset.dbmanData.trim() : td.innerText.trim();
                    message += '<div class="col fw-bold">' + headers[0] + ':</div> <div class="col">' + content + '</div>';
                    message += '</div>';
                    // Remove the first header after it has been used
                    headers.shift();
                });
                message += '</div>';

                // If a delete URL is provided, update the alert modal and show it
                if (deleteBtn.dataset.dbmanUrl) {
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

    // Sends a DELETE request to the given deleteUrl and updates the alert modal based on the response.
    deleteRecord(deleteUrl) {
        if (this.active && this.alertModal.active) {
            fetch(deleteUrl, {
                method: 'DELETE'
            })
            .then(response => {
                if (response.ok) {
                    // On successful deletion, update the alert modal and refresh the page when confirmed.
                    this.alertModal.update({
                        msgKey: 'success',
                        buttonTypes: ['confirm'],
                        confirmAction: () => {
                            window.location.reload();
                        }
                    });
                } else {
                    // On failure, update the alert modal with an error message.
                    this.alertModal.update({
                        msgKey: 'error',
                        buttonTypes: ['acknowledge']
                    });
                }
            })
            .catch(error => {
                // On network error, update the alert modal with an error message.
                this.alertModal.update({
                    msgKey: 'error',
                    buttonTypes: ['acknowledge']
                });
            });
        }
    }
}
