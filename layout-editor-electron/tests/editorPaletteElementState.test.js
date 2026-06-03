const test = require("node:test");
const assert = require("node:assert/strict");

const PaletteElementState = require("../src/renderer/editorPaletteElementState.js");

test("createElement builds type-specific palette elements and normalizes geometry", () => {
  const layout = { canvas: { width: 300, height: 120 }, elements: [{ id: "speed" }] };

  const element = PaletteElementState.createElement(
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

  assert.equal(element.id, "gear_active");
  assert.equal(element.palette_key, "gear:gear_indicator:vehicle.gear_range:active_only");
  assert.equal(element.gear_style, "active_only");
  assert.equal(Object.prototype.hasOwnProperty.call(element, "value_style"), false);
  assert.equal(element.w, 180);
  assert.equal(element.h, 110);
});

test("addOrTogglePaletteElement updates existing families instead of adding duplicates", () => {
  const layout = {
    canvas: { width: 1920, height: 480 },
    elements: [
      {
        id: "speed",
        type: "value",
        binding: "vehicle.speed_kmh",
        value_style: "digital",
        fallback_bindings: ["vehicle.speed_kmh_backup"],
      },
    ],
  };
  const template = {
    type: "value",
    label: "Speed bar",
    binding: "vehicle.speed_kmh",
    fallback_bindings: ["vehicle.speed_kmh_backup"],
    value_style: "bar",
    suffix: " km/h",
    max_value: 220,
  };

  const result = PaletteElementState.addOrTogglePaletteElement(layout, template, "Speed", { Speed: [template] });

  assert.equal(result.action, "updated");
  assert.equal(layout.elements.length, 1);
  assert.equal(layout.elements[0].value_style, "bar");
  assert.equal(layout.elements[0].suffix, " km/h");
  assert.equal(layout.elements[0].max_value, 220);
});

test("addOrTogglePaletteElement selects exact existing palette entries", () => {
  const template = { type: "value", label: "RPM", binding: "vehicle.rpm", value_style: "digital" };
  const layout = {
    elements: [
      {
        id: "rpm",
        type: "value",
        binding: "vehicle.rpm",
        value_style: "digital",
        palette_key: "engine:value:vehicle.rpm:digital",
      },
    ],
  };

  const result = PaletteElementState.addOrTogglePaletteElement(layout, template, "Engine", { Engine: [template] });

  assert.equal(result.action, "selected");
  assert.equal(result.element.id, "rpm");
  assert.equal(layout.elements.length, 1);
});
