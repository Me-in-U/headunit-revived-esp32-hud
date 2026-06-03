(function exposeEditorContextCommands(globalScope) {
  function applyVehicleCommand(state, vehicle, deps) {
    deps.recordHistory();
    deps.contextActions.applyVehicleSelection(state, vehicle, deps.editor);
    deps.markDirty();
  }

  function applyScreenCommand(state, screen, deps) {
    deps.contextActions.applyScreenSelection(state, screen, deps.editor);
    deps.renderAll();
    deps.schedulePreview(40);
  }

  function importOtherScreenCommand(state, deps) {
    deps.recordHistory();
    deps.contextActions.importOtherScreen(state, deps.editor);
    deps.markDirty();
    deps.renderAll();
    deps.schedulePreview(40);
  }

  function applyLanguageCommand(state, language, deps) {
    deps.contextActions.applyLanguageSelection(state, language, deps.i18n, deps.localStorageRef);
    deps.applyLanguage();
    deps.renderAll();
  }

  const api = {
    applyLanguageCommand,
    applyScreenCommand,
    applyVehicleCommand,
    importOtherScreenCommand,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorContextCommands = api;
})(typeof window !== "undefined" ? window : globalThis);
