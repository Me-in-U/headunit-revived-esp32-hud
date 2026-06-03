(function exposeEditorOverlayView(globalScope) {
  const HANDLE_NAMES = ["nw", "n", "ne", "e", "se", "s", "sw", "w"];

  function renderOverlay(state, dom, options) {
    if (!state.layout) {
      return;
    }
    const { sx, sy } = options.canvasScale();
    dom.selectionOverlay.replaceChildren();

    for (const element of state.layout.elements || []) {
      if (element.visible === false) {
        continue;
      }
      dom.selectionOverlay.append(renderHitbox(state, element, sx, sy, options.documentRef));
    }
  }

  function renderHitbox(state, element, sx, sy, documentRef) {
    const box = documentRef.createElement("div");
    box.className = `element-hitbox${element.id === state.selectedId ? " selected" : ""}`;
    box.dataset.id = element.id;
    box.style.left = `${Number(element.x || 0) * sx}px`;
    box.style.top = `${Number(element.y || 0) * sy}px`;
    box.style.width = `${Math.max(1, Number(element.w || 1)) * sx}px`;
    box.style.height = `${Math.max(1, Number(element.h || 1)) * sy}px`;
    if (element.id === state.selectedId) {
      appendSelectionControls(box, element, documentRef);
    }
    return box;
  }

  function appendSelectionControls(box, element, documentRef) {
    const label = documentRef.createElement("div");
    label.className = "element-label";
    label.textContent = element.id;
    box.append(label);
    for (const handle of HANDLE_NAMES) {
      box.append(renderHandle(handle, documentRef));
    }
  }

  function renderHandle(handle, documentRef) {
    const grip = documentRef.createElement("div");
    grip.className = `resize-handle ${handle}`;
    grip.dataset.handle = handle;
    grip.style.left = handle.includes("w") ? "-5px" : handle.includes("e") ? "calc(100% - 4px)" : "calc(50% - 4px)";
    grip.style.top = handle.includes("n") ? "-5px" : handle.includes("s") ? "calc(100% - 4px)" : "calc(50% - 4px)";
    return grip;
  }

  const api = {
    renderOverlay,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorOverlayView = api;
})(typeof window !== "undefined" ? window : globalThis);
