const test = require("node:test");
const assert = require("node:assert/strict");

const ViewModel = require("../src/renderer/editorViewModel.js");

test("element display labels combine label style and binding data", () => {
  const speed = {
    id: "speed_needle",
    type: "value",
    label: "Speed",
    value_style: "needle",
    binding: "vehicle.speed_kmh",
  };
  const gear = {
    id: "gear_range",
    type: "gear_indicator",
    gear_style: "active_only",
    binding: "vehicle.gear_range",
  };

  assert.equal(ViewModel.elementSummary(speed), "Speed · Needle");
  assert.equal(ViewModel.elementStyleLabel(gear), "Active Only");
  assert.equal(ViewModel.elementDataLabel(speed), "vehicle.speed_kmh");
});

test("propertyValue normalizes arrays colors and missing values", () => {
  assert.equal(ViewModel.propertyValue({ fallback_bindings: ["a.b", "c.d"] }, "fallback_bindings", "text"), "a.b, c.d");
  assert.equal(ViewModel.propertyValue({ color: "#24d36b" }, "color", "color"), "#24d36b");
  assert.equal(ViewModel.propertyValue({ color: "green" }, "color", "color"), "#ffffff");
  assert.equal(ViewModel.propertyValue({}, "label", "text"), "");
});

test("fieldApplies hides type-specific controls from unrelated elements", () => {
  assert.equal(ViewModel.fieldApplies("value_style", { type: "value" }), true);
  assert.equal(ViewModel.fieldApplies("value_style", { type: "gear_indicator" }), false);
  assert.equal(ViewModel.fieldApplies("gear_style", { type: "gear_indicator" }), true);
  assert.equal(ViewModel.fieldApplies("gear_style", { type: "value" }), false);
  assert.equal(ViewModel.fieldApplies("event_binding", { type: "nav_icon" }), true);
  assert.equal(ViewModel.fieldApplies("event_binding", { type: "warning_icon" }), false);
});

test("bindingOptions collects palette dummy and current binding paths", () => {
  const palette = {
    Speed: [
      {
        binding: "vehicle.speed_kmh",
        fallback_bindings: ["vehicle.speed_kmh_backup"],
      },
    ],
    Navigation: [{ event_binding: "nav.event", side_binding: "nav.side" }],
  };
  const dummyData = {
    vehicle: { rpm: 1850 },
    warnings: { abs: false },
  };

  assert.deepEqual(ViewModel.bindingOptions({ palette, dummyData, current: "vehicle.custom" }), [
    "nav.event",
    "nav.side",
    "vehicle.custom",
    "vehicle.rpm",
    "vehicle.speed_kmh",
    "vehicle.speed_kmh_backup",
    "warnings.abs",
  ]);
});

test("hitTestElement chooses the top visible element containing a point", () => {
  const elements = [
    { id: "low", x: 0, y: 0, w: 100, h: 100, z: 1 },
    { id: "hidden", x: 0, y: 0, w: 100, h: 100, z: 99, visible: false },
    { id: "top", x: 20, y: 20, w: 40, h: 40, z: 2 },
  ];

  assert.equal(ViewModel.hitTestElement(elements, 30, 30).id, "top");
  assert.equal(ViewModel.hitTestElement(elements, 10, 10).id, "low");
  assert.equal(ViewModel.hitTestElement(elements, 120, 120), undefined);
});

test("canvas helpers map pointer coordinates and stage scale", () => {
  const canvas = { width: 200, height: 100 };
  const stageRect = { left: 10, top: 20, width: 400, height: 200 };

  assert.deepEqual(ViewModel.eventToCanvasPoint({ clientX: 210, clientY: 120 }, canvas, stageRect), { x: 100, y: 50 });
  assert.deepEqual(ViewModel.canvasScale(canvas, stageRect), { sx: 2, sy: 2, width: 400, height: 200 });
});
