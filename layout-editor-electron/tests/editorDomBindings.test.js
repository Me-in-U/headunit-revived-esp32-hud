const test = require("node:test");
const assert = require("node:assert/strict");

const DomBindings = require("../src/renderer/editorDomBindings.js");

function fakeElement(id) {
  const listeners = {};
  return {
    id,
    value: "",
    listeners,
    addEventListener(type, handler) {
      listeners[type] = handler;
    },
  };
}

test("bindDom maps required editor element ids into the shared dom object", () => {
  const requested = [];
  const elements = new Map();
  const documentRef = {
    getElementById(id) {
      requested.push(id);
      const element = fakeElement(id);
      elements.set(id, element);
      return element;
    },
  };
  const dom = {};

  const result = DomBindings.bindDom(dom, documentRef);

  assert.equal(result, dom);
  assert.equal(dom.filePath, elements.get("filePath"));
  assert.equal(dom.paletteSearch, elements.get("paletteSearch"));
  assert.equal(dom.layerList, elements.get("layerList"));
  assert.equal(dom.validationDrawer, elements.get("validationDrawer"));
  assert.equal(dom.simulationToggle, elements.get("simulationToggle"));
  assert.equal(dom.connectionPanel, elements.get("connectionPanel"));
  assert.equal(dom.canAnalysisPanel, elements.get("canAnalysisPanel"));
  assert.equal(dom.obdAnalysisPanel, elements.get("obdAnalysisPanel"));
  assert.equal(dom.obdDeviceList, elements.get("obdDeviceList"));
  assert.equal(dom.obdSelectedStatus, elements.get("obdSelectedStatus"));
  assert.equal(dom.scanComPortsBtn, elements.get("scanComPortsBtn"));
  assert.equal(dom.comPortList, elements.get("comPortList"));
  assert.equal(dom.comSelectedStatus, elements.get("comSelectedStatus"));
  assert.equal(dom.liveCanStatus, elements.get("liveCanStatus"));
  assert.equal(dom.liveObdStatus, elements.get("liveObdStatus"));
  assert.equal(dom.liveLogList, elements.get("liveLogList"));
  assert.equal(dom.obdAdapterIdentity, elements.get("obdAdapterIdentity"));
  assert.equal(dom.obdProtocol, elements.get("obdProtocol"));
  assert.equal(dom.obdSupportedPids, elements.get("obdSupportedPids"));
  assert.equal(dom.obdDtcList, elements.get("obdDtcList"));
  assert.equal(requested.includes("previewStage"), true);
});

test("bindActions wires editor buttons and palette search behavior", () => {
  const dom = {};
  for (const id of DomBindings.DOM_IDS) {
    dom[id] = fakeElement(id);
  }
  const state = { paletteQuery: "" };
  const calls = [];
  const windowRef = {
    listeners: {},
    addEventListener(type, handler) {
      this.listeners[type] = handler;
    },
  };
  const handlers = {
    openLayout: () => calls.push(["openLayout"]),
    saveLayout: (saveAs) => calls.push(["saveLayout", saveAs]),
    undo: () => calls.push(["undo"]),
    redo: () => calls.push(["redo"]),
    resetDefaultLayout: () => calls.push(["resetDefaultLayout"]),
    validateLayout: () => calls.push(["validateLayout"]),
    exportSnapshot: () => calls.push(["exportSnapshot"]),
    exportFieldPack: () => calls.push(["exportFieldPack"]),
    onVehicleChange: () => calls.push(["onVehicleChange"]),
    onScreenChange: () => calls.push(["onScreenChange"]),
    importOtherScreen: () => calls.push(["importOtherScreen"]),
    onLanguageChange: () => calls.push(["onLanguageChange"]),
    fetchWeather: () => calls.push(["fetchWeather"]),
    onBackgroundColor: () => calls.push(["onBackgroundColor"]),
    onSimulationToggle: () => calls.push(["onSimulationToggle"]),
    selectToolTab: (tab) => calls.push(["selectToolTab", tab]),
    scanObdBle: () => calls.push(["scanObdBle"]),
    selectObdDevice: (address) => calls.push(["selectObdDevice", address]),
    scanComPorts: () => calls.push(["scanComPorts"]),
    selectComPort: (device) => calls.push(["selectComPort", device]),
    inspectObdBle: () => calls.push(["inspectObdBle"]),
    startVehicleLive: () => calls.push(["startVehicleLive"]),
    stopVehicleLive: () => calls.push(["stopVehicleLive"]),
    copyLiveSample: () => calls.push(["copyLiveSample"]),
    saveCanSignal: () => calls.push(["saveCanSignal"]),
    addObdProbeCommand: () => calls.push(["addObdProbeCommand"]),
    chooseBackgroundImage: () => calls.push(["chooseBackgroundImage"]),
    clearBackgroundImage: () => calls.push(["clearBackgroundImage"]),
    renderPalette: () => calls.push(["renderPalette"]),
    hideValidationDrawer: () => calls.push(["hideValidationDrawer"]),
    deleteSelected: () => calls.push(["deleteSelected"]),
    duplicateSelected: () => calls.push(["duplicateSelected"]),
    bumpZ: (delta) => calls.push(["bumpZ", delta]),
    renderOverlay: () => calls.push(["renderOverlay"]),
    onPointerDown: () => calls.push(["onPointerDown"]),
    onPointerMove: () => calls.push(["onPointerMove"]),
    onPointerUp: () => calls.push(["onPointerUp"]),
    onKeyDown: () => calls.push(["onKeyDown"]),
  };

  DomBindings.bindActions(dom, windowRef, state, handlers);
  dom.openBtn.listeners.click();
  dom.saveBtn.listeners.click();
  dom.saveAsBtn.listeners.click();
  dom.paletteSearch.value = "  SPEED  ";
  dom.paletteSearch.listeners.input();
  dom.simulationToggle.listeners.change();
  dom.connectionTab.listeners.click();
  dom.scanObdBtn.listeners.click();
  dom.obdDeviceList.listeners.click({ target: { closest: () => ({ dataset: { obdAddress: "AA:BB" } }) } });
  dom.scanComPortsBtn.listeners.click();
  dom.comPortList.listeners.click({ target: { closest: () => ({ dataset: { comPort: "COM7" } }) } });
  dom.inspectObdBtn.listeners.click();
  dom.startVehicleLiveBtn.listeners.click();
  dom.stopVehicleLiveBtn.listeners.click();
  dom.copyLiveSampleBtn.listeners.click();
  dom.saveCanSignalBtn.listeners.click();
  dom.addObdProbeBtn.listeners.click();
  dom.frontBtn.listeners.click();
  dom.backBtn.listeners.click();
  dom.selectionOverlay.listeners.pointerdown();
  windowRef.listeners.resize();
  windowRef.listeners.keydown();

  assert.deepEqual(calls, [
    ["openLayout"],
    ["saveLayout", false],
    ["saveLayout", true],
    ["renderPalette"],
    ["onSimulationToggle"],
    ["selectToolTab", "connection"],
    ["scanObdBle"],
    ["selectObdDevice", "AA:BB"],
    ["scanComPorts"],
    ["selectComPort", "COM7"],
    ["inspectObdBle"],
    ["startVehicleLive"],
    ["stopVehicleLive"],
    ["copyLiveSample"],
    ["saveCanSignal"],
    ["addObdProbeCommand"],
    ["bumpZ", 1],
    ["bumpZ", -1],
    ["onPointerDown"],
    ["renderOverlay"],
    ["onKeyDown"],
  ]);
  assert.equal(state.paletteQuery, "speed");
  assert.equal(windowRef.listeners.pointermove, handlers.onPointerMove);
  assert.equal(windowRef.listeners.pointerup, handlers.onPointerUp);
});
