const test = require("node:test");
const assert = require("node:assert/strict");

const Editor = require("../src/renderer/editorState.js");

test("palette matching treats split categories as the same existing element", () => {
  const palette = {
    Speed: [{ type: "value", label: "Speed", binding: "vehicle.speed_kmh", value_style: "digital" }],
  };
  const element = {
    id: "speed",
    type: "value",
    category: "primary",
    binding: "vehicle.speed_kmh",
    value_style: "digital",
    palette_key: "primary:value:vehicle.speed_kmh:digital",
  };

  const keys = Editor.elementPaletteKeys(element, palette);

  assert.equal(keys.has("speed:value:vehicle.speed_kmh:digital"), true);
});

test("selecting an existing palette item keeps it selected instead of removing it", () => {
  const palette = {
    Speed: [{ type: "value", label: "Speed", binding: "vehicle.speed_kmh", value_style: "digital" }],
  };
  const layout = {
    canvas: { width: 1920, height: 480 },
    elements: [
      {
        id: "speed",
        type: "value",
        binding: "vehicle.speed_kmh",
        value_style: "digital",
      },
    ],
  };

  const result = Editor.addOrTogglePaletteElement(layout, palette.Speed[0], "Speed", palette);

  assert.equal(result.action, "selected");
  assert.equal(layout.elements.length, 1);
  assert.equal(result.element.id, "speed");
});

test("value palette variants update one family element instead of adding duplicates", () => {
  const speedDigital = { type: "value", label: "Speed", binding: "vehicle.speed_kmh", value_style: "digital", font_size: 120 };
  const speedBar = { type: "value", label: "Speed bar", binding: "vehicle.speed_kmh", value_style: "bar", suffix: " km/h", font_size: 32 };
  const palette = { Speed: [speedDigital, speedBar] };
  const layout = { canvas: { width: 1920, height: 480 }, elements: [] };

  const added = Editor.addOrTogglePaletteElement(layout, speedDigital, "Speed", palette);
  const updated = Editor.addOrTogglePaletteElement(layout, speedBar, "Speed", palette);

  assert.equal(added.action, "added");
  assert.equal(updated.action, "updated");
  assert.equal(layout.elements.length, 1);
  assert.equal(layout.elements[0].binding, "vehicle.speed_kmh");
  assert.equal(layout.elements[0].value_style, "bar");
  assert.equal(layout.elements[0].palette_key, "speed:value:vehicle.speed_kmh:bar");
});

test("clicking an already selected palette variant keeps the element instead of deleting it", () => {
  const speedDigital = { type: "value", label: "Speed", binding: "vehicle.speed_kmh", value_style: "digital", font_size: 120 };
  const palette = { Speed: [speedDigital] };
  const layout = { canvas: { width: 1920, height: 480 }, elements: [] };

  Editor.addOrTogglePaletteElement(layout, speedDigital, "Speed", palette);
  const result = Editor.addOrTogglePaletteElement(layout, speedDigital, "Speed", palette);

  assert.equal(result.action, "selected");
  assert.equal(layout.elements.length, 1);
  assert.equal(layout.elements[0].value_style, "digital");
});

test("palette items group by element family and expose style variants", () => {
  const palette = {
    Speed: [
      { type: "value", label: "Speed", binding: "vehicle.speed_kmh", value_style: "digital" },
      { type: "value", label: "Speed bar", binding: "vehicle.speed_kmh", value_style: "bar" },
      { type: "value", label: "Fuel", binding: "vehicle.fuel_percent", value_style: "bar" },
    ],
  };

  const groups = Editor.groupPaletteFamilies(palette.Speed, "Speed");

  assert.equal(groups.length, 2);
  assert.equal(groups[0].familyKey, "value:vehicle.speed_kmh");
  assert.equal(groups[0].label, "Speed");
  assert.deepEqual(groups[0].variants.map((variant) => variant.variant), ["digital", "bar"]);
  assert.equal(groups[1].familyKey, "value:vehicle.fuel_percent");
});

test("inspector field sections put raw fields in advanced and hide irrelevant style controls", () => {
  const valueSections = Editor.inspectorSectionsForElement({ type: "value" });
  const gearSections = Editor.inspectorSectionsForElement({ type: "gear_indicator" });
  const valueFields = valueSections.flatMap((section) => section.fields.map((field) => field.key));
  const gearFields = gearSections.flatMap((section) => section.fields.map((field) => field.key));
  const advanced = valueSections.find((section) => section.id === "advanced");

  assert.equal(valueFields.includes("value_style"), true);
  assert.equal(valueFields.includes("gear_style"), false);
  assert.equal(gearFields.includes("gear_style"), true);
  assert.equal(gearFields.includes("value_style"), false);
  assert.deepEqual(advanced.fields.map((field) => field.key), ["id", "binding", "fallback_bindings"]);
});

test("gear strip and active-only palette items update the same gear family", () => {
  const layout = {
    canvas: { width: 1920, height: 480 },
    elements: [
      {
        id: "gear_range",
        type: "gear_indicator",
        binding: "vehicle.gear_range",
        gear_style: "strip",
        w: 420,
        h: 96,
      },
    ],
  };
  const template = {
    type: "gear_indicator",
    label: "Gear active",
    binding: "vehicle.gear_range",
    gear_style: "active_only",
    font_size: 36,
    active_font_size: 118,
    gears: ["P", "R", "N", "D", "3", "2", "L"],
  };

  const result = Editor.addOrTogglePaletteElement(layout, template, "Gear", { Gear: [template] });

  assert.equal(result.action, "updated");
  assert.equal(layout.elements.length, 1);
  assert.equal(layout.elements[0].gear_style, "active_only");
  assert.equal(layout.elements[0].palette_key, "gear:gear_indicator:vehicle.gear_range:active_only");
});

test("screen switching syncs the current screen before loading the target screen", () => {
  const layout = {
    elements: [{ id: "standalone_marker" }],
    screens: {
      standalone: { label: "Standalone", elements: [{ id: "old" }] },
      bridge: { label: "Bridge", elements: [{ id: "bridge_marker" }] },
    },
  };

  const selected = Editor.switchScreen(layout, "standalone", "bridge");

  assert.equal(selected, "bridge");
  assert.deepEqual(layout.screens.standalone.elements, [{ id: "standalone_marker" }]);
  assert.deepEqual(layout.elements, [{ id: "bridge_marker" }]);
});
