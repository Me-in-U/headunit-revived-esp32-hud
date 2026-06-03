const test = require("node:test");
const assert = require("node:assert/strict");

const PaletteIdentity = require("../src/renderer/editorPaletteIdentity.js");

test("paletteKey builds stable category type identity and style keys", () => {
  assert.equal(
    PaletteIdentity.paletteKey(
      { type: "value", binding: "vehicle.speed_kmh", value_style: "needle" },
      "Primary"
    ),
    "primary:value:vehicle.speed_kmh:needle"
  );
  assert.equal(
    PaletteIdentity.paletteKey({ palette_key: "custom:key" }, "Primary"),
    "custom:key"
  );
});

test("element family and variant normalize value gear warning and nav elements", () => {
  assert.equal(PaletteIdentity.elementFamilyKey({ type: "value", binding: "vehicle.speed_kmh" }), "value:vehicle.speed_kmh");
  assert.equal(PaletteIdentity.elementFamilyKey({ type: "gear_indicator" }), "gear_indicator:vehicle.gear_range");
  assert.equal(PaletteIdentity.elementFamilyKey({ type: "warning_icon", icon: "abs" }), "warning_icon:abs");
  assert.equal(PaletteIdentity.elementFamilyKey({ type: "nav_icon", event_binding: "nav.event_type" }), "nav_icon:nav.event_type");
  assert.equal(PaletteIdentity.elementVariant({ type: "value", value_style: "bar" }), "bar");
  assert.equal(PaletteIdentity.elementVariant({ type: "gear_indicator", gear_style: "active_only" }), "active_only");
});

test("elementPaletteKeys includes legacy palette keys matching template metadata", () => {
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

  const keys = PaletteIdentity.elementPaletteKeys(element, palette);

  assert.equal(keys.has("primary:value:vehicle.speed_kmh:digital"), true);
  assert.equal(keys.has("speed:value:vehicle.speed_kmh:digital"), true);
});

test("groupPaletteFamilies strips variant suffixes from family labels", () => {
  const groups = PaletteIdentity.groupPaletteFamilies(
    [
      { type: "value", label: "Speed", binding: "vehicle.speed_kmh", value_style: "digital" },
      { type: "value", label: "Speed needle", binding: "vehicle.speed_kmh", value_style: "needle" },
      { type: "gear_indicator", label: "Gear active only", binding: "vehicle.gear_range", gear_style: "active_only" },
    ],
    "HUD"
  );

  assert.deepEqual(groups.map((group) => [group.familyKey, group.label]), [
    ["value:vehicle.speed_kmh", "Speed"],
    ["gear_indicator:vehicle.gear_range", "Gear"],
  ]);
  assert.deepEqual(groups[0].variants.map((variant) => variant.label), ["Digital", "Needle"]);
});
