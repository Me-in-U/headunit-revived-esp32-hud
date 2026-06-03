const test = require("node:test");
const assert = require("node:assert/strict");

const LayerView = require("../src/renderer/editorLayerView.js");

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
  elementDataLabel(element) {
    return element.binding || "";
  },
  elementLabel(element) {
    return element.label || element.id;
  },
  elementStyleLabel(element) {
    return element.style || element.type;
  },
  escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  },
};

test("renderLayers shows empty state and zero count without elements", () => {
  const dom = {
    layerCount: fakeNode(),
    layerList: fakeNode(),
  };

  LayerView.renderLayers({ layout: { elements: [] }, selectedId: "" }, dom, {
    documentRef: fakeDocument(),
    viewModel,
    translate: (key) => (key === "noElements" ? "No elements" : key),
    onLayerSelect: () => {},
  });

  assert.equal(dom.layerCount.textContent, "0");
  assert.equal(dom.layerList.children.length, 1);
  assert.equal(dom.layerList.children[0].className, "empty-state");
  assert.equal(dom.layerList.children[0].textContent, "No elements");
});

test("renderLayers sorts by z desc marks selection and calls selection callback", () => {
  const state = {
    selectedId: "speed",
    layout: {
      elements: [
        { id: "rpm", label: "RPM", type: "value", style: "Digital", binding: "vehicle.rpm", z: 3 },
        { id: "speed", label: "Speed <fast>", type: "value", style: "Needle", binding: "vehicle.speed_kmh", z: 7 },
      ],
    },
  };
  const dom = {
    layerCount: fakeNode(),
    layerList: fakeNode(),
  };
  const selected = [];

  LayerView.renderLayers(state, dom, {
    documentRef: fakeDocument(),
    viewModel,
    translate: (key) => key,
    onLayerSelect: selected.push.bind(selected),
  });

  assert.equal(dom.layerCount.textContent, "2");
  assert.deepEqual(dom.layerList.children.map((row) => [row.type, row.className]), [
    ["button", "layer-row selected"],
    ["button", "layer-row"],
  ]);
  assert.match(dom.layerList.children[0].innerHTML, /Speed &lt;fast&gt;/);
  assert.match(dom.layerList.children[0].innerHTML, /Needle · vehicle.speed_kmh/);
  assert.match(dom.layerList.children[0].innerHTML, /z 7/);
  assert.match(dom.layerList.children[1].innerHTML, /RPM/);
  assert.match(dom.layerList.children[1].innerHTML, /z 3/);

  dom.layerList.children[1].listeners.click();

  assert.deepEqual(selected, ["rpm"]);
});
