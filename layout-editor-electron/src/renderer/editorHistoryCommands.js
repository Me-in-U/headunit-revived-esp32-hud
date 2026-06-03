(function exposeEditorHistoryCommands(globalScope) {
  function markDirtyCommand(state, deps) {
    state.dirty = true;
    deps.editor.syncCurrentScreen(state.layout, state.currentScreen);
    deps.updateFilePath();
    deps.renderTopControls();
  }

  function snapshotStateCommand(state, deps) {
    return deps.history.snapshotState(state, deps.editor.clone);
  }

  function recordHistoryCommand(state, deps) {
    if (deps.history.recordHistory(state, deps.editor.clone)) {
      deps.renderTopControls();
      return true;
    }
    return false;
  }

  function pushUndoSnapshotCommand(state, snapshot, deps) {
    deps.history.pushUndoSnapshot(state.history, snapshot);
  }

  function undoCommand(state, deps) {
    if (deps.history.undo(state, deps.editor.clone)) {
      deps.renderAll();
      deps.schedulePreview(30);
      return true;
    }
    return false;
  }

  function redoCommand(state, deps) {
    if (deps.history.redo(state, deps.editor.clone)) {
      deps.renderAll();
      deps.schedulePreview(30);
      return true;
    }
    return false;
  }

  const api = {
    markDirtyCommand,
    pushUndoSnapshotCommand,
    recordHistoryCommand,
    redoCommand,
    snapshotStateCommand,
    undoCommand,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorHistoryCommands = api;
})(typeof window !== "undefined" ? window : globalThis);
