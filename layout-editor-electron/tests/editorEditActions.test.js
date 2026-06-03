const test = require("node:test");
const assert = require("node:assert/strict");

const EditActions = require("../src/renderer/editorEditActions.js");

function dependencies(log = []) {
  return {
    editor: {
      addOrTogglePaletteElement(layout, item, category, palette) {
        log.push(["addOrTogglePaletteElement", item.id, category, palette.marker]);
        if (item.action === "selected") {
          return { action: "selected", element: { id: "existing" } };
        }
        layout.elements.push({ id: "speed", type: "value" });
        return { action: "updated", element: { id: "speed" } };
      },
    },
    propertyActions: {
      applyPropertyInput(state, element, key, value) {
        log.push(["applyPropertyInput", element.id, key, value, state.selectedId]);
        element[key] = value;
        return { inputValue: `normalized:${value}` };
      },
    },
    snapshotState() {
      log.push(["snapshotState"]);
      return { before: true };
    },
    pushUndoSnapshot(snapshot) {
      log.push(["pushUndoSnapshot", snapshot.before]);
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
    renderProperties() {
      log.push(["renderProperties"]);
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
    requestAnimationFrame(callback) {
      log.push(["requestAnimationFrame"]);
      callback();
    },
  };
}

test("selectPaletteVariant keeps existing palette element selected without dirtying history", () => {
  const log = [];
  const state = {
    layout: { elements: [] },
    selectedId: "",
    metadata: { palette: { marker: "palette" } },
    history: { redo: [{ redo: true }] },
  };

  const result = EditActions.selectPaletteVariant(state, { id: "needle", action: "selected" }, "Speed", dependencies(log));

  assert.equal(result.changed, false);
  assert.equal(state.selectedId, "existing");
  assert.deepEqual(state.history.redo, [{ redo: true }]);
  assert.deepEqual(log.map((entry) => entry[0]), ["snapshotState", "addOrTogglePaletteElement", "renderAll"]);
});

test("selectPaletteVariant records undo clears redo and schedules preview on updates", () => {
  const log = [];
  const state = {
    layout: { elements: [] },
    selectedId: "",
    metadata: { palette: { marker: "palette" } },
    history: { redo: [{ redo: true }] },
  };

  const result = EditActions.selectPaletteVariant(state, { id: "bar", action: "updated" }, "Speed", dependencies(log));

  assert.equal(result.changed, true);
  assert.equal(state.selectedId, "speed");
  assert.deepEqual(state.history.redo, []);
  assert.deepEqual(log.map((entry) => entry[0]), [
    "snapshotState",
    "addOrTogglePaletteElement",
    "pushUndoSnapshot",
    "markDirty",
    "renderAll",
    "schedulePreview",
  ]);
});

test("handlePropertyInput applies property input preserves scroll and refreshes editor panes", () => {
  const log = [];
  const element = { id: "speed", label: "Speed" };
  const state = { selectedId: "speed" };
  const dom = { propertyForm: { scrollTop: 42 } };
  const event = {
    currentTarget: {
      dataset: { key: "label" },
      value: "Road speed",
    },
  };

  const result = EditActions.handlePropertyInput(state, dom, event, () => element, dependencies(log));

  assert.equal(result.changed, true);
  assert.equal(element.label, "Road speed");
  assert.equal(event.currentTarget.value, "normalized:Road speed");
  assert.equal(dom.propertyForm.scrollTop, 42);
  assert.deepEqual(log.map((entry) => entry[0]), [
    "recordHistory",
    "applyPropertyInput",
    "markDirty",
    "renderProperties",
    "requestAnimationFrame",
    "renderLayers",
    "renderOverlay",
    "schedulePreview",
  ]);
});

test("handlePropertyInput ignores input when no element is selected", () => {
  const log = [];
  const result = EditActions.handlePropertyInput({}, { propertyForm: {} }, { currentTarget: {} }, () => null, dependencies(log));

  assert.equal(result.changed, false);
  assert.deepEqual(log, []);
});
