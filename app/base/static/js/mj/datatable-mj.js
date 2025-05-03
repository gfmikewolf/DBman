// mj/datatables-mj.js
import { ContainerMJ } from "./container-mj.js";
import { ModalAlertMJ } from "./modal-alert-mj.js";
import { ModalMJ } from "./modal-mj.js";
import { DraggerMJ } from "./dragger-mj.js";

class DatatableMJ extends ContainerMJ {
  constructor(name, modalAlert) {
    super(name, modalAlert, '#dbman-datatable-' + name);
  }

  _initArgs(name, modalAlert, selector) {
    super._initArgs && super._initArgs(selector, modalAlert);
    this.identifier = name;
    this.modalAlertElement = modalAlert;
    this.modalAlert = ModalAlertMJ.getOrCreateInstance(modalAlert);
  }

  _findElements(name, modalAlert, selector) {
    super._findElements && super._findElements(selector, modalAlert);
    this.table = this.getValidElement('table.dbman-datatable-table');
    this.cboxCheckAll = this.getValidElement('[data-dbman-toggle="check-all"]', this.table);
    this.cboxCheckItems = this.table.querySelectorAll('[data-dbman-toggle="check-item"]');
    this.searchBtngroup = this.getValidElement('.dbman-datatable-search');
    this.searchInput = this.getValidElement('[type="search"]', this.searchBtngroup);
    this.searchBtn = this.getValidElement('[data-dbman-toggle="search"]', this.searchBtngroup);
    this.searchNoFilterBtn = this.getValidElement('[data-dbman-toggle="no-filter"]', this.searchBtngroup);
    this.btnDownloadCSV = this.getValidElement('[data-dbman-toggle="download-csv"]');
    this.btnBatchDelete = this.getValidElement('[data-dbman-toggle="batch-delete"]');
    this.deleteBtns = this.table.querySelectorAll('[data-dbman-toggle="delete-record"]');
    this.modalConfig = ModalDatatableConfig.getOrCreateInstance('#dbman-datatable-config-' + name, this.table);
  }

  _initProperties(name, modalAlert, selector) {
    super._initProperties && super._initProperties(selector, modalAlert);
    this.curSearchQuery = '';
  }

  _initFunctions(name, modalAlert, selector) {
    super._initFunctions && super._initFunctions(selector, modalAlert);
    this._initRowCheck();
    this._initSearch();
    this._initDownloadCSV();
    this._initDeleteRecord();
    this._initSorting();
  }

  _initRowCheck() {
    this._initCheckAll();
    this._initCheckItems();
    this._initRowClickCheck();
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

  _initDownloadCSV() {
    // 实现CSV字段转义，若字段内包含逗号、换行符或双引号，则包装在双引号内，
    // 并将内部的双引号替换为两个连续的双引号
    function escapeCSVField(field) {
      if (field === null || field === undefined) return '';
      field = String(field);
      // 如果字段包含逗号、换行或双引号，则需要转义
      if (field.search(/("|,|\n)/g) !== -1) {
        field = field.replace(/"/g, '""');
        field = `"${field}"`;
      }
      return field;
    }

    this.btnDownloadCSV.addEventListener('click', () => {
      const headRow = this.table.querySelector('thead tr');
      const dataRows = this.table.querySelectorAll('tbody tr:not(.d-none)');

      // Extract header data from the visible table headers
      const headers = [];
      headRow.querySelectorAll('th[data-dbman-sn]:not(.d-none)').forEach(th => {
        let headerText = th.dataset.dbmanData ? th.dataset.dbmanData.trim() : th.textContent.trim();
        headers.push(escapeCSVField(headerText));
      });

      // Extract content from each data row
      const rows = [];
      dataRows.forEach(row => {
        const rowData = [];
        row.querySelectorAll('td[data-dbman-sn]:not(.d-none)').forEach(td => {
          let cellText = ""
          const aTag = td.querySelector('a');
          if (aTag) {
            cellText = td.innerHTML.replace(/<a[^>]*>(.*?)<\/a>/g, '$1').trim();
          } else {
            cellText = td.textContent.trim();
          }
          rowData.push(escapeCSVField(cellText));
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

  _initDeleteRecord() {
    this.deleteBtns.forEach(deleteBtn => {
      deleteBtn.addEventListener('click', () => {
        // Get the closest parent element table row for the delete button
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
          this.modalAlert.update({
            msgKey: 'warning_delete',
            message: message,
            buttonTypes: ['confirm', 'cancel'],
            confirmAction: this.deleteRecord.bind(this, deleteBtn.dataset.dbmanUrl)
          });
          this.modalAlert.show();
        }
      });
    });
  }

  // Sends a DELETE request to the given deleteUrl and updates the alert modal based on the response.
  deleteRecord(deleteUrl) {
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
            window.location.reload();
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

  // 在 DatatableMJ 类中增加排序初始化方法
  _initSorting() {
    // 选择所有带 data-dbman-sn 属性且未隐藏的表头单元格
    const headers = this.table.querySelectorAll('th[data-dbman-sn]:not(.d-none)');
    headers.forEach((header) => {
      // 设置鼠标样式表示可点击
      header.style.cursor = 'pointer';
      // 初始排序顺序默认为升序
      header.dataset.sortOrder = '';
      header.addEventListener('click', () => {
        // 切换排序顺序
        const currentSort = header.dataset.sortOrder;
        const newSort = currentSort === 'asc' ? 'desc' : 'asc';
        header.dataset.sortOrder = newSort;
        
        const colId = header.dataset.dbmanSn;
        const tbody = this.table.querySelector('tbody');
        // 获取 tbody 内所有行作为数组
        const rows = Array.from(tbody.querySelectorAll('tr'));
        // 对行进行排序
        rows.sort((a, b) => {
          const cellA = a.querySelector(`td[data-dbman-sn="${colId}"]`);
          const cellB = b.querySelector(`td[data-dbman-sn="${colId}"]`);
          const valA = cellA ? cellA.textContent.trim() : '';
          const valB = cellB ? cellB.textContent.trim() : '';
          
          // 如果两边都是 ISO 日期格式，则直接用字母（字典）排序
          const isoDatePattern = /^\d{4}-\d{2}-\d{2}$/;
          if (isoDatePattern.test(valA) && isoDatePattern.test(valB)) {
            return newSort === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
          }
          
          // 尝试转成数字比较
          const numA = parseFloat(valA.replace(/,/g, ''));
          const numB = parseFloat(valB.replace(/,/g, ''));
          if (!isNaN(numA) && !isNaN(numB)) {
            return newSort === 'asc' ? numA - numB : numB - numA;
          } else {
            return newSort === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
          }
        });
        // 清空 tbody 并追加排序后的行
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
      });
    });
  }
}

class ModalDatatableConfig extends ModalMJ {
    constructor(container, table) {
      super(container, table);
    }

    _initArgs(container, table) {
      super._initArgs(container, table);
      this.table = this.getValidElement(table);
    }

    _findElements(container, table) {
      super._findElements && super._findElements(container, table);
      this.headerListgroup = this.getValidElement('.list-group');
      // Check if there are any list items with data-dbman-sn
      const headerLis = this.getValidElements('li[data-dbman-sn]', this.headerListgroup);
      const headerCboxes = this.getValidElements('li[data-dbman-sn] [type="checkbox"]', this.headerListgroup);
      this._btnSaveChanges = this.getValidElement('[data-dbman-toggle="save-changes"]');
      this._btnRestoreDefault = this.getValidElement('[data-dbman-toggle="restore-default"]');
      this._dragger = new DraggerMJ(this.headerListgroup, 'vertical');    
    }

    _initProperties(container, table) {
      super._initProperties && super._initFunctions(container, table);
      // Save original checkbox order and checked states
      this._listOriginalStates = this._saveListStates();
      this._listInitialStates = [];
      // When _saveChanges is true, hiding the modal will not restore the initial states
      this._saveChanges = false;
    }

    _initFunctions(container, table) {
      super._initFunctions && super._initFunctions(container, table);
      // Add extra handler to save current checkbox order and states when showing the modal
      this.container.addEventListener('show.bs.modal', this._extraHandlerSaveInitialStates.bind(this));
      // Add extra handler to restore initial checkbox order and states when hiding the modal
      this.container.addEventListener('hide.bs.modal', this._extraHandlerRestoreInitialStates.bind(this));
      // Add handler to save changes when clicking the Save Changes button
      this._btnRestoreDefault.addEventListener('click', this._handlerRestoreDefault.bind(this));
      this._btnSaveChanges.addEventListener('click', this._handlerSaveChanges.bind(this));
    }

    _saveListStates() {
      const liStates = [];
      this.headerListgroup.querySelectorAll('li[data-dbman-sn]').forEach((li) => {
        const cb = li.querySelector('[type="checkbox"]');
        const liState = [li.dataset.dbmanSn, cb.checked];
        liStates.push(liState);
      });
      return liStates;
    }

    _restoreListStates(listStates) {
      listStates.forEach((listState) => {
        const li = this.headerListgroup.querySelector('li[data-dbman-sn="' + listState[0] + '"]');
        const cb = li.querySelector('[type="checkbox"]');
        cb.checked = listState[1];
        this.headerListgroup.appendChild(li);
      });
    }

    _extraHandlerSaveInitialStates() {
      this._listInitialStates = this._saveListStates();
    }

    _extraHandlerRestoreInitialStates() {
      if (this._saveChanges) {
          this._saveChanges = false;
          return;
      }
      this._restoreListStates(this._listInitialStates);
    }

    _handlerSaveChanges() {
      const theadRow = this.getValidElement('thead tr', this.table);
      const tbodyRows = this.table.querySelectorAll('tbody tr');
      this.headerListgroup.querySelectorAll('li[data-dbman-sn]').forEach(li => {
        const cb = this.getValidElement('[type="checkbox"]', li);
        const colNum = li.dataset.dbmanSn;
        const th = this.getValidElement('th[data-dbman-sn="' + colNum + '"]', this.table);
        const tds = this.table.querySelectorAll('td[data-dbman-sn="' + colNum + '"]');
          
        // Move the selected header column in the data table
        theadRow.appendChild(theadRow.querySelector('th[data-dbman-sn="' + colNum + '"]'));
        tbodyRows.forEach((row) => {
          const td = this.getValidElement('td[data-dbman-sn="' + colNum + '"]', row);
          row.appendChild(td);
        });

          // Show the column in the data table if checkbox is checked
        if (cb.checked) {
            th.classList.remove('d-none');
            tds.forEach((cell) => cell.classList.remove('d-none'));
        // Hide the column if checkbox is not checked
        } else {
            th.classList.add('d-none');
            tds.forEach((cell) => cell.classList.add('d-none'));
        }
      });
      this._saveChanges = true;
      this.hide();
    }

    _handlerRestoreDefault() {
      this._restoreListStates(this._listOriginalStates);
    }
}

export { DatatableMJ };
