const test = require("node:test");
const assert = require("node:assert/strict");

const ContextActions = require("../src/renderer/editorContextActions.js");

function editorHelpers() {
  const calls = [];
  return {
    calls,
    clone(value) {
      return JSON.parse(JSON.stringify(value));
    },
    importOtherScreen(layout, currentScreen) {
      calls.push(["importOtherScreen", currentScreen]);
      layout.elements = [{ id: `${currentScreen}_imported` }];
    },
    switchScreen(layout, fromScreen, toScreen) {
      calls.push(["switchScreen", fromScreen, toScreen]);
      layout.elements = [{ id: `${toScreen}_marker` }];
      return toScreen === "missing" ? "standalone" : toScreen;
    },
  };
}

test("applyVehicleSelection stores selected vehicle and upserts a cloned sorted profile", () => {
  const state = {
    vehicleProfiles: {
      beta: { id: "beta", label: "Beta", inputs: { can: true } },
    },
    layout: {
      selected_vehicle: "alpha",
      vehicles: [
        { id: "zeta", label: "Zeta" },
        { id: "beta", label: "Old Beta" },
      ],
    },
  };
  const editor = editorHelpers();

  const result = ContextActions.applyVehicleSelection(state, "beta", editor);

  assert.equal(result.changed, true);
  assert.equal(state.layout.selected_vehicle, "beta");
  assert.deepEqual(state.layout.vehicles.map((vehicle) => vehicle.id), ["beta", "zeta"]);
  assert.deepEqual(state.layout.vehicles[0], { id: "beta", label: "Beta", inputs: { can: true } });
  assert.notEqual(state.layout.vehicles[0], state.vehicleProfiles.beta);

  state.vehicleProfiles.beta.inputs.can = false;
  assert.equal(state.layout.vehicles[0].inputs.can, true);
});

test("applyVehicleSelection preserves vehicles when selected profile is missing", () => {
  const existingVehicles = [{ id: "alpha" }];
  const state = {
    vehicleProfiles: {},
    layout: {
      selected_vehicle: "alpha",
      vehicles: existingVehicles,
    },
  };

  ContextActions.applyVehicleSelection(state, "missing", editorHelpers());

  assert.equal(state.layout.selected_vehicle, "missing");
  assert.equal(state.layout.vehicles, existingVehicles);
});

test("applyScreenSelection delegates screen switch and clears selection", () => {
  const state = {
    currentScreen: "standalone",
    selectedId: "speed",
    layout: { elements: [{ id: "speed" }] },
  };
  const editor = editorHelpers();

  const result = ContextActions.applyScreenSelection(state, "bridge", editor);

  assert.equal(result.changed, true);
  assert.equal(state.currentScreen, "bridge");
  assert.equal(state.selectedId, "");
  assert.deepEqual(state.layout.elements, [{ id: "bridge_marker" }]);
  assert.deepEqual(editor.calls, [["switchScreen", "standalone", "bridge"]]);
});

test("importOtherScreen delegates import and clears selection", () => {
  const state = {
    currentScreen: "bridge",
    selectedId: "nav",
    layout: { elements: [{ id: "nav" }] },
  };
  const editor = editorHelpers();

  const result = ContextActions.importOtherScreen(state, editor);

  assert.equal(result.changed, true);
  assert.equal(state.selectedId, "");
  assert.deepEqual(state.layout.elements, [{ id: "bridge_imported" }]);
  assert.deepEqual(editor.calls, [["importOtherScreen", "bridge"]]);
});

test("applyLanguageSelection normalizes language and persists it", () => {
  const state = { appLanguage: "ko" };
  const stored = [];
  const i18n = {
    APP_LANGUAGE_KEY: "language-key",
    normalizeLanguage(value) {
      return value === "en" ? "en" : "ko";
    },
  };
  const storage = {
    setItem(key, value) {
      stored.push([key, value]);
    },
  };

  const result = ContextActions.applyLanguageSelection(state, "en", i18n, storage);

  assert.equal(result.changed, true);
  assert.equal(state.appLanguage, "en");
  assert.deepEqual(stored, [["language-key", "en"]]);
});
