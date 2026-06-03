const test = require("node:test");
const assert = require("node:assert/strict");

const Keyboard = require("../src/renderer/editorKeyboardActions.js");

function keyEvent(key, options = {}) {
  return {
    key,
    ctrlKey: false,
    metaKey: false,
    shiftKey: false,
    target: { tagName: "div" },
    ...options,
  };
}

function editorHelpers() {
  const calls = [];
  return {
    calls,
    normalizeElementForCanvas(element, canvas) {
      calls.push({ id: element.id, canvas });
      return element;
    },
  };
}

test("keyboardCommand ignores shortcuts while editing text controls", () => {
  const state = { selectedId: "speed" };

  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("z", { ctrlKey: true, target: { tagName: "input" } }), state), {
    type: "none",
  });
  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("Delete", { target: { tagName: "textarea" } }), state), {
    type: "none",
  });
});

test("keyboardCommand maps undo redo duplicate and delete shortcuts", () => {
  const state = { selectedId: "speed" };

  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("z", { ctrlKey: true }), state), { type: "undo" });
  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("z", { metaKey: true, shiftKey: true }), state), { type: "redo" });
  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("y", { ctrlKey: true }), state), { type: "redo" });
  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("d", { ctrlKey: true }), state), { type: "duplicate" });
  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("Backspace"), state), { type: "delete" });
});

test("keyboardCommand only returns duplicate delete and move commands when selected", () => {
  const state = { selectedId: "" };

  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("d", { ctrlKey: true }), state), { type: "none" });
  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("Delete"), state), { type: "none" });
  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("ArrowRight"), state), { type: "none" });
});

test("keyboardCommand maps arrow keys to move commands with shift step", () => {
  const state = { selectedId: "speed" };

  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("ArrowLeft"), state), { type: "move", dx: -1, dy: 0 });
  assert.deepEqual(Keyboard.keyboardCommand(keyEvent("ArrowDown", { shiftKey: true }), state), { type: "move", dx: 0, dy: 10 });
});

test("moveSelectedElement applies movement and normalizes against layout canvas", () => {
  const state = { layout: { canvas: { width: 200, height: 100 } } };
  const element = { id: "speed", x: "10", y: 20 };
  const editor = editorHelpers();

  assert.equal(Keyboard.moveSelectedElement(state, element, { type: "move", dx: -10, dy: 1 }, editor), true);

  assert.equal(element.x, 0);
  assert.equal(element.y, 21);
  assert.deepEqual(editor.calls, [{ id: "speed", canvas: { width: 200, height: 100 } }]);
});
