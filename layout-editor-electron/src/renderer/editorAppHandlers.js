(function exposeEditorAppHandlers(globalScope) {
  const CommandHandlers =
    globalScope.EditorAppCommandHandlers ||
    (typeof require !== "undefined" ? require("./editorAppCommandHandlers.js") : null);
  const RenderHandlers =
    globalScope.EditorAppRenderHandlers ||
    (typeof require !== "undefined" ? require("./editorAppRenderHandlers.js") : null);
  const ViewHandlers =
    globalScope.EditorAppViewHandlers || (typeof require !== "undefined" ? require("./editorAppViewHandlers.js") : null);

  function createAppHandlers(context) {
    const viewHandlers = ViewHandlers.createAppViewHandlers(context);
    const commandHandlers = CommandHandlers.createAppCommandHandlers({
      ...context,
      selectedElement: viewHandlers.selectedElement,
    });
    const renderHandlers = RenderHandlers.createAppRenderHandlers(context);

    return {
      ...viewHandlers,
      ...commandHandlers,
      ...renderHandlers,
    };
  }

  const api = {
    createAppHandlers,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppHandlers = api;
})(typeof window !== "undefined" ? window : globalThis);
