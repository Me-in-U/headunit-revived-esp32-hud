const test = require("node:test");
const assert = require("node:assert/strict");

const DragActions = require("../src/renderer/editorDragActions.js");

function editorHelpers() {
  return {
    normalizeElementForCanvas(element, canvas) {
      element.normalizedCanvas = canvas;
      return element;
    },
  };
}

function elementActions() {
  return {
    resizeElement(element, original, dx, dy, handle) {
      element.resizeCall = { original, dx, dy, handle };
      element.x = original.x + dx;
      element.y = original.y + dy;
      return element;
    },
  };
}

test("beginDrag clears selection when no element is hit", () => {
  const state = { selectedId: "speed", drag: { elementId: "speed" } };

  const drag = DragActions.beginDrag(state, null, { x: 5, y: 6 }, "");

  assert.equal(drag, null);
  assert.equal(state.selectedId, "");
  assert.equal(state.drag, null);
});

test("beginDrag records move and resize metadata from selected element", () => {
  const state = { selectedId: "", drag: null };
  const element = { id: "speed", x: "10", y: 20, w: 30, h: 40 };

  const moveDrag = DragActions.beginDrag(state, element, { x: 1, y: 2 }, "");

  assert.deepEqual(moveDrag, {
    mode: "move",
    handle: "",
    start: { x: 1, y: 2 },
    original: { x: 10, y: 20, w: 30, h: 40 },
    elementId: "speed",
    historyRecorded: false,
  });
  assert.equal(state.selectedId, "speed");

  const resizeDrag = DragActions.beginDrag(state, element, { x: 3, y: 4 }, "se");

  assert.equal(resizeDrag.mode, "resize");
  assert.equal(resizeDrag.handle, "se");
});

test("applyDragMove moves elements with rounded pointer deltas and normalizes", () => {
  const state = {
    layout: { canvas: { width: 200, height: 100 } },
    drag: {
      mode: "move",
      handle: "",
      start: { x: 5.2, y: 10.2 },
      original: { x: 20, y: 30, w: 40, h: 50 },
      elementId: "speed",
      historyRecorded: false,
    },
  };
  const element = { id: "speed" };

  assert.equal(DragActions.applyDragMove(state, element, { x: 8.9, y: 12.6 }, editorHelpers(), elementActions()), true);
  assert.equal(element.x, 24);
  assert.equal(element.y, 32);
  assert.deepEqual(element.normalizedCanvas, { width: 200, height: 100 });
});

test("applyDragMove resizes elements through element actions", () => {
  const state = {
    layout: { canvas: { width: 200, height: 100 } },
    drag: {
      mode: "resize",
      handle: "nw",
      start: { x: 0, y: 0 },
      original: { x: 20, y: 30, w: 40, h: 50 },
      elementId: "speed",
      historyRecorded: false,
    },
  };
  const element = { id: "speed" };

  assert.equal(DragActions.applyDragMove(state, element, { x: -3.6, y: 4.2 }, editorHelpers(), elementActions()), true);
  assert.deepEqual(element.resizeCall, {
    original: { x: 20, y: 30, w: 40, h: 50 },
    dx: -4,
    dy: 4,
    handle: "nw",
  });
  assert.deepEqual(element.normalizedCanvas, { width: 200, height: 100 });
});

test("endDrag clears active drag state only when one exists", () => {
  const state = { drag: null };

  assert.equal(DragActions.endDrag(state), false);

  state.drag = { elementId: "speed" };
  assert.equal(DragActions.endDrag(state), true);
  assert.equal(state.drag, null);
});
