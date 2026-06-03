const test = require("node:test");
const assert = require("node:assert/strict");

const History = require("../src/renderer/editorHistory.js");

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function editorState() {
  return {
    layout: { elements: [{ id: "speed", x: 10 }] },
    currentScreen: "standalone",
    selectedId: "speed",
    history: {
      undo: [],
      redo: [],
      applying: false,
    },
  };
}

test("snapshotState captures editable layout screen and selection as a clone", () => {
  const state = editorState();

  const snapshot = History.snapshotState(state, clone);
  state.layout.elements[0].x = 99;

  assert.equal(snapshot.layout.elements[0].x, 10);
  assert.equal(snapshot.currentScreen, "standalone");
  assert.equal(snapshot.selectedId, "speed");
});

test("recordHistory skips missing layouts and applying history states", () => {
  const state = editorState();
  state.layout = null;

  assert.equal(History.recordHistory(state, clone), false);
  assert.equal(state.history.undo.length, 0);

  state.layout = { elements: [] };
  state.history.applying = true;

  assert.equal(History.recordHistory(state, clone), false);
  assert.equal(state.history.undo.length, 0);
});

test("recordHistory pushes undo snapshots caps history and clears redo", () => {
  const state = editorState();
  state.history.redo.push({ selectedId: "old" });

  for (let index = 0; index < 52; index += 1) {
    state.layout.elements[0].x = index;
    History.recordHistory(state, clone);
  }

  assert.equal(state.history.undo.length, 50);
  assert.equal(state.history.undo[0].layout.elements[0].x, 2);
  assert.deepEqual(state.history.redo, []);
});

test("undo and redo move snapshots between stacks and restore editor state", () => {
  const state = editorState();
  History.recordHistory(state, clone);
  state.layout.elements[0].x = 42;
  state.selectedId = "rpm";

  assert.equal(History.undo(state, clone), true);
  assert.equal(state.layout.elements[0].x, 10);
  assert.equal(state.selectedId, "speed");
  assert.equal(state.history.redo.length, 1);

  assert.equal(History.redo(state, clone), true);
  assert.equal(state.layout.elements[0].x, 42);
  assert.equal(state.selectedId, "rpm");
  assert.equal(state.history.undo.length, 1);
});
