(function exposeEditorAppDeps(globalScope) {
  const StartupDeps =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorAppStartupDeps.js")
      : globalScope.EditorAppStartupDeps;
  const RenderDeps =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorAppRenderDeps.js")
      : globalScope.EditorAppRenderDeps;
  const CommandDeps =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorAppCommandDeps.js")
      : globalScope.EditorAppCommandDeps;

  const api = {
    appBootstrapDeps: StartupDeps.appBootstrapDeps,
    backgroundActionDeps: CommandDeps.backgroundActionDeps,
    commandActionDeps: CommandDeps.commandActionDeps,
    contextCommandDeps: CommandDeps.contextCommandDeps,
    editActionDeps: CommandDeps.editActionDeps,
    editorEventHandlers: StartupDeps.editorEventHandlers,
    fileCommandDeps: CommandDeps.fileCommandDeps,
    historyCommandDeps: CommandDeps.historyCommandDeps,
    pointerActionDeps: CommandDeps.pointerActionDeps,
    previewDeps: RenderDeps.previewDeps,
    renderCoordinatorDeps: RenderDeps.renderCoordinatorDeps,
    weatherActionDeps: CommandDeps.weatherActionDeps,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppDeps = api;
})(typeof window !== "undefined" ? window : globalThis);
