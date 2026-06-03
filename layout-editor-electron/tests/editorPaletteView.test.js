const test = require("node:test");
const assert = require("node:assert/strict");

const PaletteView = require("../src/renderer/editorPaletteView.js");

function fakeNode(tag = "div") {
  return {
    tag,
    type: "",
    className: "",
    textContent: "",
    innerHTML: "",
    children: [],
    listeners: {},
    append(child) {
      this.children.push(child);
    },
    replaceChildren() {
      this.children = [];
    },
    addEventListener(event, callback) {
      this.listeners[event] = callback;
    },
  };
}

function fakeDocument() {
  return {
    createElement: fakeNode,
  };
}

const viewModel = {
  escapeHtml(value) {
    return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;");
  },
};

const editor = {
  elementFamilyKey(element) {
    return `${element.type}:${element.binding}`;
  },
  elementVariant(element) {
    return element.value_style || "digital";
  },
  groupPaletteFamilies(items) {
    return [
      {
        familyKey: "value:vehicle.speed_kmh",
        label: "Speed",
        type: "value",
        binding: "vehicle.speed_kmh",
        variants: items.map((item) => ({
          variant: item.value_style,
          label: item.value_style,
          item,
        })),
      },
    ];
  },
};

test("renderPalette renders categories and active variant for existing element family", () => {
  const state = {
    metadata: {
      palette: {
        Primary: [
          { type: "value", binding: "vehicle.speed_kmh", value_style: "digital" },
          { type: "value", binding: "vehicle.speed_kmh", value_style: "needle" },
        ],
        Vehicle: [],
      },
    },
    layout: {
      elements: [{ type: "value", binding: "vehicle.speed_kmh", value_style: "needle" }],
    },
    activeCategory: "Primary",
    paletteQuery: "",
  };
  const dom = {
    categoryTabs: fakeNode(),
    paletteButtons: fakeNode(),
  };
  const selected = [];

  PaletteView.renderPalette(state, dom, {
    documentRef: fakeDocument(),
    editor,
    viewModel,
    translate: (key) => key,
    onCategorySelect: selected.push.bind(selected),
    onVariantSelect: (item, category) => selected.push(`${category}:${item.value_style}`),
  });

  assert.deepEqual(dom.categoryTabs.children.map((node) => [node.textContent, node.className]), [
    ["Primary", "category-tab active"],
    ["Vehicle", "category-tab"],
  ]);
  assert.equal(dom.paletteButtons.children.length, 1);
  const card = dom.paletteButtons.children[0];
  assert.equal(card.className, "palette-family added");
  assert.match(card.children[0].innerHTML, /Speed/);
  assert.equal(card.children[1].children[0].className, "");
  assert.equal(card.children[1].children[1].className, "active");

  dom.categoryTabs.children[1].listeners.click();
  card.children[1].children[1].listeners.click();

  assert.deepEqual(selected, ["Vehicle", "Primary:needle"]);
});

test("renderPalette falls back to first category and shows empty search results", () => {
  const state = {
    metadata: {
      palette: {
        Primary: [{ type: "value", binding: "vehicle.speed_kmh", value_style: "digital" }],
      },
    },
    layout: { elements: [] },
    activeCategory: "Missing",
    paletteQuery: "rpm",
  };
  const dom = {
    categoryTabs: fakeNode(),
    paletteButtons: fakeNode(),
  };

  PaletteView.renderPalette(state, dom, {
    documentRef: fakeDocument(),
    editor,
    viewModel,
    translate: (key) => (key === "noPaletteResults" ? "No matches" : key),
    onCategorySelect: () => {},
    onVariantSelect: () => {},
  });

  assert.equal(state.activeCategory, "Primary");
  assert.equal(dom.paletteButtons.children.length, 1);
  assert.equal(dom.paletteButtons.children[0].className, "empty-state");
  assert.equal(dom.paletteButtons.children[0].textContent, "No matches");
});

test("paletteGroupMatches searches group metadata and variant labels", () => {
  const group = {
    label: "Speed",
    type: "value",
    binding: "vehicle.speed_kmh",
    variants: [{ label: "Needle", variant: "needle", item: { label: "Speed needle" } }],
  };

  assert.equal(PaletteView.paletteGroupMatches(group, "needle"), true);
  assert.equal(PaletteView.paletteGroupMatches(group, "rpm"), false);
});
