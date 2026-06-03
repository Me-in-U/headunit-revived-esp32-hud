(function exposeEditorDragActions(globalScope) {
  function beginDrag(state, element, point, handle = "") {
    if (!element) {
      state.selectedId = "";
      state.drag = null;
      return null;
    }
    state.selectedId = element.id;
    state.drag = {
      mode: handle ? "resize" : "move",
      handle,
      start: point,
      original: {
        x: Number(element.x || 0),
        y: Number(element.y || 0),
        w: Number(element.w || 1),
        h: Number(element.h || 1),
      },
      elementId: element.id,
      historyRecorded: false,
    };
    return state.drag;
  }

  function applyDragMove(state, element, point, editor, elementActions) {
    if (!state.drag || !element) {
      return false;
    }
    const dx = Math.round(point.x - state.drag.start.x);
    const dy = Math.round(point.y - state.drag.start.y);
    const original = state.drag.original;
    if (state.drag.mode === "move") {
      element.x = original.x + dx;
      element.y = original.y + dy;
    } else {
      elementActions.resizeElement(element, original, dx, dy, state.drag.handle);
    }
    editor.normalizeElementForCanvas(element, state.layout.canvas || {});
    return true;
  }

  function endDrag(state) {
    if (!state.drag) {
      return false;
    }
    state.drag = null;
    return true;
  }

  const api = {
    applyDragMove,
    beginDrag,
    endDrag,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorDragActions = api;
})(typeof window !== "undefined" ? window : globalThis);
