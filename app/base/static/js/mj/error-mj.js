// mj/error-mj.js

/**
 * InstanceError is thrown when an instance is not found or not active.
 * It logs an error message to the console.
 * 
 * @extends Error
 * 
 * @method constructor - Creates an error message with the class name
 * @method log - Logs an error message with the class name
 */
export class InstanceError extends Error {
  constructor(className) {
    super('InstanceError: ' + className + ' cannot be instantiated.');
    this.name = 'InstanceError';
  }

  static log(className) {
    console.error('InstanceError: ', className, ' cannot be instantiated.');
  }
}