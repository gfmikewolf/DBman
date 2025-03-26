// mj/datajson.js

import { createElement } from './utils-mj.js';
import { ContainerMJ } from './container-mj.js'
import { SelectpickerMJ } from './selectpicker-mj.js';

class DatajsonMJ extends ContainerMJ {
  
  static counter = 0;
  static structureCache = {}; // all instances share the same structure cache

  constructor (container, djType=null, djData=null) {
    super(container, djType, djData);
    DatajsonMJ.counter += 1;
    this.uid = DatajsonMJ.counter;
  }

  _initArgs(container, djType, djData) {
    super._initArgs(container, djType, djData);
    try {
      if (!djData) {
        this.data = { __datajson_id__: djType };
        this.type = djType;
      } else {
        dataType = djData['__datajson_id__'];
        this.type = dataType;
        if (djType && djType != dataType) {
          throw new TypeError(`DataJson type is inconsistent. djType=${djType} !== dataType=${dataType}`);
        }
      }
    } catch (error) {
      console.error(`Error recorded in construction of DataJson: ${error}`);
    }
  }

  _initProperties(container, djType, djData) {
    super._initProperties && super._initProperties(container, djType, djData);
    this.elementCache = {};
    this.dataCache = {};
    if (this.type) {
      this.renderStructure = this.getRenderStructure();
      this.element = this.getOrCreateDOMElement();
      // each instance has its own data cache indexed by type
      this.elementCache[this.type] = this.element; 
      this.dataCache[this.type] = this.data;
    }
  }
  
  async getRenderStructure() {
    if (!this.type) {
      this.renderStructure = {};
      return this.renderStructure;
    }
    let structure = DatajsonMJ.structureCache[this.type]
    if (structure) {
      return DatajsonMJ.structureCache[this.type];
    }
    const response = await fetch(
      `/api/datajson/structure/${this.type}`, {});
    if (!response.ok) {
      throw new TypeError('Datajson type is incorrect: ', this.type);
    }
    const responseJSON = await response.json();
    structure = responseJSON['data'];
    if (!structure) {
      throw new TypeError('Datajson type is incorrect: ', this.type);
    }
    DatajsonMJ.structureCache[this.type] = structure;
    this.renderStructure = structure;
    return structure;
  }

  async update(djType=null, djData=null, kwargs = {}) {
    if (djType === null && djData === null && Object.keys(kwargs).length === 0) {
      return;
    }
    if (djType != this.type) {
      if (this.type) {
        this.elementCache[this.type] = this.element;
        this.getDataFromDOM();
        this.dataCache[this.type] = this.data;
        this.renderStructure = this.getRenderStructure();
        this.element.style.display = 'none';
      }
      if (djType) {
        this.type = djType;
      }
      if (!djData) {
        this.data = { __datajson_id__: this.type };
      } else {
        this.data = djData;
      }
      if (this.type in this.elementCache) {
        this.element = this.elementCache[this.type];
        this.element.style.display = 'block';
      } else {
        this.element = await this.getOrCreateDOMElement();
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

  getDataFromDOM() {
    for (let key of this.renderStructure['data']) {
      const keyUid = `${this.type}-${key}-${this.uid}`;
      const input = this.element.querySelector(`#${keyUid}`);
      if (input.value) {
        this.data[key] = inputElement.value;
      }
    }
    return this.data;
  }

  async getOrCreateDOMElement() {
    if (this.elementCache[this.type]) {
      return this.elementCache[this.type];
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
    }
    this.elementCache[this.type] = card;
    this.container.appendChild(frag);
    return card;
  }
}

export { DatajsonMJ };
