// mj/base-mj.js
import { InstanceError } from './error-mj.js';

/**
 * BaseMJ is the base abstract class providing a set of rules for construction.
 * 
 * @abstract
 * 
 * @method _initArgs - Initializes the arguments passed to the constructor.
 * @method _findElements - Finds the elements within the container. Throw an error if prequesites are not met.
 * @method _initProperties - Initializes the properties of the class.
 * @method _initFunctions - Initializes the functions of the class.
 */
class BaseMJ {
  constructor(...args) {
    if (new.target === BaseMJ) {
        throw new InstanceError('BaseMJ');
    }
    this._initPrerequisites && this._initPrerequisites(...args);
    if (args.length > 0) {
      this._initArgs && this._initArgs(...args);
    }
    this._findElements && this._findElements(...args);
    this._initProperties && this._initProperties(...args);
    this._initFunctions && this._initFunctions(...args);
  }
}

export { BaseMJ };
