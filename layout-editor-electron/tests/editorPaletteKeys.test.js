const test = require("node:test");
const assert = require("node:assert/strict");

const PaletteKeys = require("../src/renderer/editorPaletteKeys.js");

test("palette key helpers build stable palette element and family identities", () => {
  assert.equal(
    PaletteKeys.paletteKey({ type: "value", binding: "vehicle.speed_kmh", value_style: "needle" }, "Primary"),
    "primary:value:vehicle.speed_kmh:needle"
  );
  assert.equal(PaletteKeys.paletteKey({ palette_key: "custom:key" }, "Primary"), "custom:key");
  assert.equal(PaletteKeys.elementFamilyKey({ type: "value", binding: "vehicle.speed_kmh" }), "value:vehicle.speed_kmh");
  assert.equal(PaletteKeys.elementFamilyKey({ type: "gear_indicator" }), "gear_indicator:vehicle.gear_range");
  assert.equal(PaletteKeys.elementFamilyKey({ type: "warning_icon", icon: "abs" }), "warning_icon:abs");
  assert.equal(PaletteKeys.elementFamilyKey({ type: "nav_icon", event_binding: "nav.event_type" }), "nav_icon:nav.event_type");
  assert.equal(PaletteKeys.elementVariant({ type: "value", value_style: "bar" }), "bar");
  assert.equal(PaletteKeys.elementVariant({ type: "gear_indicator", gear_style: "active_only" }), "active_only");
});

test("palette key helpers include legacy palette keys for matching metadata", () => {
  const element = {
    type: "value",
    category: "primary",
    binding: "vehicle.speed_kmh",
    value_style: "digital",
    palette_key: "primary:value:vehicle.speed_kmh:digital",
  };
  const palette = {
    Speed: [{ type: "value", binding: "vehicle.speed_kmh", value_style: "digital" }],
  };

  const keys = PaletteKeys.elementPaletteKeys(element, palette);

  assert.equal(keys.has("primary:value:vehicle.speed_kmh:digital"), true);
  assert.equal(keys.has("speed:value:vehicle.speed_kmh:digital"), true);
});
