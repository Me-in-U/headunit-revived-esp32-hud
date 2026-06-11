const assert = require("node:assert/strict");
const test = require("node:test");

const AppDeps = require("../src/renderer/editorAppDeps.js");

test("editorEventHandlers exposes the complete DOM action handler map", () => {
  const runtime = runtimeDeps();
  const handlers = AppDeps.editorEventHandlers(runtime);

  assert.deepEqual(Object.keys(handlers).sort(), [
    "addObdProbeCommand",
    "bumpZ",
    "chooseBackgroundImage",
    "clearBackgroundImage",
    "copyLiveSample",
    "deleteSelected",
    "duplicateSelected",
    "editObdPidDefinition",
    "exportFieldPack",
    "exportSnapshot",
    "fetchWeather",
    "hideValidationDrawer",
    "importOtherScreen",
    "inspectObdBle",
    "onBackgroundColor",
    "onKeyDown",
    "onLanguageChange",
    "onPointerDown",
    "onPointerMove",
    "onPointerUp",
    "onScreenChange",
    "onSimulationToggle",
    "onVehicleChange",
    "onVehicleLiveEvent",
    "openLayout",
    "redo",
    "renderOverlay",
    "renderPalette",
    "resetDefaultLayout",
    "saveCanSignal",
    "saveLayout",
    "saveObdPidDefinition",
    "scanComPorts",
    "scanObdBle",
    "scanObdComPorts",
    "selectCanPort",
    "selectComPort",
    "selectObdDevice",
    "selectObdSerialPort",
    "selectToolTab",
    "startCanLive",
    "startObdLive",
    "startVehicleLive",
    "stopCanLive",
    "stopObdLive",
    "stopVehicleLive",
    "undo",
    "validateLayout",
  ]);
  assert.equal(handlers.openLayout, runtime.openLayout);
  assert.equal(handlers.bumpZ, runtime.bumpZ);
});

test("appBootstrapDeps maps startup services and handler bindings", () => {
  const runtime = runtimeDeps();
  const deps = AppDeps.appBootstrapDeps(runtime);

  assert.equal(deps.applyLanguage, runtime.applyLanguage);
  assert.equal(deps.documentRef, runtime.documentRef);
  assert.equal(deps.domBindings, runtime.domBindings);
  assert.equal(deps.handlers.saveLayout, runtime.saveLayout);
  assert.equal(deps.handlers.saveObdPidDefinition, runtime.saveObdPidDefinition);
  assert.equal(deps.handlers.editObdPidDefinition, runtime.editObdPidDefinition);
  assert.equal(deps.handlers.scanObdComPorts, runtime.scanObdComPorts);
  assert.equal(deps.handlers.startObdLive, runtime.startObdLive);
  assert.equal(deps.handlers.startCanLive, runtime.startCanLive);
  assert.equal(deps.handlers.onVehicleLiveEvent, runtime.onVehicleLiveEvent);
  assert.equal(deps.hudEditor, runtime.windowRef.hudEditor);
  assert.equal(deps.windowRef, runtime.windowRef);
});

test("preview and file deps wrap window services and drag ghost hiding", async () => {
  const calls = [];
  const runtime = runtimeDeps(calls);

  const previewDeps = AppDeps.previewDeps(runtime);
  await previewDeps.renderPreview({ layout: "request" });
  previewDeps.hideDragGhost();

  const fileDeps = AppDeps.fileCommandDeps(runtime);
  assert.equal(fileDeps.confirm("discard?"), true);
  fileDeps.hideDragGhost();

  assert.deepEqual(calls, [
    ["renderPreview", { layout: "request" }],
    ["hideDragGhost", runtime.dom],
    ["confirm", "discard?"],
    ["hideDragGhost", runtime.dom],
  ]);
  assert.equal(fileDeps.pixelStatus, runtime.dom.pixelStatus);
  assert.equal(fileDeps.renderAll, runtime.renderAll);
});

test("action dependency factories preserve command module contracts", () => {
  const runtime = runtimeDeps();

  assert.deepEqual(AppDeps.weatherActionDeps(runtime), {
    markDirty: runtime.markDirty,
    recordHistory: runtime.recordHistory,
    renderAll: runtime.renderAll,
    schedulePreview: runtime.schedulePreview,
    setStatus: runtime.setStatus,
    translate: runtime.translate,
  });
  assert.equal(AppDeps.contextCommandDeps(runtime).localStorageRef, runtime.localStorageRef);
  assert.equal(AppDeps.backgroundActionDeps(runtime).recordHistory, runtime.recordHistory);
  assert.equal(AppDeps.editActionDeps(runtime).propertyActions, runtime.propertyActions);
  assert.equal(AppDeps.pointerActionDeps(runtime).dragGhost, runtime.dragGhost);
  assert.equal(AppDeps.commandActionDeps(runtime).keyboardActions, runtime.keyboardActions);
  assert.equal(AppDeps.historyCommandDeps(runtime).history, runtime.history);
  assert.equal(AppDeps.renderCoordinatorDeps(runtime).paletteView, runtime.paletteView);
  assert.equal(AppDeps.vehicleLiveActionDeps(runtime).vehicleLiveState, runtime.vehicleLiveState);
  assert.equal(AppDeps.vehicleLiveActionDeps(runtime).renderVehicleTools, runtime.renderVehicleTools);
});

function runtimeDeps(calls = []) {
  const fn = (name) => function action(...args) {
    calls.push([name, ...args]);
  };
  return {
    applyLanguage: fn("applyLanguage"),
    applyLoadedLayout: fn("applyLoadedLayout"),
    backgroundActions: { name: "backgroundActions" },
    addObdProbeCommand: fn("addObdProbeCommand"),
    bumpZ: fn("bumpZ"),
    canvasScale: fn("canvasScale"),
    chooseBackgroundImage: fn("chooseBackgroundImage"),
    clearBackgroundImage: fn("clearBackgroundImage"),
    commandActions: { name: "commandActions" },
    confirmDiscardChanges: fn("confirmDiscardChanges"),
    contextActions: { name: "contextActions" },
    copyLiveSample: fn("copyLiveSample"),
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
    exportFieldPack: fn("exportFieldPack"),
    exportSnapshot: fn("exportSnapshot"),
    fetchWeather: fn("fetchWeather"),
    fileActions: { name: "fileActions" },
    hideValidationDrawer: fn("hideValidationDrawer"),
    hitTest: fn("hitTest"),
    history: { name: "history" },
    i18n: { name: "i18n" },
    importOtherScreen: fn("importOtherScreen"),
    inspectObdBle: fn("inspectObdBle"),
    inspectorView: { name: "inspectorView" },
    keyboardActions: { name: "keyboardActions" },
    layerView: { name: "layerView" },
    localStorageRef: { name: "localStorage" },
    markDirty: fn("markDirty"),
    navigatorRef: { name: "navigator" },
    onBackgroundColor: fn("onBackgroundColor"),
    onKeyDown: fn("onKeyDown"),
    onLanguageChange: fn("onLanguageChange"),
    onSimulationToggle: fn("onSimulationToggle"),
    onVehicleLiveEvent: fn("onVehicleLiveEvent"),
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
    renderVehicleTools: fn("renderVehicleTools"),
    requestAnimationFrameRef: fn("requestAnimationFrame"),
    resetDefaultLayout: fn("resetDefaultLayout"),
    saveLayout: fn("saveLayout"),
    saveCanSignal: fn("saveCanSignal"),
    schedulePreview: fn("schedulePreview"),
    scanComPorts: fn("scanComPorts"),
    scanObdBle: fn("scanObdBle"),
    scanObdComPorts: fn("scanObdComPorts"),
    selectCanPort: fn("selectCanPort"),
    selectComPort: fn("selectComPort"),
    selectObdDevice: fn("selectObdDevice"),
    selectObdSerialPort: fn("selectObdSerialPort"),
    selectedElement: fn("selectedElement"),
    selectToolTab: fn("selectToolTab"),
    selectPaletteVariant: fn("selectPaletteVariant"),
    setStatus: fn("setStatus"),
    showValidationDrawer: fn("showValidationDrawer"),
    snapshotState: fn("snapshotState"),
    startCanLive: fn("startCanLive"),
    startObdLive: fn("startObdLive"),
    startVehicleLive: fn("startVehicleLive"),
    stopCanLive: fn("stopCanLive"),
    stopObdLive: fn("stopObdLive"),
    stopVehicleLive: fn("stopVehicleLive"),
    topControls: { name: "topControls" },
    translate: (key) => `t:${key}`,
    undo: fn("undo"),
    updateFilePath: fn("updateFilePath"),
    validateLayout: fn("validateLayout"),
    vehicleLiveState: { name: "vehicleLiveState" },
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
