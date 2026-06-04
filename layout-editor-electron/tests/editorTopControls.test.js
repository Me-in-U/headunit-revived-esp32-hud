const test = require("node:test");
const assert = require("node:assert/strict");

const TopControls = require("../src/renderer/editorTopControls.js");

function fakeSelect() {
  return {
    value: "",
    children: [],
    append(child) {
      this.children.push(child);
    },
    replaceChildren() {
      this.children = [];
    },
  };
}

function fakeDocument() {
  return {
    createElement(tag) {
      return { tag, value: "", textContent: "" };
    },
  };
}

test("renderTopControls updates canvas metadata controls and vehicle options", () => {
  const state = {
    layout: {
      canvas: { width: 1280, height: 400, background: "#123456" },
      elements: [{ id: "speed" }, { id: "rpm" }],
      selected_vehicle: "avante",
    },
    currentScreen: "bridge",
    appLanguage: "ko",
    paletteQuery: "speed",
    simulationEnabled: true,
    history: { undo: [{}], redo: [] },
    vehicleProfiles: {
      avante: { label: "Avante HD" },
      testcar: { label: "Test Car" },
    },
  };
  const dom = {
    canvasMeta: { textContent: "" },
    screenSelect: { value: "" },
    languageSelect: { value: "" },
    backgroundColor: { value: "" },
    simulationToggle: { checked: false },
    undoBtn: { disabled: false },
    redoBtn: { disabled: false },
    paletteSearch: { value: "" },
    vehicleSelect: fakeSelect(),
  };

  TopControls.renderTopControls(state, dom, {
    documentRef: fakeDocument(),
    validColor: (value) => /^#[0-9a-f]{6}$/i.test(value),
    vehicleLabel: (profiles, id) => profiles[id]?.label || id,
  });

  assert.equal(dom.canvasMeta.textContent, "1280 x 400, 2 elements");
  assert.equal(dom.screenSelect.value, "bridge");
  assert.equal(dom.languageSelect.value, "ko");
  assert.equal(dom.backgroundColor.value, "#123456");
  assert.equal(dom.simulationToggle.checked, true);
  assert.equal(dom.undoBtn.disabled, false);
  assert.equal(dom.redoBtn.disabled, true);
  assert.equal(dom.paletteSearch.value, "speed");
  assert.deepEqual(
    dom.vehicleSelect.children.map((option) => [option.value, option.textContent]),
    [
      ["avante", "Avante HD"],
      ["testcar", "Test Car"],
    ]
  );
  assert.equal(dom.vehicleSelect.value, "avante");
});

test("renderTopControls falls back to safe canvas color and preserves unknown selected vehicle", () => {
  const state = {
    layout: {
      canvas: { background: "bad" },
      elements: [],
      selected_vehicle: "custom",
    },
    currentScreen: "standalone",
    appLanguage: "en",
    paletteQuery: "",
    history: { undo: [], redo: [{}] },
    vehicleProfiles: {},
  };
  const dom = {
    canvasMeta: { textContent: "" },
    screenSelect: { value: "" },
    languageSelect: { value: "" },
    backgroundColor: { value: "" },
    undoBtn: { disabled: false },
    redoBtn: { disabled: false },
    paletteSearch: { value: "old" },
    vehicleSelect: fakeSelect(),
  };

  TopControls.renderTopControls(state, dom, {
    documentRef: fakeDocument(),
    validColor: () => false,
    vehicleLabel: (profiles, id) => profiles[id]?.label || id,
  });

  assert.equal(dom.canvasMeta.textContent, "1920 x 480, 0 elements");
  assert.equal(dom.backgroundColor.value, "#05080c");
  assert.equal(dom.undoBtn.disabled, true);
  assert.equal(dom.redoBtn.disabled, false);
  assert.deepEqual(dom.vehicleSelect.children.map((option) => option.value), ["custom"]);
  assert.equal(dom.vehicleSelect.value, "custom");
});
