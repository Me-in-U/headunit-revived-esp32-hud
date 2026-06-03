const test = require("node:test");
const assert = require("node:assert/strict");

const PaletteGroups = require("../src/renderer/editorPaletteGroups.js");

test("palette group helpers strip variant suffixes and collect variants per family", () => {
  const groups = PaletteGroups.groupPaletteFamilies(
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
  assert.deepEqual(groups[0].variants.map((variant) => variant.paletteKey), [
    "hud:value:vehicle.speed_kmh:digital",
    "hud:value:vehicle.speed_kmh:needle",
  ]);
});
