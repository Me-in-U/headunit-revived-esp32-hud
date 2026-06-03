(function exposeEditorEditActions(globalScope) {
  function selectPaletteVariant(state, item, category, deps) {
    const before = deps.snapshotState();
    const result = deps.editor.addOrTogglePaletteElement(
      state.layout,
      item,
      category,
      state.metadata.palette || {}
    );
    state.selectedId = result.element?.id || "";
    if (result.action === "selected") {
      deps.renderAll();
      return { changed: false, result };
    }
    deps.pushUndoSnapshot(before);
    state.history.redo = [];
    deps.markDirty();
    deps.renderAll();
    deps.schedulePreview(40);
    return { changed: true, result };
  }

  function handlePropertyInput(state, dom, event, selectedElement, deps) {
    const element = selectedElement();
    if (!element) {
      return { changed: false };
    }
    deps.recordHistory();
    const propertyScrollTop = dom.propertyForm.scrollTop;
    const key = event.currentTarget.dataset.key;
    const result = deps.propertyActions.applyPropertyInput(
      state,
      element,
      key,
      event.currentTarget.value,
      deps.editor
    );
    event.currentTarget.value = result.inputValue;
    deps.markDirty();
    deps.renderProperties();
    deps.requestAnimationFrame(() => {
      dom.propertyForm.scrollTop = propertyScrollTop;
    });
    deps.renderLayers();
    deps.renderOverlay();
    deps.schedulePreview(60);
    return { changed: true, result };
  }

  const api = {
    handlePropertyInput,
    selectPaletteVariant,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorEditActions = api;
})(typeof window !== "undefined" ? window : globalThis);
