// mj/dragger-mj.js
import { ContainerMJ } from "./container-mj.js";

export class DraggerMJ extends ContainerMJ {
  constructor(container) {
    super(container);
  }

  _findElements(container) {
    super._findElements && super._findElements(container);
    // Find draggable elements within the container.
    this.draggables = this.getValidElements('.draggable');
  }

  _initProperties(container) {
    super._initProperties && super._initProperties(container);
    // Store the bound function references
    this._onMouseMoveHandler = this._onMouseMove.bind(this);
    this._onMouseUpHandler = this._onMouseUp.bind(this);
    this._onTouchMoveHandler = this._onTouchMove.bind(this);
    this._onTouchEndHandler = this._onTouchEnd.bind(this);
  }

  _initFunctions(container) {
    super._initFunctions && super._initFunctions(container);
    // Add event listeners for each draggable element.
    this.draggables.forEach(draggable => {
      draggable.addEventListener('mousedown', (e) => {
        e.preventDefault();
        const parentLi = draggable.parentElement;
        parentLi.classList.add('dragging');
        parentLi.classList.add('active');
        document.addEventListener('mousemove', this._onMouseMoveHandler);
        document.addEventListener('mouseup', this._onMouseUpHandler);
      });
      draggable.addEventListener('touchstart', (e) => {
        e.preventDefault();
        const parentLi = draggable.parentElement;
        parentLi.classList.add('dragging');
        parentLi.classList.add('active');
        document.addEventListener('touchmove', this._onTouchMoveHandler);
        document.addEventListener('touchend', this._onTouchEndHandler);
      });
    });
  }
  
  _onMouseMove(e) {
    const parentLi = this.container.querySelector('.dragging');
    const afterElement = this._getDragAfterElement(e.clientY);
    if (afterElement == null) {
      this.container.appendChild(parentLi);
    } else {
      this.container.insertBefore(parentLi, afterElement);
    }
  }
  
  _onMouseUp() {
    const parentLi = this.container.querySelector('.dragging');
    parentLi.classList.remove('dragging');
    parentLi.classList.remove('active');
    document.removeEventListener('mousemove', this._onMouseMoveHandler);
    document.removeEventListener('mouseup', this._onMouseUpHandler);
  }
  
  _onTouchMove(e) {
    const parentLi = this.container.querySelector('.dragging');
    const touch = e.touches[0];
    const afterElement = this._getDragAfterElement(touch.clientY);
    if (afterElement == null) {
      this.container.appendChild(parentLi);
    } else {
      this.container.insertBefore(parentLi, afterElement);
    }
  }
  
  _onTouchEnd() {
    const parentLi = this.container.querySelector('.dragging');
    parentLi.classList.remove('dragging');
    parentLi.classList.remove('active');
    document.removeEventListener('touchmove', this._onTouchMoveHandler);
    document.removeEventListener('touchend', this._onTouchEndHandler);
  }
  
  _getDragAfterElement(y) {
    const draggableElements = [
      ...this.container.querySelectorAll('.draggableList:not(.dragging)')
    ];
    return draggableElements.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
  }
}
