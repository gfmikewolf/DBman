// mj/utils-mj.js

/**
 * getElement returns an element from a string or an element.
 * 
 * @param {string|Element} arg - A string or an element.
 * @returns {Element} - An element or null.
 */
function getElement(arg, container = document) {
  return typeof arg === 'string' ? 
    container.querySelector(arg) : 
    arg instanceof Element ? 
      arg : null;
}

function getElements(arg, container = document) {
  return typeof arg === 'string' ? 
    container.querySelectorAll(arg) : 
    arg instanceof NodeList ? 
      arg : null;
}

export { getElement, getElements };