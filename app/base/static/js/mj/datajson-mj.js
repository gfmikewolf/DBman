// mj/datajson.js

import { createElement } from './utils-mj.js';
import { ContainerMJ } from './container-mj.js'
import { SelectpickerMJ } from './selectpicker-mj.js';

class DatajsonMJ extends ContainerMJ {
  
  static counter = 0;
  static elementCache = {}; // all instances share the same element structure cache

  constructor (container, targetElement, djType=null, djData=null) {
    super(container, targetElement, djType, djData);
    DatajsonMJ.counter += 1;
    this.uid = DatajsonMJ.counter;
  }

  _initArgs(container, targetElement, djType, djData) {
    super._initArgs(container, targetElement, djType, djData);
    this._load(djType, djData);
    this.targetElement = targetElement;
  }

  async _initProperties(container, targetElement, djType, djData) {
    super._initProperties && super._initProperties(container, targetElement, djType, djData);
    this.renderStructure = null;
    if (this.type) {
      this.renderStructure = await this.getRenderStructure();
      this.element = this.getOrCreateDOMElement();
      // each instance has its own data cache indexed by type
      DatajsonMJ.elementCache[this.type] = this.element; 
    }
  }
  
  _load(djType, djData) {
    try {
      if (!djData || Object.keys(djData).length === 0) {
        this.data = { __datajson_id__: djType };
        this.type = djType;
      } else {
        const dataType = djData['__datajson_id__'] || null;
        this.type = dataType;
        if (djType && djType != dataType) {
          throw new TypeError(`DataJson type is inconsistent. djType=${djType} !== dataType=${dataType}`);
        }
      }
    } catch (error) {
      console.error(`Error recorded in construction of DataJson: ${error}`);
    }
  }

  async getRenderStructure() {
    if (!this.type) {
      return null;
    }
    const response = await fetch(
      `/api/datajson/structure/${this.type}`, {});
    if (!response.ok) {
      throw new TypeError('Datajson type is incorrect: ', this.type);
    }
    const responseJSON = await response.json();
    const structure = responseJSON['data'];
    if (!structure) {
      throw new TypeError('Datajson type is incorrect: ', this.type);
    }
    return structure;
  }

  async update(newType=null, newData=null, kwargs = {}) {
    if (newType === null && djData === null && Object.keys(kwargs).length === 0) {
      return;
    }
    if (!newData) {
      newData = {};
    }
    for (let key in kwargs) {
      newData[key] = kwargs[key];  
    }
    if (newType != this.type) {
      if (this.type) {
        this.element.style.display = 'none';
        DatajsonMJ.elementCache[this.type] = this.element;
      }
      this._load(newType, newData);
      if(!this.type) {
        this.renderStructure = null;
      } else {
        this.element = await this.getOrCreateDOMElement();
        this.element.style.display = 'block';
      }
    }
    this.updateData(this.data, kwargs);
  }

  updateData(djData, kwargs) {
    for (let key in kwargs) {
      if (key in djData) {
        djData[key] = kwargs[key];
      }
    }
    for (let key in djData) {
      if (key in this.data) {
        this.data[key] = djData[key];
      } else {
        throw new Error(`Data is corrupted in key: ${key} for type: ${this.type}`);
      }
    }
    this.reRender();
  }

  reRender() {
    for (let key in this.data) {
      const keyUid = `${this.type}-${key}-${this.uid}`;
      const inputElement = this.element.querySelector(`#${keyUid}`);
      if (inputElement) {
        inputElement.value = this.data[key];
      }
    }
  }

  getData() {
    if (!this.renderStructure) {
      return {};
    }
    for (let key of this.renderStructure['data']) {
      const keyUid = `${this.type}-${key}-${this.uid}`;
      const input = this.element.querySelector(`#${keyUid}`);
      if (input.value) {
        this.data[key] = input.value;
      }
    }
    return this.data;
  }

  async getOrCreateDOMElement() {
    if (DatajsonMJ.elementCache[this.type]) {
      return DatajsonMJ.elementCache[this.type];
    }
    const frag = document.createDocumentFragment();
    const card = createElement('div', frag, 'card');
    const cardBody = createElement('div', card, 'card-body');
    const structure = await this.getRenderStructure();
    let inputElement;

    for (let key of structure['data']) {
      const keyUid = `${this.type}-${key}-${this.uid}`;
      let value = this.data[key];
      if (value === null || value === undefined) {
        value = '';
      }
      const inputGroup = createElement('div', cardBody, 'input-group mb-3 flex-nowrap');
      const label = createElement(
        'label', 
        inputGroup,
        'input-group-text', 
        { for: keyUid },
        key
      );

      if (structure['required'].includes(key)) {
        const span = createElement('span', label, 'text-danger', {}, '*');
      }
      if (structure['date'].includes(key)) {
        const input = createElement(
          'input', 
          inputGroup, 
          'form-control', 
          { type: 'date', id: keyUid, value: value }
        );
        inputElement = input;
      } else if (key in structure['ref_map']) {
        const ref_pks_name = structure['ref_map'][key];
        let selectpicker = null;
        if (ref_pks_name.length > 5) {
          selectpicker = createElement(
            'div', inputGroup, 'selectpicker-mj');
          const searchInput = createElement(
            'input', 
            selectpicker, 
            'form-control', 
            { type: 'search', placeholder: '\u{1F50D}' } // Unicode for magnifying glass
          );
        }
        const select = createElement(
          'select', 
          inputGroup, 
          'form-select', 
          { id: keyUid }
        );
        inputElement = select;
        const hiddenOption = createElement(
          'option', select, '', { value: '', hidden: true }, '/'
        );
        if (value === null || value === undefined || value === '') {
          hiddenOption.selected = true;
        }
        for (let pks_name in ref_pks_name) {
          const option = createElement(
            'option', select, '', { value: ref_pks_name[pks_name][0] }, ref_pks_name[pks_name][1]
          );
          if (value === ref_pks_name[pks_name][0]) {
            option.selected = true;
          }
        }
        if (ref_pks_name.length > 5) {
          new SelectpickerMJ(inputGroup);
        }
      } else if (key in structure['longtext']) {
        const textarea = createElement(
          'textarea', 
          inputGroup, 
          'form-control', 
          { 
            id: keyUid, 
            rows: (value === null || value === undefined || value === '') ?
              3 : Math.ceil(value.length / 40), 
            pattern: '.*\\S.*' }, 
          value
        );
        inputElement = textarea;
      } else {
        const input = createElement(
          'input', 
          inputGroup, 
          'form-control', 
          { type: 'text', id: keyUid, value: value, pattern: '.*\\S.*' }
        );
        inputElement = input;
      }
      if (key in structure['readonly']) {
        inputElement.readOnly = true;
      }
      if (key in structure['required']) {
        inputElement.required = true;
      }
      inputElement.addEventListener('change', () => {
        this.targetElement.value = JSON.stringify(this.getData());
      });
    }
    DatajsonMJ.elementCache[this.type] = card;
    this.container.appendChild(frag);
    this.renderStructure = structure;
    return card;
  }
}

export { DatajsonMJ };
