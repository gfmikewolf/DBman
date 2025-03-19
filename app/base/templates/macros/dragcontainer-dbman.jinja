export class DragContainer {
    constructor(arg) {
        this.active = false;
        // 存储绑定后的函数引用
        this._onMouseMoveHandler = this._onMouseMove.bind(this);
        this._onMouseUpHandler = this._onMouseUp.bind(this);
        this._onTouchMoveHandler = this._onTouchMove.bind(this);
        this._onTouchEndHandler = this._onTouchEnd.bind(this);

        if (typeof arg === 'string') {
            this.container = document.querySelector(arg);
            if (!this.container)
                return;
        } else if (arg instanceof Element) {
            this.container = arg;
        }
        const draggables = this.container.querySelectorAll('.draggable');
        if (draggables.length === 0)
            return;

        draggables.forEach(draggable => {
            draggable.addEventListener('mousedown', (e) => {
                e.preventDefault();
                const parentLi = draggable.parentElement; // 获取手柄的父元素 <li>
                parentLi.classList.add('dragging');
                parentLi.classList.add('active');
                document.addEventListener('mousemove', this._onMouseMoveHandler);
                document.addEventListener('mouseup', this._onMouseUpHandler);
            });
            draggable.addEventListener('touchstart', (e) => {
                e.preventDefault();
                const parentLi = draggable.parentElement; // 获取手柄的父元素 <li>
                parentLi.classList.add('dragging');
                parentLi.classList.add('active');
                document.addEventListener('touchmove', this._onTouchMoveHandler);
                document.addEventListener('touchend', this._onTouchEndHandler);
            });
        });
        this.active = true;
    }
    
    _onMouseMove(e) {
        const parentLi = this.container.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
        const afterElement = this._getDragAfterElement(e.clientY);
        if (afterElement == null) {
            this.container.appendChild(parentLi);
        } else {
            this.container.insertBefore(parentLi, afterElement);
        }
    }

    _onMouseUp() {
        const parentLi = this.container.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
        if (parentLi) {
            parentLi.classList.remove('dragging');
            parentLi.classList.remove('active');
        }
        document.removeEventListener('mousemove', this._onMouseMoveHandler);
        document.removeEventListener('mouseup', this._onMouseUpHandler);
    }

    _onTouchMove(e) {
        const parentLi = this.container.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
        const touch = e.touches[0];
        const afterElement = this._getDragAfterElement(touch.clientY);
        if (afterElement == null) {
            this.container.appendChild(parentLi);
        } else {
            this.container.insertBefore(parentLi, afterElement);
        }
    }

    _onTouchEnd() {
        const parentLi = document.querySelector('.dragging'); // 获取正在拖拽的 <li> 元素
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
