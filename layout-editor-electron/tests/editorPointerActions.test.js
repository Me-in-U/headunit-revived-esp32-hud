const test = require("node:test");
const assert = require("node:assert/strict");

const PointerActions = require("../src/renderer/editorPointerActions.js");

function pointerEvent(target, overrides = {}) {
  const calls = [];
  return {
    target,
    pointerId: 9,
    calls,
    preventDefault() {
      calls.push("preventDefault");
    },
    ...overrides,
  };
}

function fakeDom() {
  return {
    previewImage: { src: "data:image/png;base64,abc" },
    dragGhost: {
      hidden: true,
      style: {},
    },
    selectionOverlay: {
      captures: [],
      setPointerCapture(pointerId) {
        this.captures.push(pointerId);
      },
    },
  };
}

function dependencies(log = []) {
  const elements = {
    speed: { id: "speed", x: 10, y: 20, w: 30, h: 40 },
  };
  return {
    dragActions: {
      beginDrag(state, element, point, handle) {
        log.push(["beginDrag", element?.id || null, point, handle]);
        state.drag = element ? { elementId: element.id, historyRecorded: false } : null;
      },
      applyDragMove(_state, element, point) {
        log.push(["applyDragMove", element.id, point]);
        element.x = point.x;
        element.y = point.y;
      },
      endDrag(state) {
        log.push(["endDrag"]);
        const active = Boolean(state.drag);
        state.drag = null;
        return active;
      },
    },
    elementActions: {},
    editor: {},
    eventToCanvas() {
      return { x: 12, y: 34 };
    },
    hitTest(x, y) {
      log.push(["hitTest", x, y]);
      return elements.speed;
    },
    elementById(id) {
      return elements[id] || null;
    },
    canvasScale() {
      return { width: 200, height: 100, sx: 2, sy: 2 };
    },
    dragGhost: {
      computeDragGhostStyle(element, canvas, scale) {
        log.push(["computeDragGhostStyle", element.id, canvas, scale]);
        return { left: "10px", top: "20px" };
      },
    },
    renderAll() {
      log.push(["renderAll"]);
    },
    renderProperties() {
      log.push(["renderProperties"]);
    },
    renderOverlay() {
      log.push(["renderOverlay"]);
    },
    recordHistory() {
      log.push(["recordHistory"]);
    },
    markDirty() {
      log.push(["markDirty"]);
    },
    schedulePreview(delay) {
      log.push(["schedulePreview", delay]);
    },
  };
}

test("handlePointerDown begins drag on selected hitbox captures pointer and shows ghost", () => {
  const log = [];
  const state = { layout: { canvas: { width: 100, height: 50 } }, drag: null };
  const dom = fakeDom();
  const targetBox = { dataset: { id: "speed" } };
  const target = {
    dataset: {},
    closest(selector) {
      assert.equal(selector, ".element-hitbox");
      return targetBox;
    },
  };
  const event = pointerEvent(target);

  const result = PointerActions.handlePointerDown(state, dom, event, dependencies(log));

  assert.equal(result.started, true);
  assert.equal(state.drag.elementId, "speed");
  assert.equal(dom.selectionOverlay.captures[0], 9);
  assert.equal(dom.dragGhost.hidden, false);
  assert.equal(dom.dragGhost.style.backgroundImage, 'url("data:image/png;base64,abc")');
  assert.deepEqual(event.calls, ["preventDefault"]);
  assert.deepEqual(log.map((item) => item[0]), ["beginDrag", "renderAll", "computeDragGhostStyle"]);
});

test("handlePointerDown clears drag ghost when no element is hit", () => {
  const log = [];
  const state = { layout: {}, drag: null };
  const dom = fakeDom();
  dom.dragGhost.hidden = false;
  dom.dragGhost.style.backgroundImage = "old";
  const deps = dependencies(log);
  deps.hitTest = () => null;
  const event = pointerEvent({ dataset: {}, closest: () => null });

  const result = PointerActions.handlePointerDown(state, dom, event, deps);

  assert.equal(result.started, false);
  assert.equal(dom.dragGhost.hidden, true);
  assert.equal(dom.dragGhost.style.backgroundImage, "");
  assert.deepEqual(event.calls, []);
  assert.deepEqual(log.map((item) => item[0]), ["beginDrag", "renderAll"]);
});

test("handlePointerMove records history once applies drag and schedules preview", () => {
  const log = [];
  const state = {
    layout: { canvas: { width: 100, height: 50 } },
    drag: { elementId: "speed", historyRecorded: false },
  };
  const dom = fakeDom();
  dom.dragGhost.hidden = false;

  const result = PointerActions.handlePointerMove(state, dom, pointerEvent({}), dependencies(log));

  assert.equal(result.moved, true);
  assert.equal(state.drag.historyRecorded, true);
  assert.deepEqual(log.map((item) => item[0]), [
    "recordHistory",
    "applyDragMove",
    "renderProperties",
    "renderOverlay",
    "computeDragGhostStyle",
    "schedulePreview",
  ]);
});

test("handlePointerMove ignores missing drag or missing element", () => {
  const log = [];
  const dom = fakeDom();
  const deps = dependencies(log);
  const missingDrag = PointerActions.handlePointerMove({ drag: null }, dom, pointerEvent({}), deps);
  const missingElement = PointerActions.handlePointerMove({ drag: { elementId: "missing" } }, dom, pointerEvent({}), deps);

  assert.equal(missingDrag.moved, false);
  assert.equal(missingElement.moved, false);
  assert.deepEqual(log, []);
});

test("handlePointerUp marks dirty only when drag actually ended", () => {
  const log = [];
  const dom = fakeDom();
  const state = { drag: { elementId: "speed" } };
  const ended = PointerActions.handlePointerUp(state, dom, dependencies(log));
  const ignored = PointerActions.handlePointerUp(state, dom, dependencies(log));

  assert.equal(ended.ended, true);
  assert.equal(ignored.ended, false);
  assert.deepEqual(log.map((item) => item[0]), ["endDrag", "markDirty", "renderAll", "schedulePreview", "endDrag"]);
});
