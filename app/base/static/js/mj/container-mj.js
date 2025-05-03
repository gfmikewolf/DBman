// mj/container-mj.js
import { InstanceError } from './error-mj.js';
import { getElement, getElements } from './utils-mj.js';
import { BaseMJ } from './base-mj.js';

/**
 * ContainerMJ is the base class for all container-like classes.
 * 
 * @abstract
 * 
 * @property {Element} container - Must be Args[0] in construction, the container element for the class.
 * 
 * @method getInstance - Get the instance of the class from the container element.
 * @method getOrCreateInstance - Get the instance of the class from the container element or create a new instance.
 * @method _initMoreArgs - Sub-classes shall override this method to process more arguments of the constructor.
 */
class ContainerMJ extends BaseMJ {
  constructor(container, ...moreArgs) {
    super(container, ...moreArgs);
  }

  _initArgs(container) {
    this.container = getElement(container);
    if (!this.container) {
      throw new InstanceError(this.constructor.name);
    }
    this.container.__containerMJInstance = this;
  }

  static getInstance(container) {
    if (container instanceof this) {
      return container;
    }
    const element = getElement(container);
    return element ? element.__containerMJInstance || null : null;
  }

  static getOrCreateInstance(container, ...moreArgs) {
    if (!container) {
      throw new TypeError(this.constructor.name +'.getOrCreate(container, ...args): container is required.');
    } else {
      return this.getInstance(container) || new this(container, ...moreArgs);
    }
  }

  getValidElement(selector, container = this.container) {
    const element = getElement(selector, container);
    if (!element) {
      throw new InstanceError(selector);
    }
    return element;
  }

  getValidElements(selector, container = this.container) {
    const elements = getElements(selector, container);
    if (elements.length === 0) {
      throw new InstanceError(selector);
    }
    return elements;
  }
}

export { ContainerMJ };