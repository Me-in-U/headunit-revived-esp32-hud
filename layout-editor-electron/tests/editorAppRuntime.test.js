const assert = require("node:assert/strict");
const test = require("node:test");

const AppRuntime = require("../src/renderer/editorAppRuntime.js");

test("collectWindowModules gathers renderer module references from window", () => {
  const windowRef = {
    EditorState: {},
    EditorBackgroundActions: {},
    EditorCommandActions: {},
    EditorContextActions: {},
    EditorContextCommands: {},
    EditorFileActions: {},
    EditorFileCommands: {},
    DragGhost: {},
    EditorViewModel: {},
    EditorI18n: {},
    EditorAppCommandHandlers: {},
    EditorAppHandlers: {},
    EditorAppRenderHandlers: {},
    EditorAppState: {},
    EditorAppViewHandlers: {},
    EditorAppBootstrap: {},
    EditorAppDeps: {},
    EditorHistory: {},
    EditorHistoryCommands: {},
    EditorElementActions: {},
    EditorPropertyActions: {},
    EditorDragActions: {},
    EditorDomActions: {},
    EditorDomBindings: {},
    EditorEditActions: {},
    EditorInspectorView: {},
    EditorKeyboardActions: {},
    EditorLayerView: {},
    EditorOverlayView: {},
    EditorPaletteView: {},
    EditorPointerActions: {},
    EditorPreviewActions: {},
    EditorRenderCoordinator: {},
    EditorTopControls: {},
    EditorWeatherActions: {},
  };

  const modules = AppRuntime.collectWindowModules(windowRef);

  assert.equal(modules.editor, windowRef.EditorState);
  assert.equal(modules.backgroundActions, windowRef.EditorBackgroundActions);
  assert.equal(modules.appState, windowRef.EditorAppState);
  assert.equal(modules.appCommandHandlers, windowRef.EditorAppCommandHandlers);
  assert.equal(modules.appHandlers, windowRef.EditorAppHandlers);
  assert.equal(modules.appRenderHandlers, windowRef.EditorAppRenderHandlers);
  assert.equal(modules.appViewHandlers, windowRef.EditorAppViewHandlers);
  assert.equal(modules.appBootstrap, windowRef.EditorAppBootstrap);
  assert.equal(modules.appDeps, windowRef.EditorAppDeps);
  assert.equal(modules.renderCoordinator, windowRef.EditorRenderCoordinator);
});

test("createAppRuntime merges modules refs and app handlers into command runtime", () => {
  const modules = {
    contextActions: {},
    domBindings: {},
    dragActions: {},
    dragGhost: {},
    editor: {},
    elementActions: {},
    fileActions: {},
    history: {},
    i18n: {},
    inspectorView: {},
    keyboardActions: {},
    layerView: {},
    overlayView: {},
    paletteView: {},
    pointerActions: {},
    propertyActions: {},
    topControls: {},
    viewModel: {},
  };
  const refs = {
    documentRef: {},
    dom: {},
    localStorageRef: {},
    navigatorRef: {},
    requestAnimationFrameRef: () => {},
    windowRef: {},
  };
  const handlers = {
    applyLanguage() {},
    applyLoadedLayout() {},
    bumpZ() {},
    canvasScale() {},
    chooseBackgroundImage() {},
    clearBackgroundImage() {},
    confirmDiscardChanges() {},
    deleteSelected() {},
    duplicateSelected() {},
    elementById() {},
    eventToCanvas() {},
    exportFieldPack() {},
    exportSnapshot() {},
    fetchWeather() {},
    hideValidationDrawer() {},
    hitTest() {},
    importOtherScreen() {},
    markDirty() {},
    onBackgroundColor() {},
    onKeyDown() {},
    onLanguageChange() {},
    onPointerDown() {},
    onPointerMove() {},
    onPointerUp() {},
    onPropertyInput() {},
    onScreenChange() {},
    onVehicleChange() {},
    openLayout() {},
    propertyLabel() {},
    pushUndoSnapshot() {},
    recordHistory() {},
    redo() {},
    renderAll() {},
    renderLayers() {},
    renderOverlay() {},
    renderPalette() {},
    renderPreview() {},
    renderProperties() {},
    renderTopControls() {},
    resetDefaultLayout() {},
    saveLayout() {},
    schedulePreview() {},
    selectedElement() {},
    selectPaletteVariant() {},
    setStatus() {},
    showValidationDrawer() {},
    snapshotState() {},
    translate() {},
    undo() {},
    updateFilePath() {},
    validateLayout() {},
  };

  const runtime = AppRuntime.createAppRuntime({ modules, refs, handlers });

  assert.equal(runtime.editor, modules.editor);
  assert.equal(runtime.dom, refs.dom);
  assert.equal(runtime.requestAnimationFrameRef, refs.requestAnimationFrameRef);
  assert.equal(runtime.renderAll, handlers.renderAll);
  assert.equal(runtime.pointerActions, modules.pointerActions);
  assert.equal(runtime.windowRef, refs.windowRef);
});
