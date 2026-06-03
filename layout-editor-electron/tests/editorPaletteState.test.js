const test = require("node:test");
const assert = require("node:assert/strict");

const PaletteState = require("../src/renderer/editorPaletteState.js");

test("palette families group value variants under one binding", () => {
  const groups = PaletteState.groupPaletteFamilies(
    [
      { type: "value", label: "Speed", binding: "vehicle.speed_kmh", value_style: "digital" },
      { type: "value", label: "Speed needle", binding: "vehicle.speed_kmh", value_style: "needle" },
      { type: "value", label: "RPM", binding: "vehicle.rpm", value_style: "sport_gauge" },
    ],
    "Primary"
  );

  assert.equal(groups.length, 2);
  assert.equal(groups[0].familyKey, "value:vehicle.speed_kmh");
  assert.equal(groups[0].label, "Speed");
  assert.deepEqual(groups[0].variants.map((variant) => variant.variant), ["digital", "needle"]);
});

test("selecting another value variant updates one family element", () => {
  const layout = { canvas: { width: 1920, height: 480 }, elements: [] };
  const speedDigital = {
    type: "value",
    label: "Speed",
    binding: "vehicle.speed_kmh",
    fallback_bindings: ["vehicle.speed_kmh_backup"],
    value_style: "digital",
    font_size: 120,
  };
  const speedNeedle = {
    type: "value",
    label: "Speed needle",
    binding: "vehicle.speed_kmh",
    fallback_bindings: ["vehicle.speed_kmh_backup"],
    value_style: "needle",
    max_value: 220,
    suffix: " km/h",
  };

  const added = PaletteState.addOrTogglePaletteElement(layout, speedDigital, "Primary", {
    Primary: [speedDigital, speedNeedle],
  });
  const updated = PaletteState.addOrTogglePaletteElement(layout, speedNeedle, "Primary", {
    Primary: [speedDigital, speedNeedle],
  });

  assert.equal(added.action, "added");
  assert.equal(updated.action, "updated");
  assert.equal(layout.elements.length, 1);
  assert.equal(layout.elements[0].value_style, "needle");
  assert.deepEqual(layout.elements[0].fallback_bindings, ["vehicle.speed_kmh_backup"]);
  assert.equal(layout.elements[0].palette_key, "primary:value:vehicle.speed_kmh:needle");
});

test("gear variants update one gear family without value style", () => {
  const layout = {
    canvas: { width: 1920, height: 480 },
    elements: [
      {
        id: "gear_range",
        type: "gear_indicator",
        binding: "vehicle.gear_range",
        gear_style: "strip",
        value_style: "digital",
      },
    ],
  };

  const result = PaletteState.addOrTogglePaletteElement(
    layout,
    {
      type: "gear_indicator",
      label: "Gear active",
      binding: "vehicle.gear_range",
      gear_style: "active_only",
      gears: ["P", "R", "N", "D"],
    },
    "Gear",
    {}
  );

  assert.equal(result.action, "updated");
  assert.equal(layout.elements.length, 1);
  assert.equal(layout.elements[0].gear_style, "active_only");
  assert.equal(Object.prototype.hasOwnProperty.call(layout.elements[0], "value_style"), false);
});

test("normalizeElementForCanvas clamps size position and font", () => {
  const element = {
    x: 2000,
    y: -20,
    w: 5000,
    h: 0,
    font_size: 4,
  };

  PaletteState.normalizeElementForCanvas(element, { width: 320, height: 120 });

  assert.deepEqual(element, {
    x: 0,
    y: 0,
    w: 320,
    h: 1,
    font_size: 8,
  });
});
