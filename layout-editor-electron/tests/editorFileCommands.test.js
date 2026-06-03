const test = require("node:test");
const assert = require("node:assert/strict");

const FileCommands = require("../src/renderer/editorFileCommands.js");

function deps(overrides = {}) {
  const calls = [];
  return {
    calls,
    confirmDiscardChanges: () => true,
    confirm: (message) => {
      calls.push(["confirm", message]);
      return true;
    },
    editor: {
      ensureScreens(layout, requested) {
        layout.ensured = requested;
        return requested;
      },
    },
    fileActions: {
      applyLoadedLayout(state, response, editor) {
        calls.push(["applyLoadedLayout", response.path || ""]);
        state.layout = response.layout;
        state.path = response.path || "";
        editor.ensureScreens(state.layout, response.currentScreen || "standalone");
        return response.ok ? { applied: true } : { applied: false, errorMessage: "load failed" };
      },
      saveLayout(state, saveAs) {
        calls.push(["saveLayout", saveAs]);
        state.dirty = false;
        return Promise.resolve({ saved: true, message: saveAs ? "Saved as" : "Saved" });
      },
      validateLayout() {
        calls.push(["validateLayout"]);
        return Promise.resolve({ ok: true, nonBackgroundPixels: 12, renderSize: [1920, 480] });
      },
      exportSnapshot() {
        calls.push(["exportSnapshot"]);
        return Promise.resolve({ ok: true, message: "PNG exported: out.png" });
      },
      exportFieldPack() {
        calls.push(["exportFieldPack"]);
        return Promise.resolve({ ok: false, errorMessage: "zip failed" });
      },
    },
    hideDragGhost: () => calls.push(["hideDragGhost"]),
    hideValidationDrawer: () => calls.push(["hideValidationDrawer"]),
    renderAll: () => calls.push(["renderAll"]),
    renderPreview: () => {
      calls.push(["renderPreview"]);
      return Promise.resolve();
    },
    setStatus: (message, kind = "") => calls.push(["setStatus", message, kind]),
    showValidationDrawer: (messages) => calls.push(["showValidationDrawer", messages]),
    translate: (key) => key,
    pixelStatus: { textContent: "" },
    ...overrides,
  };
}

test("openLayoutCommand confirms unsaved changes then loads renders and previews", async () => {
  const state = { layout: { old: true }, path: "old.json" };
  const service = {
    openLayout() {
      return Promise.resolve({ ok: true, layout: {}, path: "new.json", currentScreen: "bridge" });
    },
  };
  const d = deps();

  const result = await FileCommands.openLayoutCommand(state, service, d);

  assert.equal(result.opened, true);
  assert.equal(state.path, "new.json");
  assert.deepEqual(d.calls, [
    ["applyLoadedLayout", "new.json"],
    ["hideDragGhost"],
    ["hideValidationDrawer"],
    ["renderAll"],
    ["renderPreview"],
  ]);
});

test("openLayoutCommand stops before service call when discard is rejected", async () => {
  let opened = false;
  const d = deps({ confirmDiscardChanges: () => false });

  const result = await FileCommands.openLayoutCommand({}, {
    openLayout() {
      opened = true;
      return Promise.resolve({ ok: true, layout: {} });
    },
  }, d);

  assert.equal(result.canceled, true);
  assert.equal(opened, false);
  assert.deepEqual(d.calls, []);
});

test("resetDefaultLayoutCommand asks for reset confirmation and reports ready", async () => {
  const state = { dirty: true };
  const d = deps();

  const result = await FileCommands.resetDefaultLayoutCommand(state, {
    loadDefault() {
      return Promise.resolve({ ok: true, layout: {}, path: "default.json" });
    },
  }, d);

  assert.equal(result.reset, true);
  assert.deepEqual(d.calls, [
    ["confirm", "unsaved. resetConfirm"],
    ["applyLoadedLayout", "default.json"],
    ["hideDragGhost"],
    ["hideValidationDrawer"],
    ["renderAll"],
    ["renderPreview"],
    ["setStatus", "resetReady", "ok"],
  ]);
});

test("saveLayoutCommand renders and reports successful saves", async () => {
  const state = { dirty: true };
  const d = deps();

  const result = await FileCommands.saveLayoutCommand(state, true, {}, d);

  assert.equal(result.saved, true);
  assert.equal(state.dirty, false);
  assert.deepEqual(d.calls, [
    ["saveLayout", true],
    ["renderAll"],
    ["setStatus", "Saved as", "ok"],
  ]);
});

test("validate and export commands update status and drawers", async () => {
  const state = {};
  const d = deps();

  await FileCommands.validateLayoutCommand(state, {}, d);
  await FileCommands.exportSnapshotCommand(state, {}, d);
  await FileCommands.exportFieldPackCommand(state, {}, d);

  assert.equal(d.pixelStatus.textContent, "1920 x 480");
  assert.deepEqual(d.calls, [
    ["validateLayout"],
    ["hideValidationDrawer"],
    ["setStatus", "Layout OK · 12 non-background pixels", "ok"],
    ["exportSnapshot"],
    ["setStatus", "PNG exported: out.png", "ok"],
    ["exportFieldPack"],
    ["setStatus", "zip failed", "error"],
  ]);
});
