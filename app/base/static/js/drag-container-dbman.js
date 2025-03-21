export class DragContainer {
    constructor(arg) {
        // Initially set active to true; if any error occurs, set active to false and return.
        this.active = true;
        // Store the bound function references
        this._onMouseMoveHandler = this._onMouseMove.bind(this);
        this._onMouseUpHandler = this._onMouseUp.bind(this);
        this._onTouchMoveHandler = this._onTouchMove.bind(this);
        this._onTouchEndHandler = this._onTouchEnd.bind(this);

        // Locate the container element from the argument.
        if (typeof arg === 'string') {
            this.container = document.querySelector(arg);
            if (!this.container) {
                console.log('Container not found for selector:', arg);
                this.active = false;
                return;
            }
        } else if (arg instanceof Element) {
            this.container = arg;
        } else {
            console.log('Invalid argument provided to DragContainer.');
            this.active = false;
            return;
        }
        // Find draggable elements within the container.
        const draggables = this.container.querySelectorAll('.draggable');
        if (draggables.length === 0) {
            console.log('No draggable elements found in the container.');
            this.active = false;
            return;
        }

        // Add event listeners for each draggable element.
        draggables.forEach(draggable => {
            draggable.addEventListener('mousedown', (e) => {
                e.preventDefault();
                const parentLi = draggable.parentElement; // Get the parent <li> of the handle
                if (!parentLi) return;
                parentLi.classList.add('dragging');
                parentLi.classList.add('active');
                document.addEventListener('mousemove', this._onMouseMoveHandler);
                document.addEventListener('mouseup', this._onMouseUpHandler);
            });
            draggable.addEventListener('touchstart', (e) => {
                e.preventDefault();
                const parentLi = draggable.parentElement; // Get the parent <li> of the handle
                if (!parentLi) return;
                parentLi.classList.add('dragging');
                parentLi.classList.add('active');
                document.addEventListener('touchmove', this._onTouchMoveHandler);
                document.addEventListener('touchend', this._onTouchEndHandler);
            });
        });
    }
    
    _onMouseMove(e) {
        const parentLi = this.container.querySelector('.dragging'); // Get the currently dragging <li> element
        const afterElement = this._getDragAfterElement(e.clientY);
        if (afterElement == null) {
            this.container.appendChild(parentLi);
        } else {
            this.container.insertBefore(parentLi, afterElement);
        }
    }
    
    _onMouseUp() {
        const parentLi = this.container.querySelector('.dragging'); // Get the currently dragging <li> element
        if (parentLi) {
            parentLi.classList.remove('dragging');
            parentLi.classList.remove('active');
        }
        document.removeEventListener('mousemove', this._onMouseMoveHandler);
        document.removeEventListener('mouseup', this._onMouseUpHandler);
    }
    
    _onTouchMove(e) {
        const parentLi = this.container.querySelector('.dragging'); // Get the currently dragging <li> element
        const touch = e.touches[0];
        const afterElement = this._getDragAfterElement(touch.clientY);
        if (afterElement == null) {
            this.container.appendChild(parentLi);
        } else {
            this.container.insertBefore(parentLi, afterElement);
        }
    }
    
    _onTouchEnd() {
        const parentLi = this.container.querySelector('.dragging'); // Get the currently dragging <li> element
        if (parentLi) {
            parentLi.classList.remove('dragging');
            parentLi.classList.remove('active');
        }
        document.removeEventListener('touchmove', this._onTouchMoveHandler);
        document.removeEventListener('touchend', this._onTouchEndHandler);
    }
    
    _getDragAfterElement(y) {
        const draggableElements = [...this.container.querySelectorAll('.draggableList:not(.dragging)')];
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
