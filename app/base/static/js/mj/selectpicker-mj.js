// mj/selectpicker-mj.js
import { ContainerMJ } from "./container-mj.js";

class SelectpickerMJ extends ContainerMJ {
  constructor(container) {
      super(container);
  }
  
  static getOrCreateAll() {
    return Array.from(document.querySelectorAll('.mj-selectpicker')).reduce(
      (acc, selectpickerElement) => (
        acc.push(SelectpickerMJ.getOrCreateInstance(selectpickerElement)),
        acc
      ), 
      []
    );
  }
  
  _findElements(container) {
    super._findElements && super._findElements(container);
    this.search = this.getValidElement('[type="search"]');
    this.select = this.getValidElement('select');
  }

  _initFunctions(container) {
    super._initFunctions && super._initFunctions(container);
    this._initSearchClick();
    this._initSearchChange();
  }

  _initSearchClick() {
    this.search.addEventListener('focus', () => {
        this.select.click();
    });
  }
  _initSearchChange() {
    this.search.addEventListener('input', (event) => {
      const searchValue = event.target.value.toLowerCase();
      Array.from(this.select.options).forEach(option => 
        option.style.display = option.text.toLowerCase().includes(searchValue) ? 
          '' : 'none'
      );
    });
  }
}

export { SelectpickerMJ };