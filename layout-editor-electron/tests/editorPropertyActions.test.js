const test = require("node:test");
const assert = require("node:assert/strict");

const PropertyActions = require("../src/renderer/editorPropertyActions.js");

function editorHelpers() {
  const calls = [];
  return {
    COLOR_KEYS: ["color", "active_color", "inactive_color", "accent", "redline_color"],
    calls,
    uniqueId(_layout, value) {
      return `${value}_unique`;
    },
    normalizeElementForCanvas(element, canvas) {
      calls.push({ id: element.id, canvas });
      return element;
    },
  };
}

function stateWith(element) {
  return {
    layout: {
      canvas: { width: 200, height: 100 },
      elements: [element],
    },
    selectedId: element.id,
  };
}

test("applyPropertyInput renames ids with uniqueId and updates selectedId", () => {
  const element = { id: "speed", type: "value" };
  const state = stateWith(element);
  const editor = editorHelpers();

  const result = PropertyActions.applyPropertyInput(state, element, "id", "speed2", editor);

  assert.equal(element.id, "speed2_unique");
  assert.equal(state.selectedId, "speed2_unique");
  assert.equal(result.inputValue, "speed2_unique");
  assert.equal(editor.calls.length, 1);
});

test("applyPropertyInput parses numeric fields and clears blank value range fields", () => {
  const element = { id: "speed", type: "value", x: 10, min_value: 0, max_value: 220 };
  const state = stateWith(element);
  const editor = editorHelpers();

  PropertyActions.applyPropertyInput(state, element, "x", "42", editor);
  PropertyActions.applyPropertyInput(state, element, "min_value", "12.5", editor);
  PropertyActions.applyPropertyInput(state, element, "max_value", "", editor);

  assert.equal(element.x, 42);
  assert.equal(element.min_value, 12.5);
  assert.equal("max_value" in element, false);
});

test("applyPropertyInput normalizes fallback bindings gears and colors", () => {
  const element = { id: "gear", type: "gear_indicator" };
  const state = stateWith(element);
  const editor = editorHelpers();

  PropertyActions.applyPropertyInput(state, element, "fallback_bindings", " a.b, , c.d ", editor);
  PropertyActions.applyPropertyInput(state, element, "gears", "p/r,n", editor);
  PropertyActions.applyPropertyInput(state, element, "color", "#ABCDEF", editor);

  assert.deepEqual(element.fallback_bindings, ["a.b", "c.d"]);
  assert.deepEqual(element.gears, ["P", "R", "N"]);
  assert.equal(element.color, "#abcdef");
});

test("applyPropertyInput applies type-specific styles and clears palette keys for bindings", () => {
  const valueElement = { id: "speed", type: "value", value_style: "digital", palette_key: "old" };
  const gearElement = { id: "gear", type: "gear_indicator", gear_style: "strip", palette_key: "old" };
  const navElement = { id: "nav", type: "nav_icon", event_binding: "nav.event", palette_key: "old" };
  const editor = editorHelpers();

  PropertyActions.applyPropertyInput(stateWith(valueElement), valueElement, "value_style", "bar", editor);
  PropertyActions.applyPropertyInput(stateWith(gearElement), gearElement, "value_style", "needle", editor);
  PropertyActions.applyPropertyInput(stateWith(gearElement), gearElement, "gear_style", "active_only", editor);
  PropertyActions.applyPropertyInput(stateWith(navElement), navElement, "event_binding", "nav.next", editor);

  assert.equal(valueElement.value_style, "bar");
  assert.equal("palette_key" in valueElement, false);
  assert.equal(gearElement.value_style, undefined);
  assert.equal(gearElement.gear_style, "active_only");
  assert.equal("palette_key" in gearElement, false);
  assert.equal(navElement.event_binding, "nav.next");
  assert.equal("palette_key" in navElement, false);
});
