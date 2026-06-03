const test = require("node:test");
const assert = require("node:assert/strict");

const FileActions = require("../src/renderer/editorFileActions.js");

function editorHelpers() {
  const calls = [];
  return {
    calls,
    ensureScreens(layout, requested) {
      calls.push(["ensureScreens", requested]);
      layout.screensEnsured = requested;
      return requested === "missing" ? "standalone" : requested;
    },
  };
}

test("applyLoadedLayout resets editor state and ensures screen metadata", () => {
  const state = {
    layout: { old: true },
    path: "old.json",
    currentScreen: "bridge",
    vehicleProfiles: { old: true },
    selectedId: "speed",
    dirty: true,
    validationMessages: ["old issue"],
    history: {
      undo: [{ old: true }],
      redo: [{ old: true }],
    },
  };
  const layout = {};
  const editor = editorHelpers();

  const result = FileActions.applyLoadedLayout(state, {
    ok: true,
    layout,
    path: "new.json",
    currentScreen: "primary",
    vehicleProfiles: { avante: { id: "avante" } },
  }, editor);

  assert.equal(result.applied, true);
  assert.equal(state.layout, layout);
  assert.equal(state.path, "new.json");
  assert.equal(state.currentScreen, "primary");
  assert.deepEqual(state.vehicleProfiles, { avante: { id: "avante" } });
  assert.equal(state.layout.language, "ko");
  assert.deepEqual(state.layout.supported_languages, ["ko", "en"]);
  assert.equal(state.selectedId, "");
  assert.equal(state.dirty, false);
  assert.deepEqual(state.validationMessages, []);
  assert.deepEqual(state.history.undo, []);
  assert.deepEqual(state.history.redo, []);
  assert.deepEqual(editor.calls, [["ensureScreens", "primary"]]);
});

test("applyLoadedLayout reports canceled and failed loads without mutating state", () => {
  const state = {
    layout: { old: true },
    path: "old.json",
    currentScreen: "bridge",
    history: { undo: [], redo: [] },
  };

  const canceled = FileActions.applyLoadedLayout(state, { canceled: true }, editorHelpers());
  const failed = FileActions.applyLoadedLayout(state, { ok: false, errors: ["bad layout"] }, editorHelpers());

  assert.equal(canceled.canceled, true);
  assert.equal(failed.errorMessage, "bad layout");
  assert.deepEqual(state.layout, { old: true });
  assert.equal(state.path, "old.json");
  assert.equal(state.currentScreen, "bridge");
});

test("saveLayout sends current layout payload and applies successful save response", async () => {
  const calls = [];
  const state = {
    layout: { id: "layout" },
    path: "input.json",
    currentScreen: "standalone",
    dirty: true,
    history: {
      undo: [{ id: "old" }],
      redo: [{ id: "redo" }],
    },
  };
  const service = {
    saveLayoutAs(payload) {
      calls.push(["saveLayoutAs", payload]);
      return Promise.resolve({
        ok: true,
        layout: { id: "saved" },
        path: "saved.json",
        message: "Saved as",
      });
    },
  };

  const result = await FileActions.saveLayout(state, true, service);

  assert.equal(result.saved, true);
  assert.equal(result.message, "Saved as");
  assert.deepEqual(calls, [["saveLayoutAs", {
    layout: { id: "layout" },
    path: "input.json",
    currentScreen: "standalone",
  }]]);
  assert.deepEqual(state.layout, { id: "saved" });
  assert.equal(state.path, "saved.json");
  assert.equal(state.dirty, false);
  assert.deepEqual(state.history.undo, []);
  assert.deepEqual(state.history.redo, []);
});

test("saveLayout reports failed responses and preserves state", async () => {
  const state = {
    layout: { id: "layout" },
    path: "input.json",
    currentScreen: "standalone",
    dirty: true,
    history: { undo: [{ id: "old" }], redo: [] },
  };
  const service = {
    saveLayout() {
      return Promise.resolve({ ok: false, errors: ["write denied"] });
    },
  };

  const result = await FileActions.saveLayout(state, false, service);

  assert.equal(result.saved, false);
  assert.equal(result.errorMessage, "write denied");
  assert.deepEqual(state.layout, { id: "layout" });
  assert.equal(state.path, "input.json");
  assert.equal(state.dirty, true);
  assert.deepEqual(state.history.undo, [{ id: "old" }]);
});

test("validateLayout and export helpers send shared layout payload", async () => {
  const calls = [];
  const state = {
    layout: { id: "layout" },
    path: "layout.json",
    currentScreen: "standalone",
  };
  const service = {
    validateLayout(payload) {
      calls.push(["validateLayout", payload]);
      return Promise.resolve({ ok: true, renderSize: [1920, 480], nonBackgroundPixels: 123 });
    },
    exportSnapshot(payload) {
      calls.push(["exportSnapshot", payload]);
      return Promise.resolve({ ok: true, output: "out.png" });
    },
    exportFieldPack(payload) {
      calls.push(["exportFieldPack", payload]);
      return Promise.resolve({ ok: false, errors: ["zip failed"] });
    },
  };

  const validation = await FileActions.validateLayout(state, service);
  const snapshot = await FileActions.exportSnapshot(state, service);
  const fieldPack = await FileActions.exportFieldPack(state, service);

  assert.equal(validation.ok, true);
  assert.deepEqual(snapshot, { canceled: false, ok: true, message: "PNG exported: out.png" });
  assert.deepEqual(fieldPack, { canceled: false, ok: false, errorMessage: "zip failed" });
  assert.deepEqual(calls, [
    ["validateLayout", { layout: { id: "layout" }, path: "layout.json", currentScreen: "standalone" }],
    ["exportSnapshot", { layout: { id: "layout" }, path: "layout.json", currentScreen: "standalone" }],
    ["exportFieldPack", { layout: { id: "layout" }, path: "layout.json", currentScreen: "standalone" }],
  ]);
});
