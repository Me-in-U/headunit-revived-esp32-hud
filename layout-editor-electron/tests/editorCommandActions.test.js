const test = require("node:test");
const assert = require("node:assert/strict");

const CommandActions = require("../src/renderer/editorCommandActions.js");

function dependencies(log = []) {
  const selected = { id: "speed", x: 10, y: 20 };
  return {
    editor: {},
    elementActions: {
      duplicateSelectedElement(state) {
        log.push(["duplicateSelectedElement"]);
        state.selectedId = "speed_copy";
        return true;
      },
      deleteSelectedElement(state) {
        log.push(["deleteSelectedElement"]);
        state.selectedId = "";
        return true;
      },
      bumpSelectedZ(_state, delta) {
        log.push(["bumpSelectedZ", delta]);
        return true;
      },
    },
    keyboardActions: {
      keyboardCommand(event) {
        return event.command;
      },
      moveSelectedElement(_state, element, command) {
        log.push(["moveSelectedElement", element.id, command.dx, command.dy]);
        return true;
      },
    },
    selectedElement() {
      return selected;
    },
    recordHistory() {
      log.push(["recordHistory"]);
    },
    markDirty() {
      log.push(["markDirty"]);
    },
    renderAll() {
      log.push(["renderAll"]);
    },
    renderLayers() {
      log.push(["renderLayers"]);
    },
    renderOverlay() {
      log.push(["renderOverlay"]);
    },
    schedulePreview(delay) {
      log.push(["schedulePreview", delay]);
    },
    setStatus(message, kind) {
      log.push(["setStatus", message, kind]);
    },
    translate(key) {
      return `t:${key}`;
    },
    undo() {
      log.push(["undo"]);
    },
    redo() {
      log.push(["redo"]);
    },
  };
}

function keyEvent(command) {
  const calls = [];
  return {
    command,
    calls,
    preventDefault() {
      calls.push("preventDefault");
    },
  };
}

test("duplicateSelected records history updates layout and reports status", () => {
  const log = [];
  const state = { selectedId: "speed" };

  const result = CommandActions.duplicateSelected(state, dependencies(log));

  assert.equal(result.changed, true);
  assert.equal(state.selectedId, "speed_copy");
  assert.deepEqual(log, [
    ["recordHistory"],
    ["duplicateSelectedElement"],
    ["markDirty"],
    ["renderAll"],
    ["schedulePreview", 40],
    ["setStatus", "t:duplicateReady", "ok"],
  ]);
});

test("deleteSelected and bumpZ only run when an element is selected", () => {
  const log = [];
  const state = { selectedId: "speed" };
  const deps = dependencies(log);

  const deleted = CommandActions.deleteSelected(state, deps);
  const ignoredDelete = CommandActions.deleteSelected(state, deps);
  state.selectedId = "speed";
  const bumped = CommandActions.bumpZ(state, -1, deps);

  assert.equal(deleted.changed, true);
  assert.equal(ignoredDelete.changed, false);
  assert.equal(bumped.changed, true);
  assert.deepEqual(log.map((entry) => entry[0]), [
    "recordHistory",
    "deleteSelectedElement",
    "markDirty",
    "renderAll",
    "schedulePreview",
    "recordHistory",
    "bumpSelectedZ",
    "markDirty",
    "renderLayers",
    "renderOverlay",
    "schedulePreview",
  ]);
});

test("handleKeyDown delegates undo redo duplicate delete and movement commands", () => {
  const log = [];
  const state = { selectedId: "speed" };
  const deps = dependencies(log);
  const events = [
    keyEvent({ type: "undo" }),
    keyEvent({ type: "redo" }),
    keyEvent({ type: "duplicate" }),
    keyEvent({ type: "delete" }),
    keyEvent({ type: "move", dx: 1, dy: 0 }),
    keyEvent({ type: "none" }),
  ];

  const results = events.map((event) => CommandActions.handleKeyDown(state, event, deps));

  assert.deepEqual(results.map((result) => result.handled), [true, true, true, true, true, false]);
  assert.deepEqual(events.map((event) => event.calls), [
    ["preventDefault"],
    ["preventDefault"],
    ["preventDefault"],
    ["preventDefault"],
    ["preventDefault"],
    [],
  ]);
  assert.deepEqual(log.map((entry) => entry[0]), [
    "undo",
    "redo",
    "recordHistory",
    "duplicateSelectedElement",
    "markDirty",
    "renderAll",
    "schedulePreview",
    "setStatus",
    "recordHistory",
    "deleteSelectedElement",
    "markDirty",
    "renderAll",
    "schedulePreview",
    "moveSelectedElement",
    "markDirty",
    "renderAll",
    "schedulePreview",
  ]);
});
