const test = require("node:test");
const assert = require("node:assert/strict");

const ContextCommands = require("../src/renderer/editorContextCommands.js");

function deps() {
  const calls = [];
  return {
    calls,
    applyLanguage: () => calls.push(["applyLanguage"]),
    contextActions: {
      applyLanguageSelection(state, language, i18n, storage) {
        calls.push(["applyLanguageSelection", language, Boolean(i18n), Boolean(storage)]);
        state.appLanguage = language;
      },
      applyScreenSelection(state, screen, editor) {
        calls.push(["applyScreenSelection", screen, Boolean(editor)]);
        state.currentScreen = screen;
      },
      applyVehicleSelection(state, vehicle, editor) {
        calls.push(["applyVehicleSelection", vehicle, Boolean(editor)]);
        state.selectedVehicle = vehicle;
      },
      importOtherScreen(state, editor) {
        calls.push(["importOtherScreen", Boolean(editor)]);
        state.imported = true;
      },
    },
    editor: {},
    i18n: {},
    localStorageRef: {},
    markDirty: () => calls.push(["markDirty"]),
    recordHistory: () => calls.push(["recordHistory"]),
    renderAll: () => calls.push(["renderAll"]),
    schedulePreview: (delay) => calls.push(["schedulePreview", delay]),
  };
}

test("applyVehicleCommand records history applies selection and marks dirty", () => {
  const state = {};
  const d = deps();

  ContextCommands.applyVehicleCommand(state, "avante", d);

  assert.equal(state.selectedVehicle, "avante");
  assert.deepEqual(d.calls, [
    ["recordHistory"],
    ["applyVehicleSelection", "avante", true],
    ["markDirty"],
  ]);
});

test("applyScreenCommand switches screen then renders and schedules preview", () => {
  const state = {};
  const d = deps();

  ContextCommands.applyScreenCommand(state, "bridge", d);

  assert.equal(state.currentScreen, "bridge");
  assert.deepEqual(d.calls, [
    ["applyScreenSelection", "bridge", true],
    ["renderAll"],
    ["schedulePreview", 40],
  ]);
});

test("importOtherScreenCommand records history imports marks dirty and refreshes preview", () => {
  const state = {};
  const d = deps();

  ContextCommands.importOtherScreenCommand(state, d);

  assert.equal(state.imported, true);
  assert.deepEqual(d.calls, [
    ["recordHistory"],
    ["importOtherScreen", true],
    ["markDirty"],
    ["renderAll"],
    ["schedulePreview", 40],
  ]);
});

test("applyLanguageCommand persists language and re-renders without dirtying layout", () => {
  const state = {};
  const d = deps();

  ContextCommands.applyLanguageCommand(state, "en", d);

  assert.equal(state.appLanguage, "en");
  assert.deepEqual(d.calls, [
    ["applyLanguageSelection", "en", true, true],
    ["applyLanguage"],
    ["renderAll"],
  ]);
});
