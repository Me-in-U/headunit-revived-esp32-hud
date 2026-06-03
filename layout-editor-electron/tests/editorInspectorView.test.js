const test = require("node:test");
const assert = require("node:assert/strict");

const InspectorView = require("../src/renderer/editorInspectorView.js");

function fakeNode(tag = "div") {
  return {
    tag,
    id: "",
    type: "",
    htmlFor: "",
    open: undefined,
    value: "",
    className: "",
    textContent: "",
    dataset: {},
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
  bindingOptions({ current }) {
    return ["vehicle.rpm", current, "vehicle.speed_kmh"].filter(Boolean).sort();
  },
  elementSummary(element) {
    return `${element.label} · ${element.value_style}`;
  },
  optionLabel(value) {
    return String(value).toUpperCase();
  },
  propertyValue(element, key, type) {
    if (type === "color") {
      return element[key] || "#ffffff";
    }
    return element[key] ?? "";
  },
};

const editor = {
  inspectorSectionsForElement() {
    return [
      {
        id: "data",
        label: "Data",
        fields: [{ key: "binding", label: "Binding", type: "binding-select" }],
      },
      {
        id: "presentation",
        label: "Presentation",
        fields: [
          { key: "value_style", label: "Value style", type: "select", options: ["digital", "needle"] },
          { key: "color", label: "Color", type: "color" },
        ],
      },
      {
        id: "advanced",
        label: "Advanced",
        collapsed: true,
        fields: [{ key: "id", label: "ID", type: "text" }],
      },
    ];
  },
};

test("renderProperties shows empty state when no element is selected", () => {
  const dom = {
    selectedLabel: fakeNode(),
    propertyForm: fakeNode(),
  };

  InspectorView.renderProperties({ layout: {}, metadata: {} }, dom, {
    documentRef: fakeDocument(),
    editor,
    viewModel,
    selectedElement: () => null,
    translate: (key) => (key === "noSelection" ? "No selection" : "Select an element"),
    sectionLabel: (section) => section.label,
    propertyLabel: (key, fallback) => fallback,
    onPropertyInput: () => {},
  });

  assert.equal(dom.selectedLabel.textContent, "No selection");
  assert.equal(dom.propertyForm.children.length, 1);
  assert.equal(dom.propertyForm.children[0].className, "empty-state");
  assert.equal(dom.propertyForm.children[0].textContent, "Select an element");
});

test("renderProperties renders inspector sections fields options and input handlers", () => {
  const element = {
    id: "speed",
    label: "Speed",
    binding: "vehicle.speed_kmh",
    value_style: "needle",
    color: "#24d36b",
  };
  const state = {
    metadata: { palette: {} },
    layout: { dummy_data: { vehicle: { rpm: 1000, speed_kmh: 42 } } },
  };
  const dom = {
    selectedLabel: fakeNode(),
    propertyForm: fakeNode(),
  };
  const events = [];

  InspectorView.renderProperties(state, dom, {
    documentRef: fakeDocument(),
    editor,
    viewModel,
    selectedElement: () => element,
    translate: (key) => key,
    sectionLabel: (section) => `section:${section.id}`,
    propertyLabel: (key, fallback) => `label:${fallback}`,
    onPropertyInput: (event) => events.push(event.currentTarget?.dataset?.key || "keydown"),
  });

  assert.equal(dom.selectedLabel.textContent, "Speed · needle");
  assert.deepEqual(dom.propertyForm.children.map((node) => [node.tag, node.className]), [
    ["section", "property-section data"],
    ["section", "property-section presentation"],
    ["details", "property-section advanced"],
  ]);
  assert.equal(dom.propertyForm.children[2].open, false);

  const bindingField = dom.propertyForm.children[0].children[1].children[0];
  const bindingInput = bindingField.children[1];
  assert.equal(bindingField.children[0].textContent, "label:Binding");
  assert.equal(bindingInput.tag, "select");
  assert.equal(bindingInput.dataset.key, "binding");
  assert.equal(bindingInput.dataset.inputType, "binding-select");
  assert.deepEqual(bindingInput.children.map((option) => option.value), ["vehicle.rpm", "vehicle.speed_kmh", "vehicle.speed_kmh"]);
  assert.equal(bindingInput.value, "vehicle.speed_kmh");

  const styleInput = dom.propertyForm.children[1].children[1].children[0].children[1];
  assert.equal(styleInput.tag, "select");
  assert.deepEqual(styleInput.children.map((option) => [option.value, option.textContent]), [
    ["digital", "DIGITAL"],
    ["needle", "NEEDLE"],
  ]);
  assert.equal(styleInput.value, "needle");

  const colorInput = dom.propertyForm.children[1].children[1].children[1].children[1];
  assert.equal(colorInput.tag, "input");
  assert.equal(colorInput.type, "color");
  assert.equal(colorInput.value, "#24d36b");

  styleInput.listeners.change({ currentTarget: styleInput });
  let prevented = false;
  styleInput.listeners.keydown({
    key: "Enter",
    currentTarget: styleInput,
    preventDefault() {
      prevented = true;
    },
  });

  assert.equal(prevented, true);
  assert.deepEqual(events, ["value_style", "value_style"]);
});
