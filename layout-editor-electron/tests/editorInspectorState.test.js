const test = require("node:test");
const assert = require("node:assert/strict");

const InspectorState = require("../src/renderer/editorInspectorState.js");

test("value inspector sections expose data presentation and advanced fields", () => {
  const sections = InspectorState.inspectorSectionsForElement({ type: "value" });
  const byId = new Map(sections.map((section) => [section.id, section]));

  assert.deepEqual(sections.map((section) => section.id), ["basic", "layout", "data", "presentation", "advanced"]);
  assert.deepEqual(byId.get("data").fields.map((field) => field.key), [
    "binding",
    "min_value",
    "max_value",
    "tick_interval",
  ]);
  assert.equal(byId.get("presentation").fields.some((field) => field.key === "value_style"), true);
  assert.equal(byId.get("presentation").fields.some((field) => field.key === "gear_style"), false);
  assert.equal(byId.get("advanced").collapsed, true);
  assert.deepEqual(byId.get("advanced").fields.map((field) => field.key), ["id", "binding", "fallback_bindings"]);
});

test("gear inspector sections hide value style controls", () => {
  const sections = InspectorState.inspectorSectionsForElement({ type: "gear_indicator" });
  const fields = sections.flatMap((section) => section.fields.map((field) => field.key));

  assert.equal(fields.includes("gear_style"), true);
  assert.equal(fields.includes("value_style"), false);
});
