const test = require("node:test");
const assert = require("node:assert/strict");

const Actions = require("../src/renderer/editorElementActions.js");

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function editorHelpers() {
  return {
    clone,
    uniqueId(_layout, base) {
      return `${base}_2`;
    },
    nextZ() {
      return 9;
    },
    normalizeElementForCanvas(element) {
      element.normalized = true;
      return element;
    },
  };
}

test("duplicateSelectedElement clones selected element offsets it and selects the copy", () => {
  const state = {
    layout: {
      canvas: { width: 200, height: 100 },
      elements: [{ id: "speed", label: "Speed", x: 10, y: 20, z: 3 }],
    },
    selectedId: "speed",
  };

  const copy = Actions.duplicateSelectedElement(state, editorHelpers());

  assert.equal(copy.id, "speed_copy_2");
  assert.equal(copy.label, "Speed copy");
  assert.equal(copy.x, 34);
  assert.equal(copy.y, 44);
  assert.equal(copy.z, 9);
  assert.equal(copy.normalized, true);
  assert.equal(state.selectedId, "speed_copy_2");
  assert.equal(state.layout.elements.length, 2);
  assert.equal(state.layout.elements[0].id, "speed");
});

test("deleteSelectedElement removes the selected element and clears selection", () => {
  const state = {
    layout: { elements: [{ id: "speed" }, { id: "rpm" }] },
    selectedId: "speed",
  };

  assert.equal(Actions.deleteSelectedElement(state), true);
  assert.deepEqual(state.layout.elements.map((element) => element.id), ["rpm"]);
  assert.equal(state.selectedId, "");
});

test("bumpSelectedZ increments z for the selected element only", () => {
  const state = {
    layout: { elements: [{ id: "speed", z: "3" }, { id: "rpm", z: 5 }] },
    selectedId: "speed",
  };

  const element = Actions.bumpSelectedZ(state, -1);

  assert.equal(element.z, 2);
  assert.equal(state.layout.elements[1].z, 5);
});

test("resizeElement applies handle deltas and preserves minimum size", () => {
  const element = { x: 10, y: 10, w: 50, h: 40 };

  Actions.resizeElement(element, { x: 10, y: 10, w: 50, h: 40 }, 12, -5, "ne");
  assert.deepEqual(element, { x: 10, y: 5, w: 62, h: 45 });

  Actions.resizeElement(element, { x: 10, y: 10, w: 50, h: 40 }, 80, 90, "nw");
  assert.deepEqual(element, { x: 10, y: 5, w: 8, h: 8 });
});
