// mj/datajson.js
import { BaseMJ } from './base-mj.js'

class DatajsonMJ extends BaseMJ {
  constructor (djType=null, djData=null) {
    super(djType, djData);
  }

  _initArgs(djType, djData) {
    if (!djType && !djData) {
      throw new TypeError('Must instantiate DatajsonMJ with at least one param.');
    }
    this.type = djType;
    this.data = djData;
    if (this.type === null) {
      try {
        this.type = this.data['__datajson_id__'];
        if (this.type === null) {
          throw new TypeError('No Datajson_id or data is available.')
        }
      }
      catch(error) {
        throw new TypeError('Data is corrupted: ', error, this)
      }
    } else if (this.type != this.data['__datajson_id__']) {
      throw new TypeError('Data is corrupted', this)
    }
  }

  _initProperties() {
    this.structureCache = {}
    this.dataCache = {}
    this.renderStructure = this.getRenderStructure();
    this.structureCache['this.type'] = 
      JSON.parse(
        JSON.stringify(this.renderStructure)
      );
    this.element = this.createDOMElement();
    this.dataCache['this.type'] = this.element;
  }
  
  async getRenderStructure() {
    const response = await fetch(
      `/api/datajson/structure/${this.type}`, {});
    if (!response.ok) {
      throw new TypeError('Datajson type is incorrect: ', this.type);
    }
    const responseJSON = response.json;
    return responseJSON['data'];
  }

  createDOMElement() {
    this.container = document.createElement('div');
    container.classList.add('card');
    const cardBody = this.container.createDOMElement('div');
    cardBody.classList.add('card-body');
    const form = cardBody.createDOMElement('form');
    form.id = 'datajson-input-'
    return container;
  }
}
