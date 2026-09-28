import { findScrollableParent } from '@jadawel/modules/core/utils/dom'
import { findGridDropIndex } from '@jadawel/modules/arabase/utils/gridOrder'

/**
 * Grid-aware variant of core's `v-sortable` directive
 * (`modules/core/directives/sortable.js`), fork-owned because core's directive is
 * Y-axis-only: built for vertical lists, it mis-detects the drop target in a
 * multi-column grid. The lifecycle is identical (mousedown on an optional handle,
 * 3-pixel movement threshold, vertical auto-scroll near the viewport edges,
 * Escape cancels, click suppression after a drop), but the drop target is
 * computed on both axes (`findGridDropIndex`) and the indicator is a cell-sized
 * outline box instead of a horizontal line.
 *
 * Usage mirrors core: `v-grid-sortable="{ id: item.id, update: onUpdate,
 * handle: '.child-element', enabled: true }"`. The directive only shows the drag
 * effect and reports the new order; persisting it is the update callback's job.
 */
let parent
let scrollableParent
let indicator

const sortableChildren = (container) =>
  [...container.childNodes].filter(
    (e) => e !== indicator && e.nodeType === 1 && e.sortableId !== undefined
  )

const getMousedownElement = (el, binding) => {
  const handle = binding.value.handle
  return handle ? el.querySelector(handle) || el : el
}

export default {
  /**
   * Called when the directive must bind to the element. It will register the
   * mousedown event on the element, which is used to start the drag and drop
   * process.
   */
  beforeMount(el, binding) {
    binding.dir.updated(el, binding)
    el.sortableAutoScrolling = false

    const mousedownElement = getMousedownElement(el, binding)

    el.mousedownEvent = (event) => {
      if (!el.sortableEnabled || event.button !== 0) {
        return
      }

      el.sortableMoved = false
      el.sortableStartClientX = event.clientX
      el.sortableStartClientY = event.clientY

      el.mouseMoveEvent = (event) => binding.dir.move(el, binding, event)
      window.addEventListener('mousemove', el.mouseMoveEvent)

      el.mouseUpEvent = (event) => binding.dir.up(el, binding, event)
      window.addEventListener('mouseup', el.mouseUpEvent)

      el.keydownEvent = (event) => {
        if (event.key === 'Escape') {
          // When the user presses the escape key we want to cancel the action
          binding.dir.cancel(el, event)
        }
      }
      document.body.addEventListener('keydown', el.keydownEvent)

      parent = el.parentNode
      scrollableParent = findScrollableParent(parent) || parent

      // If the parent container is not positioned, add the position automatically.
      if (getComputedStyle(parent).position === 'static') {
        parent.style.position = 'relative'
      }

      indicator = document.createElement('div')
      indicator.classList.add('grid-sortable-position-indicator')
      parent.insertBefore(indicator, parent.firstChild)
    }
    mousedownElement.addEventListener('mousedown', el.mousedownEvent)
  },
  /**
   * When the directive must unbind from the element, we will remove all the events
   * that could have been added.
   */
  unmounted(el, binding) {
    if (el.sortableMoved) {
      binding.dir.cancel(el)
    }

    const mousedownElement = getMousedownElement(el, binding)
    mousedownElement.removeEventListener('mousedown', el.mousedownEvent)
  },
  updated(el, binding) {
    el.sortableId = binding.value.id
    el.sortableEnabled =
      binding.value.enabled || binding.value.enabled === undefined
  },
  /**
   * Called when the user moves the mouse when the dragging of the element has
   * started. It calculates the target indicator box and saves before which
   * element the dragged element must be placed.
   */
  move(el, binding, event = null, startAutoScroll = true) {
    if (event !== null) {
      event.preventDefault()
      el.sortableLastMoveEvent = event
    } else {
      event = el.sortableLastMoveEvent
    }

    // Sometimes the user could accidentally drag the element one or two pixels while
    // clicking it. Because it could be annoying that the click doesn't work because
    // the moving state started, we check here if the user has at least dragged
    // the element 3 pixels vertically or horizontally before starting the moved state.
    if (!el.sortableMoved) {
      if (
        Math.abs(event.clientX - el.sortableStartClientX) > 3 ||
        Math.abs(event.clientY - el.sortableStartClientY) > 3
      ) {
        el.sortableMoved = true
      } else {
        return
      }
    }

    // Set pointer events to none because that will prevent hover and click
    // effects.
    // Only the sortable items: the board also holds its "add widget" tile.
    const all = sortableChildren(parent)

    // Add the `sortable-sorting-item` which disables the pointer events and user
    // select of all the sortable items. This will give a smoother user experience
    // as the user can't accidentally click the item and can't select the text while
    // dragging.
    all.forEach((s) => {
      s.classList.add('sortable-sorting-item')
    })

    const parentRect = parent.getBoundingClientRect()
    const rtl = document.documentElement.dir === 'rtl'

    // The drop target is the first item whose row band or inline midline the
    // cursor precedes; if there is none, the item moves to the end.
    const rects = all.map((item) => item.getBoundingClientRect())
    const dropIndex = findGridDropIndex(
      rects,
      event.clientX,
      event.clientY,
      rtl
    )
    const before = dropIndex < all.length ? all[dropIndex] : null

    // Save the element where the dragging item must be placed before so that the
    // new order can be calculated when the user releases the mouse.
    el.sortableBeforeElement = before

    // The indicator outlines the target cell: the before element's rect, or —
    // when dropping at the end — the last item's rect, to signal "after this one".
    const targetRect = before ? rects[dropIndex] : rects[rects.length - 1]
    indicator.style.top =
      targetRect.top - parentRect.top + parent.scrollTop + 'px'
    indicator.style.left = targetRect.left - parentRect.left + 'px'
    indicator.style.width = targetRect.width + 'px'
    indicator.style.height = targetRect.height + 'px'

    // If the user is not already auto scrolling, which happens while dragging and
    // moving the element close to the end of the view port at the top or bottom
    // side, we might need to initiate that process.
    if (
      scrollableParent.scrollHeight > scrollableParent.clientHeight &&
      (!el.sortableAutoScrolling || !startAutoScroll)
    ) {
      const scrollableParentRect = scrollableParent.getBoundingClientRect()
      const parentHeight =
        scrollableParentRect.bottom - scrollableParentRect.top
      const side = Math.ceil((parentHeight / 100) * 10)
      const autoScrollMouseTop = event.clientY - scrollableParentRect.top
      const autoScrollMouseBottom = parentHeight - autoScrollMouseTop
      let speed = 0

      if (autoScrollMouseTop < side) {
        speed = -(3 - Math.ceil((Math.max(0, autoScrollMouseTop) / side) * 3))
      } else if (autoScrollMouseBottom < side) {
        speed = 3 - Math.ceil((Math.max(0, autoScrollMouseBottom) / side) * 3)
      }

      // If the speed is either a positive or negative, so not 0, we know that we
      // need to start auto scrolling.
      if (speed !== 0) {
        el.sortableAutoScrolling = true
        scrollableParent.scrollTop += speed
        el.sortableScrollTimeout = setTimeout(() => {
          binding.dir.move(el, binding, null, false)
        }, 10)
      } else {
        el.sortableAutoScrolling = false
      }
    }
  },
  /**
   * Called when the user releases the mouse after the dragging of the element has
   * started. It will check calculate the new order of all items based on the last
   * beforeElement element saved by the move method. If the item has changed
   * position, the update function is called which needs to change the actual order
   * of the items.
   */
  up(el, binding) {
    binding.dir.cancel(el, binding)

    if (!el.sortableMoved) {
      return
    }

    el.sortableMoved = false

    // It could be that the element or a child element has a click handler. When the
    // user releases the mouse pointer, that click event could also be triggered
    // which we don't because we are dragging the element instead of clicking on it
    // directly. This makes sure that when releasing the mouse pointer, that click
    // event is stopped.
    const preventOtherClickEvent = (event) => {
      event.stopPropagation()
      window.removeEventListener('click', preventOtherClickEvent, true)
    }
    window.addEventListener('click', preventOtherClickEvent, true)
    // Remove the event because it could be that the user wants to click on the
    // element right after it has been moved.
    setTimeout(() => {
      window.removeEventListener('click', preventOtherClickEvent, true)
    })

    const oldOrder = sortableChildren(parent).map((e) => e.sortableId)
    const newOrder = oldOrder.filter((id) => id !== el.sortableId)
    const targetIndex = el.sortableBeforeElement
      ? newOrder.findIndex((id) => id === el.sortableBeforeElement.sortableId)
      : newOrder.length

    if (targetIndex === -1) {
      return
    }

    newOrder.splice(targetIndex, 0, el.sortableId)

    if (JSON.stringify(oldOrder) === JSON.stringify(newOrder)) {
      return
    }

    binding.value.update(
      newOrder,
      oldOrder,
      el.sortableId,
      el.sortableBeforeElement?.sortableId || null
    )
  },
  /**
   * Cancels the sorting by removing the target indicator, sorting classes and event
   * listeners.
   */
  cancel(el) {
    clearTimeout(el.sortableScrollTimeout)

    if (indicator.parentNode) {
      indicator.parentNode.removeChild(indicator)
    }

    sortableChildren(parent).forEach((s) => {
      s.classList.remove('sortable-sorting-item')
    })

    window.removeEventListener('mouseup', el.mouseUpEvent)
    window.removeEventListener('mousemove', el.mouseMoveEvent)
    document.body.removeEventListener('keydown', el.keydownEvent)
  },
}
