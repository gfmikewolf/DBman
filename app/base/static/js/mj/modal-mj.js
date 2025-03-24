// mj/modal-mj.js
import { InstanceError } from './error-mj.js';
import { ContainerMJ } from './container-mj.js';

/**
 * ModalMJ is a base class for creating Bootstrap modals.
 * @extends ContainerMJ
 * @property {HTMLElement} container - The modal element.
 * @property {Bootstrap.Modal} bsModal - The Bootstrap Modal instance.
 * @property {boolean} active - True if the modal is active.
 * @method show - Show the modal.
 * @method hide - Hide the modal.
 * @method _blurFocus - Remove focus from elements inside the modal.
 * @method _extraHandlerHide - Extra handler when the modal is being hidden.
 */
class ModalMJ extends ContainerMJ {
  constructor(container, ...moreArgs) {
    super(container, ...moreArgs);
  }

  _findElements(container, ...moreArgs) {
    super._findElements && super._findElements(container, ...moreArgs);
    this.bsModal = bootstrap.Modal.getOrCreateInstance(this.container);
    if (!this.bsModal) {
        throw new InstanceError('Bootstrap Modal for' + container);
    }
  }

  _initFunctions(container, ...moreArgs) {
    super._initFunctions && super._initFunctions(container, ...moreArgs);
    // Add an extra handler when the modal is being hidden
    this.container.addEventListener('hide.bs.modal', this._extraHandlerHide.bind(this));
  }
    
  show(timeout = 0) {
    this.bsModal.show();
    if (timeout > 0) {
      setTimeout(() => this.hide(), timeout);
    }
  }

  hide() {
    this._blurFocus();
    this.bsModal.hide();
  }

  /**
   * Remove focus from elements inside the modal to prevent aria-hidden warnings.
   */
  _blurFocus() {
    if (document.activeElement && this.container.contains(document.activeElement)) {
      document.activeElement.blur();
    }
  }

  _extraHandlerHide() {
    this._blurFocus();
  }
}

export { ModalMJ };