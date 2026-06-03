(function exposeEditorPointerActions(globalScope) {
  function pointerHandle(event) {
    return event.target?.dataset?.handle || "";
  }

  function pointerTargetElement(event, point, deps) {
    const targetBox = event.target?.closest?.(".element-hitbox");
    if (targetBox) {
      return deps.elementById(targetBox.dataset.id);
    }
    return deps.hitTest(point.x, point.y);
  }

  function handlePointerDown(state, dom, event, deps) {
    if (!state.layout) {
      return { started: false, ignored: true };
    }
    const point = deps.eventToCanvas(event);
    const handle = pointerHandle(event);
    const element = pointerTargetElement(event, point, deps);
    if (!element) {
      deps.dragActions.beginDrag(state, null, point, handle);
      hideDragGhost(dom);
      deps.renderAll();
      return { started: false };
    }
    deps.dragActions.beginDrag(state, element, point, handle);
    dom.selectionOverlay.setPointerCapture?.(event.pointerId);
    deps.renderAll();
    showDragGhost(state, dom, element, deps);
    event.preventDefault?.();
    return { started: true, element };
  }

  function handlePointerMove(state, dom, event, deps) {
    if (!state.drag) {
      return { moved: false };
    }
    const element = deps.elementById(state.drag.elementId);
    if (!element) {
      return { moved: false };
    }
    if (!state.drag.historyRecorded) {
      deps.recordHistory();
      state.drag.historyRecorded = true;
    }
    const point = deps.eventToCanvas(event);
    deps.dragActions.applyDragMove(state, element, point, deps.editor, deps.elementActions);
    deps.renderProperties();
    deps.renderOverlay();
    updateDragGhost(state, dom, element, deps);
    deps.schedulePreview(55);
    event.preventDefault?.();
    return { moved: true, element };
  }

  function handlePointerUp(state, dom, deps) {
    if (!deps.dragActions.endDrag(state)) {
      return { ended: false };
    }
    deps.markDirty();
    deps.renderAll();
    deps.schedulePreview(20);
    return { ended: true };
  }

  function showDragGhost(state, dom, element, deps) {
    if (!dom.previewImage.src || !element) {
      hideDragGhost(dom);
      return;
    }
    dom.dragGhost.hidden = false;
    dom.dragGhost.style.backgroundImage = `url("${dom.previewImage.src}")`;
    updateDragGhost(state, dom, element, deps);
  }

  function updateDragGhost(state, dom, element, deps) {
    if (dom.dragGhost.hidden || !element) {
      return;
    }
    const scale = deps.canvasScale();
    const style = deps.dragGhost.computeDragGhostStyle(element, state.layout?.canvas, scale);
    Object.assign(dom.dragGhost.style, style);
  }

  function hideDragGhost(dom) {
    if (!dom.dragGhost) {
      return;
    }
    dom.dragGhost.hidden = true;
    dom.dragGhost.style.backgroundImage = "";
  }

  const api = {
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    hideDragGhost,
    pointerTargetElement,
    showDragGhost,
    updateDragGhost,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPointerActions = api;
})(typeof window !== "undefined" ? window : globalThis);
