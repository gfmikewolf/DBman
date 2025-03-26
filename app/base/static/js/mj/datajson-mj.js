// mj/datajson.js

import { createElement } from './utils-mj.js';
import { ContainerMJ } from './container-mj.js'
import { SelectpickerMJ } from './selectpicker-mj.js';

class DatajsonMJ extends ContainerMJ {
  
  static counter = 0;
  static structureCache = {}; // all instances share the same structure cache

  constructor (container, djType=null, djData=null) {
    super(container, djType, djData);
    this.counter += 1;
    this.uid = this.counter;
  }

  _initArgs(container, djType, djData) {
    super._initArgs(container, djType, djData);
    if (djType === null && djData === null) {
      throw new TypeError('Must instantiate DatajsonMJ with at least one param.');
    }
    let dataType;
    if (djData) {
      dataType = djData['__datajson_id__'];
      if (dataType === null || dataType === undefined) {
        throw new TypeError('No Datajson_id or data is available.');
      }
      this.type = dataType;
    } else {
      this.data = { __datajson_id__: djType };
      dataType = djType;
      this.type = djType;
    }
    if (djType !== this.type) {
      throw new TypeError(`Data is corrupted, type is inconsistent. ${djType} !== ${this.type}`);
    }
  }

  _initProperties(container, djType, djData) {
    super._initProperties && super._initProperties(container, djType, djData);
    this.elementCache = {};
    this.dataCache = {};
    this.structureCache = {};
    this.renderStructure = this.getRenderStructure();
    this.element = this.getOrCreateDOMElement();
    // each instance has its own data cache indexed by type
    this.elementCache[this.type] = this.element; 
    this.dataCache[this.type] = this.data;
  }
  
  async getRenderStructure() {
    let structure = this.structureCache[this.type]
    if (structure) {
      return this.structureCache[this.type];
    }
    const response = await fetch(
      `/api/datajson/structure/${this.type}`, {});
    if (!response.ok) {
      throw new TypeError('Datajson type is incorrect: ', this.type);
    }
    const responseJSON = response.json;
    structure = responseJSON['data'];
    if (!structure) {
      throw new TypeError('Datajson type is incorrect: ', this.type);
    }
    this.structureCache[this.type] = structure;
    this.renderStructure = structure;
    return structure;
  }

  update(djType=null, djData=null, kwargs = {}) {
    if (djType === null && djData === null && Object.keys(kwargs).length === 0) {
      return;
    }
    if (djType !== this.type) {
      this.elementCache[this.type] = this.element;
      this.getDataFromDOM();
      this.dataCache[this.type] = this.data;
      this.type = djType;
      this.renderStructure = this.getRenderStructure();
      this.element.style.display = 'none';
      if (djData === null) {
        this.data = { __datajson_id__: this.type };
      } else {
        this.data = djData;
      }
      if (this.type in this.elementCache) {
        this.element = this.elementCache[this.type];
        this.element.style.display = 'block';
      } else {
        this.element = this.getOrCreateDOMElement();
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
      const inputElement = this.element.getElementById(keyUid);
      if (inputElement) {
        inputElement.value = this.data[key];
      }
    }
  }

  getDataFromDOM() {
    for (let key in this.data) {
      const keyUid = `${this.type}-${key}-${this.uid}`;
      const input = this.element.querySelector(`#${keyUid}`);
      if (input.value) {
        this.data[key] = inputElement.value;
      }
    }
    return this.data;
  }

  getOrCreateDOMElement() {
    if (this.elementCache[this.type]) {
      return this.elementCache[this.type];
    }
    const frag = document.createDocumentFragment();
    const card = createElement('div', frag, 'card');
    const cardBody = createElement('div', card, 'card-body');
    const inputGroup = createElement('div', cardBody, 'input-group mb-3 flex-nowrap');
    const structure = this.getRenderStructure();
    
    for (let key in structure['data']) {
      const keyUid = `${this.type}-${key}-${this.uid}`;
      let value = this.data[key];
      if (value === null || value === undefined) {
        value = '';
      }
      const ref_keys = Object.keys(structure['ref_map']);
      
      const label = createElement(
        'label', 
        inputGroup,
        'input-group-text', 
        { for: keyUid },
        key
      );

      if (key in structure['required']) {
        createElement('span', label, '', {}, '*');
        label.classList.add('text-danger');
      }
      if (key in structure['date']) {
        const input = createElement(
          'input', 
          inputGroup, 
          'form-control', 
          { type: 'date', id: keyUid, value: value }
        );
        inputElement = input;
      } else if (key in ref_keys) {
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
        new SelectpickerMJ(selectpicker);
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