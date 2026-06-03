const test = require("node:test");
const assert = require("node:assert/strict");

const HistoryCommands = require("../src/renderer/editorHistoryCommands.js");

function deps(overrides = {}) {
  const calls = [];
  return {
    calls,
    clone: (value) => JSON.parse(JSON.stringify(value)),
    editor: {
      clone: (value) => JSON.parse(JSON.stringify(value)),
      syncCurrentScreen(layout, screen) {
        calls.push(["syncCurrentScreen", screen]);
        layout.synced = screen;
      },
    },
    history: {
      snapshotState(state, clone) {
        calls.push(["snapshotState", Boolean(clone)]);
        return { layout: clone(state.layout), selectedId: state.selectedId };
      },
      recordHistory(state, clone) {
        calls.push(["recordHistory", Boolean(clone)]);
        return Boolean(state.recordable);
      },
      pushUndoSnapshot(history, snapshot) {
        calls.push(["pushUndoSnapshot", snapshot.id]);
        history.undo.push(snapshot);
      },
      undo(state, clone) {
        calls.push(["undo", Boolean(clone)]);
        return Boolean(state.canUndo);
      },
      redo(state, clone) {
        calls.push(["redo", Boolean(clone)]);
        return Boolean(state.canRedo);
      },
    },
    renderAll: () => calls.push(["renderAll"]),
    renderTopControls: () => calls.push(["renderTopControls"]),
    schedulePreview: (delay) => calls.push(["schedulePreview", delay]),
    updateFilePath: () => calls.push(["updateFilePath"]),
    ...overrides,
  };
}

test("markDirtyCommand syncs current screen and refreshes top chrome", () => {
  const state = { dirty: false, currentScreen: "bridge", layout: {} };
  const d = deps();

  HistoryCommands.markDirtyCommand(state, d);

  assert.equal(state.dirty, true);
  assert.equal(state.layout.synced, "bridge");
  assert.deepEqual(d.calls, [
    ["syncCurrentScreen", "bridge"],
    ["updateFilePath"],
    ["renderTopControls"],
  ]);
});

test("snapshot and pushUndoSnapshot delegate to history helpers", () => {
  const state = { layout: { id: "layout" }, selectedId: "speed", history: { undo: [] } };
  const d = deps();

  const snapshot = HistoryCommands.snapshotStateCommand(state, d);
  HistoryCommands.pushUndoSnapshotCommand(state, { id: "manual" }, d);

  assert.deepEqual(snapshot, { layout: { id: "layout" }, selectedId: "speed" });
  assert.deepEqual(state.history.undo, [{ id: "manual" }]);
  assert.deepEqual(d.calls, [
    ["snapshotState", true],
    ["pushUndoSnapshot", "manual"],
  ]);
});

test("recordHistoryCommand refreshes top controls only when a snapshot was recorded", () => {
  const d = deps();

  const skipped = HistoryCommands.recordHistoryCommand({ recordable: false }, d);
  const recorded = HistoryCommands.recordHistoryCommand({ recordable: true }, d);

  assert.equal(skipped, false);
  assert.equal(recorded, true);
  assert.deepEqual(d.calls, [
    ["recordHistory", true],
    ["recordHistory", true],
    ["renderTopControls"],
  ]);
});

test("undo and redo commands render and schedule preview only when history changes", () => {
  const d = deps();

  const undoSkipped = HistoryCommands.undoCommand({ canUndo: false }, d);
  const undoDone = HistoryCommands.undoCommand({ canUndo: true }, d);
  const redoSkipped = HistoryCommands.redoCommand({ canRedo: false }, d);
  const redoDone = HistoryCommands.redoCommand({ canRedo: true }, d);

  assert.equal(undoSkipped, false);
  assert.equal(undoDone, true);
  assert.equal(redoSkipped, false);
  assert.equal(redoDone, true);
  assert.deepEqual(d.calls, [
    ["undo", true],
    ["undo", true],
    ["renderAll"],
    ["schedulePreview", 30],
    ["redo", true],
    ["redo", true],
    ["renderAll"],
    ["schedulePreview", 30],
  ]);
});
