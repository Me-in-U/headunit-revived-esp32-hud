(function exposeEditorElementActions(globalScope) {
  const MIN_ELEMENT_SIZE = 8;
  const DUPLICATE_OFFSET = 24;

  function elementById(layout, id) {
    if (!id) {
      return null;
    }
    return (layout?.elements || []).find((element) => element.id === id) || null;
  }

  function selectedElement(state) {
    return elementById(state.layout, state.selectedId);
  }

  function duplicateSelectedElement(state, editor) {
    const element = selectedElement(state);
    if (!element) {
      return null;
    }
    const copy = editor.clone(element);
    copy.id = editor.uniqueId(state.layout, `${element.id}_copy`);
    copy.label = copy.label ? `${copy.label} copy` : copy.id;
    copy.x = Number(copy.x || 0) + DUPLICATE_OFFSET;
    copy.y = Number(copy.y || 0) + DUPLICATE_OFFSET;
    copy.z = editor.nextZ(state.layout);
    editor.normalizeElementForCanvas(copy, state.layout.canvas || {});
    state.layout.elements = [...(state.layout.elements || []), copy];
    state.selectedId = copy.id;
    return copy;
  }

  function deleteSelectedElement(state) {
    if (!state.selectedId) {
      return false;
    }
    state.layout.elements = (state.layout.elements || []).filter((element) => element.id !== state.selectedId);
    state.selectedId = "";
    return true;
  }

  function bumpSelectedZ(state, delta) {
    const element = selectedElement(state);
    if (!element) {
      return null;
    }
    element.z = Number.parseInt(element.z || 0, 10) + delta;
    return element;
  }

  function resizeElement(element, original, dx, dy, handle) {
    let x = original.x;
    let y = original.y;
    let w = original.w;
    let h = original.h;
    if (handle.includes("e")) {
      w = original.w + dx;
    }
    if (handle.includes("s")) {
      h = original.h + dy;
    }
    if (handle.includes("w")) {
      x = original.x + dx;
      w = original.w - dx;
    }
    if (handle.includes("n")) {
      y = original.y + dy;
      h = original.h - dy;
    }
    if (w < MIN_ELEMENT_SIZE) {
      x = element.x;
      w = MIN_ELEMENT_SIZE;
    }
    if (h < MIN_ELEMENT_SIZE) {
      y = element.y;
      h = MIN_ELEMENT_SIZE;
    }
    Object.assign(element, { x, y, w, h });
    return element;
  }

  const api = {
    DUPLICATE_OFFSET,
    MIN_ELEMENT_SIZE,
    bumpSelectedZ,
    deleteSelectedElement,
    duplicateSelectedElement,
    elementById,
    resizeElement,
    selectedElement,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorElementActions = api;
})(typeof window !== "undefined" ? window : globalThis);
