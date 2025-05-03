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

function createElement( tag, 
                        container = null, 
                        classList = '', 
                        attributes = {}, 
                        innerText = '') {
  let root = null;
  if (container === null || container instanceof Element || container instanceof DocumentFragment) {
    root = document;
  } else if (container instanceof Document) {
    root = container;
  }
  const element = root.createElement(tag);
  if (classList !== '') {
    classList.split(' ').forEach(className => {
      element.classList.add(className);
    });
  }
  for (let key in attributes) {
    element.setAttribute(key, attributes[key]);
  }
  if (innerText !== '') {
    element.innerText = innerText;
  }
  if (container instanceof Element || container instanceof DocumentFragment) {
    container.appendChild(element);
  }
  return element;
}

export { getElement, getElements, createElement };
