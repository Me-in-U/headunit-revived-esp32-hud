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
