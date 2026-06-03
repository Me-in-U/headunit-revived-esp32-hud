const test = require("node:test");
const assert = require("node:assert/strict");

const OverlayView = require("../src/renderer/editorOverlayView.js");

function fakeNode(tag = "div") {
  return {
    tag,
    className: "",
    textContent: "",
    dataset: {},
    style: {},
    children: [],
    append(child) {
      this.children.push(child);
    },
    replaceChildren() {
      this.children = [];
    },
  };
}

function fakeDocument() {
  return {
    createElement: fakeNode,
  };
}

test("renderOverlay clears old nodes skips hidden elements and scales hitboxes", () => {
  const dom = {
    selectionOverlay: fakeNode(),
  };
  dom.selectionOverlay.children.push(fakeNode());
  const state = {
    selectedId: "",
    layout: {
      elements: [
        { id: "speed", x: 10, y: 20, w: 30, h: 40 },
        { id: "hidden", x: 1, y: 1, w: 10, h: 10, visible: false },
      ],
    },
  };

  OverlayView.renderOverlay(state, dom, {
    documentRef: fakeDocument(),
    canvasScale: () => ({ sx: 2, sy: 3 }),
  });

  assert.equal(dom.selectionOverlay.children.length, 1);
  const box = dom.selectionOverlay.children[0];
  assert.equal(box.className, "element-hitbox");
  assert.equal(box.dataset.id, "speed");
  assert.deepEqual(box.style, {
    left: "20px",
    top: "60px",
    width: "60px",
    height: "120px",
  });
});

test("renderOverlay marks selected element and adds label plus resize handles", () => {
  const dom = {
    selectionOverlay: fakeNode(),
  };
  const state = {
    selectedId: "speed",
    layout: {
      elements: [{ id: "speed", x: 0, y: 0, w: 0, h: 0 }],
    },
  };

  OverlayView.renderOverlay(state, dom, {
    documentRef: fakeDocument(),
    canvasScale: () => ({ sx: 4, sy: 5 }),
  });

  const box = dom.selectionOverlay.children[0];
  assert.equal(box.className, "element-hitbox selected");
  assert.equal(box.style.width, "4px");
  assert.equal(box.style.height, "5px");
  assert.equal(box.children[0].className, "element-label");
  assert.equal(box.children[0].textContent, "speed");

  const handles = box.children.slice(1);
  assert.deepEqual(
    handles.map((node) => [node.className, node.dataset.handle, node.style.left, node.style.top]),
    [
      ["resize-handle nw", "nw", "-5px", "-5px"],
      ["resize-handle n", "n", "calc(50% - 4px)", "-5px"],
      ["resize-handle ne", "ne", "calc(100% - 4px)", "-5px"],
      ["resize-handle e", "e", "calc(100% - 4px)", "calc(50% - 4px)"],
      ["resize-handle se", "se", "calc(100% - 4px)", "calc(100% - 4px)"],
      ["resize-handle s", "s", "calc(50% - 4px)", "calc(100% - 4px)"],
      ["resize-handle sw", "sw", "-5px", "calc(100% - 4px)"],
      ["resize-handle w", "w", "-5px", "calc(50% - 4px)"],
    ]
  );
});

test("renderOverlay no-ops when layout is missing", () => {
  const dom = {
    selectionOverlay: fakeNode(),
  };
  dom.selectionOverlay.children.push(fakeNode("old"));

  OverlayView.renderOverlay({ layout: null }, dom, {
    documentRef: fakeDocument(),
    canvasScale: () => {
      throw new Error("canvasScale should not be called");
    },
  });

  assert.equal(dom.selectionOverlay.children.length, 1);
});
