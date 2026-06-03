const test = require("node:test");
const assert = require("node:assert/strict");

const RenderCoordinator = require("../src/renderer/editorRenderCoordinator.js");

function deps() {
  const calls = [];
  return {
    calls,
    canvasScale: () => ({ sx: 1, sy: 1 }),
    documentRef: {},
    editor: {},
    inspectorView: {
      renderProperties(state, dom, options) {
        calls.push(["renderProperties", options.sectionLabel({ id: "basic" }), options.propertyLabel("x", "X")]);
      },
    },
    i18n: {
      sectionLabel(language, section) {
        return `${language}:${section.id}`;
      },
    },
    layerView: {
      renderLayers(state, dom, options) {
        calls.push(["renderLayers"]);
        dom.layerSelect = options.onLayerSelect;
      },
    },
    overlayView: {
      renderOverlay(state, dom, options) {
        calls.push(["renderOverlay", options.canvasScale().sx]);
      },
    },
    paletteView: {
      renderPalette(state, dom, options) {
        calls.push(["renderPalette", state.activeCategory]);
        dom.categorySelect = options.onCategorySelect;
        dom.variantSelect = options.onVariantSelect;
      },
    },
    propertyLabel: (key, fallback) => `${key}:${fallback}`,
    selectedElement: () => ({ id: "speed" }),
    selectPaletteVariant: (item, category) => calls.push(["selectPaletteVariant", item.id, category]),
    topControls: {
      renderTopControls(state, dom, options) {
        calls.push(["renderTopControls", options.vehicleLabel({ id: "avante" })]);
      },
    },
    translate: (key) => key,
    updateFilePath: () => calls.push(["updateFilePath"]),
    viewModel: {
      validColor: (value) => value || "#000000",
      vehicleLabel: (vehicle) => vehicle.id,
    },
  };
}

test("renderAll skips missing layouts", () => {
  const d = deps();

  const rendered = RenderCoordinator.renderAll({ layout: null }, {}, d);

  assert.equal(rendered, false);
  assert.deepEqual(d.calls, []);
});

test("renderAll renders panels in editor order and updates file path", () => {
  const state = { layout: { elements: [] }, activeCategory: "Speed", appLanguage: "ko" };
  const d = deps();

  const rendered = RenderCoordinator.renderAll(state, {}, d);

  assert.equal(rendered, true);
  assert.deepEqual(d.calls, [
    ["renderTopControls", "avante"],
    ["renderPalette", "Speed"],
    ["renderProperties", "ko:basic", "x:X"],
    ["renderLayers"],
    ["renderOverlay", 1],
    ["updateFilePath"],
  ]);
});

test("renderPalette callback updates active category and re-renders palette only", () => {
  const state = { layout: { elements: [] }, activeCategory: "Speed", appLanguage: "ko" };
  const dom = {};
  const d = deps();

  RenderCoordinator.renderPalette(state, dom, d);
  dom.categorySelect("Gear");
  dom.variantSelect({ id: "needle" }, "Speed");

  assert.equal(state.activeCategory, "Gear");
  assert.deepEqual(d.calls, [
    ["renderPalette", "Speed"],
    ["renderPalette", "Gear"],
    ["selectPaletteVariant", "needle", "Speed"],
  ]);
});

test("renderLayers callback selects a layer and re-renders all panels", () => {
  const state = { layout: { elements: [] }, activeCategory: "Speed", appLanguage: "ko", selectedId: "" };
  const dom = {};
  const d = deps();

  RenderCoordinator.renderLayers(state, dom, d);
  dom.layerSelect("rpm");

  assert.equal(state.selectedId, "rpm");
  assert.deepEqual(d.calls, [
    ["renderLayers"],
    ["renderTopControls", "avante"],
    ["renderPalette", "Speed"],
    ["renderProperties", "ko:basic", "x:X"],
    ["renderLayers"],
    ["renderOverlay", 1],
    ["updateFilePath"],
  ]);
});
