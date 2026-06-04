(function exposeEditorAppRuntime(globalScope) {
  function collectWindowModules(windowRef) {
    return {
      appBootstrap: windowRef.EditorAppBootstrap,
      appCommandHandlers: windowRef.EditorAppCommandHandlers,
      appDeps: windowRef.EditorAppDeps,
      appHandlers: windowRef.EditorAppHandlers,
      appRenderHandlers: windowRef.EditorAppRenderHandlers,
      appState: windowRef.EditorAppState,
      appViewHandlers: windowRef.EditorAppViewHandlers,
      backgroundActions: windowRef.EditorBackgroundActions,
      commandActions: windowRef.EditorCommandActions,
      contextActions: windowRef.EditorContextActions,
      contextCommands: windowRef.EditorContextCommands,
      domActions: windowRef.EditorDomActions,
      domBindings: windowRef.EditorDomBindings,
      dragActions: windowRef.EditorDragActions,
      dragGhost: windowRef.DragGhost,
      editActions: windowRef.EditorEditActions,
      editor: windowRef.EditorState,
      elementActions: windowRef.EditorElementActions,
      fileActions: windowRef.EditorFileActions,
      fileCommands: windowRef.EditorFileCommands,
      history: windowRef.EditorHistory,
      historyCommands: windowRef.EditorHistoryCommands,
      i18n: windowRef.EditorI18n,
      inspectorView: windowRef.EditorInspectorView,
      keyboardActions: windowRef.EditorKeyboardActions,
      layerView: windowRef.EditorLayerView,
      overlayView: windowRef.EditorOverlayView,
      paletteView: windowRef.EditorPaletteView,
      pointerActions: windowRef.EditorPointerActions,
      previewActions: windowRef.EditorPreviewActions,
      propertyActions: windowRef.EditorPropertyActions,
      renderCoordinator: windowRef.EditorRenderCoordinator,
      topControls: windowRef.EditorTopControls,
      vehicleLiveActions: windowRef.EditorVehicleLiveActions,
      vehicleLiveState: windowRef.EditorVehicleLiveState,
      vehicleLiveView: windowRef.EditorVehicleLiveView,
      viewModel: windowRef.EditorViewModel,
      weatherActions: windowRef.EditorWeatherActions,
    };
  }

  function createAppRuntime({ modules, refs, handlers }) {
    return {
      ...handlers,
      contextActions: modules.contextActions,
      documentRef: refs.documentRef,
      dom: refs.dom,
      domBindings: modules.domBindings,
      dragActions: modules.dragActions,
      dragGhost: modules.dragGhost,
      editor: modules.editor,
      elementActions: modules.elementActions,
      fileActions: modules.fileActions,
      history: modules.history,
      i18n: modules.i18n,
      inspectorView: modules.inspectorView,
      keyboardActions: modules.keyboardActions,
      layerView: modules.layerView,
      localStorageRef: refs.localStorageRef,
      navigatorRef: refs.navigatorRef,
      overlayView: modules.overlayView,
      paletteView: modules.paletteView,
      pointerActions: modules.pointerActions,
      propertyActions: modules.propertyActions,
      requestAnimationFrameRef: refs.requestAnimationFrameRef,
      topControls: modules.topControls,
      vehicleLiveActions: modules.vehicleLiveActions,
      vehicleLiveState: modules.vehicleLiveState,
      vehicleLiveView: modules.vehicleLiveView,
      viewModel: modules.viewModel,
      windowRef: refs.windowRef,
    };
  }

  const api = {
    collectWindowModules,
    createAppRuntime,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppRuntime = api;
})(typeof window !== "undefined" ? window : globalThis);
