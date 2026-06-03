(function exposeEditorCommandActions(globalScope) {
  function duplicateSelected(state, deps) {
    if (!deps.selectedElement()) {
      return { changed: false };
    }
    deps.recordHistory();
    if (!deps.elementActions.duplicateSelectedElement(state, deps.editor)) {
      return { changed: false };
    }
    deps.markDirty();
    deps.renderAll();
    deps.schedulePreview(40);
    deps.setStatus(deps.translate("duplicateReady"), "ok");
    return { changed: true };
  }

  function deleteSelected(state, deps) {
    if (!state.selectedId) {
      return { changed: false };
    }
    deps.recordHistory();
    if (!deps.elementActions.deleteSelectedElement(state)) {
      return { changed: false };
    }
    deps.markDirty();
    deps.renderAll();
    deps.schedulePreview(40);
    return { changed: true };
  }

  function bumpZ(state, delta, deps) {
    if (!deps.selectedElement()) {
      return { changed: false };
    }
    deps.recordHistory();
    if (!deps.elementActions.bumpSelectedZ(state, delta)) {
      return { changed: false };
    }
    deps.markDirty();
    deps.renderLayers();
    deps.renderOverlay();
    deps.schedulePreview(40);
    return { changed: true };
  }

  function handleKeyDown(state, event, deps) {
    const command = deps.keyboardActions.keyboardCommand(event, state);
    if (command.type === "undo") {
      deps.undo();
      event.preventDefault();
      return { handled: true, command };
    }
    if (command.type === "redo") {
      deps.redo();
      event.preventDefault();
      return { handled: true, command };
    }
    if (command.type === "duplicate") {
      duplicateSelected(state, deps);
      event.preventDefault();
      return { handled: true, command };
    }
    if (command.type === "delete") {
      deleteSelected(state, deps);
      event.preventDefault();
      return { handled: true, command };
    }
    if (command.type !== "move") {
      return { handled: false, command };
    }
    const element = deps.selectedElement();
    if (!deps.keyboardActions.moveSelectedElement(state, element, command, deps.editor)) {
      return { handled: false, command };
    }
    deps.markDirty();
    deps.renderAll();
    deps.schedulePreview(50);
    event.preventDefault();
    return { handled: true, command };
  }

  const api = {
    bumpZ,
    deleteSelected,
    duplicateSelected,
    handleKeyDown,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorCommandActions = api;
})(typeof window !== "undefined" ? window : globalThis);
