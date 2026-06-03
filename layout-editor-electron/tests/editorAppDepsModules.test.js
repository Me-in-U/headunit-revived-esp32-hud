const assert = require("node:assert/strict");
const test = require("node:test");

const AppDeps = require("../src/renderer/editorAppDeps.js");
const StartupDeps = require("../src/renderer/editorAppStartupDeps.js");
const RenderDeps = require("../src/renderer/editorAppRenderDeps.js");
const CommandDeps = require("../src/renderer/editorAppCommandDeps.js");

test("startup deps module matches the compatibility app deps API", () => {
  const runtime = runtimeDeps();

  assert.deepEqual(StartupDeps.appBootstrapDeps(runtime), AppDeps.appBootstrapDeps(runtime));
  assert.deepEqual(Object.keys(StartupDeps.editorEventHandlers(runtime)).sort(), Object.keys(AppDeps.editorEventHandlers(runtime)).sort());
});

test("render deps module preserves render coordinator and preview dependencies", async () => {
  const calls = [];
  const runtime = runtimeDeps(calls);

  assert.deepEqual(RenderDeps.renderCoordinatorDeps(runtime), AppDeps.renderCoordinatorDeps(runtime));
  await RenderDeps.previewDeps(runtime).renderPreview("request");
  RenderDeps.previewDeps(runtime).hideDragGhost();

  assert.deepEqual(calls, [
    ["renderPreview", "request"],
    ["hideDragGhost", runtime.dom],
  ]);
});

test("command deps module preserves command and action dependency contracts", () => {
  const runtime = runtimeDeps();

  assert.deepEqual(CommandDeps.fileCommandDeps(runtime).pixelStatus, AppDeps.fileCommandDeps(runtime).pixelStatus);
  assert.deepEqual(CommandDeps.weatherActionDeps(runtime), AppDeps.weatherActionDeps(runtime));
  assert.deepEqual(CommandDeps.contextCommandDeps(runtime), AppDeps.contextCommandDeps(runtime));
  assert.deepEqual(CommandDeps.backgroundActionDeps(runtime), AppDeps.backgroundActionDeps(runtime));
  assert.deepEqual(CommandDeps.editActionDeps(runtime), AppDeps.editActionDeps(runtime));
  assert.deepEqual(CommandDeps.pointerActionDeps(runtime), AppDeps.pointerActionDeps(runtime));
  assert.deepEqual(CommandDeps.commandActionDeps(runtime), AppDeps.commandActionDeps(runtime));
  assert.deepEqual(CommandDeps.historyCommandDeps(runtime), AppDeps.historyCommandDeps(runtime));
});

function runtimeDeps(calls = []) {
  const fn = (name) => function action(...args) {
    calls.push([name, ...args]);
  };
  return {
    applyLanguage: fn("applyLanguage"),
    applyLoadedLayout: fn("applyLoadedLayout"),
    bumpZ: fn("bumpZ"),
    canvasScale: fn("canvasScale"),
    chooseBackgroundImage: fn("chooseBackgroundImage"),
    clearBackgroundImage: fn("clearBackgroundImage"),
    confirmDiscardChanges: fn("confirmDiscardChanges"),
    contextActions: { name: "contextActions" },
    deleteSelected: fn("deleteSelected"),
    documentRef: { name: "document" },
    dom: { pixelStatus: { textContent: "" } },
    domBindings: { name: "domBindings" },
    dragActions: { name: "dragActions" },
    dragGhost: { name: "dragGhost" },
    duplicateSelected: fn("duplicateSelected"),
    editor: { name: "editor" },
    elementActions: { name: "elementActions" },
    elementById: fn("elementById"),
    eventToCanvas: fn("eventToCanvas"),
    exportFieldPack: fn("exportFieldPack"),
    exportSnapshot: fn("exportSnapshot"),
    fetchWeather: fn("fetchWeather"),
    fileActions: { name: "fileActions" },
    hideValidationDrawer: fn("hideValidationDrawer"),
    hitTest: fn("hitTest"),
    history: { name: "history" },
    i18n: { name: "i18n" },
    importOtherScreen: fn("importOtherScreen"),
    inspectorView: { name: "inspectorView" },
    keyboardActions: { name: "keyboardActions" },
    layerView: { name: "layerView" },
    localStorageRef: { name: "localStorage" },
    markDirty: fn("markDirty"),
    onBackgroundColor: fn("onBackgroundColor"),
    onKeyDown: fn("onKeyDown"),
    onLanguageChange: fn("onLanguageChange"),
    onPointerDown: fn("onPointerDown"),
    onPointerMove: fn("onPointerMove"),
    onPointerUp: fn("onPointerUp"),
    onPropertyInput: fn("onPropertyInput"),
    onScreenChange: fn("onScreenChange"),
    onVehicleChange: fn("onVehicleChange"),
    openLayout: fn("openLayout"),
    overlayView: { name: "overlayView" },
    paletteView: { name: "paletteView" },
    pointerActions: { hideDragGhost: fn("hideDragGhost") },
    propertyActions: { name: "propertyActions" },
    propertyLabel: fn("propertyLabel"),
    pushUndoSnapshot: fn("pushUndoSnapshot"),
    recordHistory: fn("recordHistory"),
    redo: fn("redo"),
    renderAll: fn("renderAll"),
    renderLayers: fn("renderLayers"),
    renderOverlay: fn("renderOverlay"),
    renderPalette: fn("renderPalette"),
    renderPreview: fn("renderPreview"),
    renderProperties: fn("renderProperties"),
    renderTopControls: fn("renderTopControls"),
    requestAnimationFrameRef: fn("requestAnimationFrame"),
    resetDefaultLayout: fn("resetDefaultLayout"),
    saveLayout: fn("saveLayout"),
    schedulePreview: fn("schedulePreview"),
    selectedElement: fn("selectedElement"),
    selectPaletteVariant: fn("selectPaletteVariant"),
    setStatus: fn("setStatus"),
    showValidationDrawer: fn("showValidationDrawer"),
    snapshotState: fn("snapshotState"),
    topControls: { name: "topControls" },
    translate: (key) => `t:${key}`,
    undo: fn("undo"),
    updateFilePath: fn("updateFilePath"),
    validateLayout: fn("validateLayout"),
    viewModel: { name: "viewModel" },
    windowRef: {
      confirm(message) {
        calls.push(["confirm", message]);
        return true;
      },
      hudEditor: {
        renderPreview(request) {
          calls.push(["renderPreview", request]);
          return Promise.resolve({ ok: true });
        },
      },
    },
  };
}
