const test = require("node:test");
const assert = require("node:assert/strict");

const Factory = require("../src/renderer/editorPaletteElementFactory.js");

test("palette element factory creates type-specific elements and stable ids", () => {
  const layout = { canvas: { width: 300, height: 120 }, elements: [{ id: "gear_active" }] };

  const element = Factory.createElement(
    layout,
    {
      type: "gear_indicator",
      label: "Gear active",
      binding: "vehicle.gear_range",
      gear_style: "active_only",
      font_size: 40,
      gears: ["P", "R", "N", "D"],
    },
    "Gear"
  );

  assert.equal(element.id, "gear_active_2");
  assert.equal(element.palette_key, "gear:gear_indicator:vehicle.gear_range:active_only");
  assert.equal(element.gear_style, "active_only");
  assert.equal(Object.prototype.hasOwnProperty.call(element, "value_style"), false);
  assert.equal(element.w, 180);
  assert.equal(element.h, 110);
  assert.deepEqual(element.gears, ["P", "R", "N", "D"]);
});

test("palette element factory normalizes canvas bounds and z ordering", () => {
  const layout = {
    canvas: { width: 100, height: 50 },
    elements: [{ id: "a", z: 3 }, { id: "b", z: "8" }],
  };

  const element = Factory.createElement(
    layout,
    {
      type: "value",
      label: "Oversized",
      binding: "vehicle.speed_kmh",
      value_style: "bar",
      font_size: 4,
    },
    "Primary"
  );

  assert.equal(element.z, 9);
  assert.equal(element.w, 100);
  assert.equal(element.h, 50);
  assert.equal(element.x, 0);
  assert.equal(element.y, 0);
  assert.equal(element.font_size, 8);
});
