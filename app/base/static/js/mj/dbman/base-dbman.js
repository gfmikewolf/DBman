// app/base/static/js/base-dbman.js
import { InstanceError } from './error-mj.js';
import { BaseMJ } from './base-mj.js';
/**
 * BaseDBMan is the base class for all database management classes.
 * 
 * @class BaseDBMan
 * @extends BaseMJ
 * @abstract
 *
 */
export class BaseDBMan extends BaseMJ {
    constructor(...args) {
        super(...args);
        if (new.target === BaseDBMan) {
            throw new InstanceError(this.name);
        }   
    }
}