(function exposeEditorHistory(globalScope) {
  const DEFAULT_UNDO_LIMIT = 50;

  function defaultClone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function snapshotState(state, clone = defaultClone) {
    return {
      layout: clone(state.layout),
      currentScreen: state.currentScreen,
      selectedId: state.selectedId,
    };
  }

  function recordHistory(state, clone = defaultClone, limit = DEFAULT_UNDO_LIMIT) {
    if (!state.layout || state.history?.applying) {
      return false;
    }
    pushUndoSnapshot(state.history, snapshotState(state, clone), limit);
    state.history.redo = [];
    return true;
  }

  function pushUndoSnapshot(history, snapshot, limit = DEFAULT_UNDO_LIMIT) {
    if (!history || !snapshot) {
      return false;
    }
    history.undo.push(snapshot);
    if (history.undo.length > limit) {
      history.undo.shift();
    }
    return true;
  }

  function restoreSnapshot(state, snapshot, clone = defaultClone) {
    if (!snapshot) {
      return false;
    }
    state.history.applying = true;
    state.layout = clone(snapshot.layout);
    state.currentScreen = snapshot.currentScreen;
    state.selectedId = snapshot.selectedId || "";
    state.dirty = true;
    state.history.applying = false;
    return true;
  }

  function undo(state, clone = defaultClone) {
    if (!state.history.undo.length) {
      return false;
    }
    state.history.redo.push(snapshotState(state, clone));
    return restoreSnapshot(state, state.history.undo.pop(), clone);
  }

  function redo(state, clone = defaultClone) {
    if (!state.history.redo.length) {
      return false;
    }
    state.history.undo.push(snapshotState(state, clone));
    return restoreSnapshot(state, state.history.redo.pop(), clone);
  }

  const api = {
    DEFAULT_UNDO_LIMIT,
    pushUndoSnapshot,
    recordHistory,
    redo,
    restoreSnapshot,
    snapshotState,
    undo,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorHistory = api;
})(typeof window !== "undefined" ? window : globalThis);
