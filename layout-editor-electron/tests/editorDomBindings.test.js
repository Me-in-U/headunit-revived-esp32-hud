const test = require("node:test");
const assert = require("node:assert/strict");

const DomBindings = require("../src/renderer/editorDomBindings.js");

function fakeElement(id) {
  const listeners = {};
  const element = {
    id,
    attributes: {},
    className: id === "canvasPanel" ? "canvas-panel" : "",
    textContent: "",
    value: "",
    listeners,
    classList: {
      toggle(className, enabled) {
        const classNames = new Set(String(element.className || "").split(/\s+/).filter(Boolean));
        if (enabled) {
          classNames.add(className);
        } else {
          classNames.delete(className);
        }
        element.className = [...classNames].join(" ");
      },
    },
    addEventListener(type, handler) {
      listeners[type] = handler;
    },
    setAttribute(name, value) {
      this.attributes[name] = value;
    },
  };
  return element;
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
  assert.equal(dom.obdSerialPort, elements.get("obdSerialPort"));
  assert.equal(dom.obdSerialBaud, elements.get("obdSerialBaud"));
  assert.equal(dom.scanObdComPortsBtn, elements.get("scanObdComPortsBtn"));
  assert.equal(dom.obdSerialPortList, elements.get("obdSerialPortList"));
  assert.equal(dom.startObdLiveBtn, elements.get("startObdLiveBtn"));
  assert.equal(dom.stopObdLiveBtn, elements.get("stopObdLiveBtn"));
  assert.equal(dom.obdAnalysisStatus, elements.get("obdAnalysisStatus"));
  assert.equal(dom.scanComPortsBtn, elements.get("scanComPortsBtn"));
  assert.equal(dom.comPortList, elements.get("comPortList"));
  assert.equal(dom.comSelectedStatus, elements.get("comSelectedStatus"));
  assert.equal(dom.startCanLiveBtn, elements.get("startCanLiveBtn"));
  assert.equal(dom.stopCanLiveBtn, elements.get("stopCanLiveBtn"));
  assert.equal(dom.liveCanStatus, elements.get("liveCanStatus"));
  assert.equal(dom.liveObdStatus, elements.get("liveObdStatus"));
  assert.equal(dom.liveLogList, elements.get("liveLogList"));
  assert.equal(dom.obdAdapterIdentity, elements.get("obdAdapterIdentity"));
  assert.equal(dom.obdProtocol, elements.get("obdProtocol"));
  assert.equal(dom.obdSupportedPids, elements.get("obdSupportedPids"));
  assert.equal(dom.obdDtcList, elements.get("obdDtcList"));
  assert.equal(dom.obdPidCommand, elements.get("obdPidCommand"));
  assert.equal(dom.saveObdPidBtn, elements.get("saveObdPidBtn"));
  assert.equal(dom.obdValueList, elements.get("obdValueList"));
  assert.equal(dom.canvasPanel, elements.get("canvasPanel"));
  assert.equal(dom.toggleCanvasBtn, elements.get("toggleCanvasBtn"));
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
    scanObdComPorts: () => calls.push(["scanObdComPorts"]),
    scanComPorts: () => calls.push(["scanComPorts"]),
    selectObdSerialPort: (device) => calls.push(["selectObdSerialPort", device]),
    selectCanPort: (device) => calls.push(["selectCanPort", device]),
    selectComPort: (device) => calls.push(["selectComPort", device]),
    inspectObdBle: () => calls.push(["inspectObdBle"]),
    startObdLive: () => calls.push(["startObdLive"]),
    stopObdLive: () => calls.push(["stopObdLive"]),
    startCanLive: () => calls.push(["startCanLive"]),
    stopCanLive: () => calls.push(["stopCanLive"]),
    copyLiveSample: () => calls.push(["copyLiveSample"]),
    saveCanSignal: () => calls.push(["saveCanSignal"]),
    addObdProbeCommand: () => calls.push(["addObdProbeCommand"]),
    saveObdPidDefinition: () => calls.push(["saveObdPidDefinition"]),
    editObdPidDefinition: (row) => calls.push(["editObdPidDefinition", row]),
    assignObdBinding: (binding, label) => calls.push(["assignObdBinding", binding, label]),
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
  dom.scanObdComPortsBtn.listeners.click();
  dom.obdSerialPortList.listeners.click({ target: { closest: () => ({ dataset: { obdSerialPort: "COM5" } }) } });
  dom.obdDeviceList.listeners.click({ target: { closest: () => ({ dataset: { obdAddress: "AA:BB" } }) } });
  dom.scanComPortsBtn.listeners.click();
  dom.comPortList.listeners.click({ target: { closest: () => ({ dataset: { comPort: "COM7" } }) } });
  dom.inspectObdBtn.listeners.click();
  dom.startObdLiveBtn.listeners.click();
  dom.stopObdLiveBtn.listeners.click();
  dom.startCanLiveBtn.listeners.click();
  dom.stopCanLiveBtn.listeners.click();
  dom.copyLiveSampleBtn.listeners.click();
  dom.saveCanSignalBtn.listeners.click();
  dom.addObdProbeBtn.listeners.click();
  dom.saveObdPidBtn.listeners.click();
  dom.obdValueList.listeners.click({
    target: {
      closest: (selector) =>
        selector === "[data-obd-define-pid]"
          ? { dataset: { obdDefinePid: "0149", obdLabel: "Mode 01 PID 49", obdUnit: "raw", obdPath: "", obdRawBytes: "80" }, disabled: false }
          : null,
    },
  });
  dom.obdValueList.listeners.click({ target: { closest: () => ({ dataset: { obdBinding: "vehicle.rpm", obdLabel: "Engine RPM" }, disabled: false }) } });
  dom.frontBtn.listeners.click();
  dom.backBtn.listeners.click();
  dom.toggleCanvasBtn.listeners.click();
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
    ["scanObdComPorts"],
    ["selectObdSerialPort", "COM5"],
    ["selectObdDevice", "AA:BB"],
    ["scanComPorts"],
    ["selectCanPort", "COM7"],
    ["inspectObdBle"],
    ["startObdLive"],
    ["stopObdLive"],
    ["startCanLive"],
    ["stopCanLive"],
    ["copyLiveSample"],
    ["saveCanSignal"],
    ["addObdProbeCommand"],
    ["saveObdPidDefinition"],
    ["editObdPidDefinition", { command: "0149", label: "Mode 01 PID 49", unit: "raw", path: "", rawBytes: "80" }],
    ["assignObdBinding", "vehicle.rpm", "Engine RPM"],
    ["bumpZ", 1],
    ["bumpZ", -1],
    ["onPointerDown"],
    ["renderOverlay"],
    ["onKeyDown"],
  ]);
  assert.equal(state.paletteQuery, "speed");
  assert.equal(dom.canvasPanel.className.includes("is-collapsed"), true);
  assert.equal(dom.toggleCanvasBtn.textContent, "Canvas 펼치기");
  assert.equal(dom.toggleCanvasBtn.attributes["aria-expanded"], "false");
  assert.equal(windowRef.listeners.pointermove, handlers.onPointerMove);
  assert.equal(windowRef.listeners.pointerup, handlers.onPointerUp);
});
