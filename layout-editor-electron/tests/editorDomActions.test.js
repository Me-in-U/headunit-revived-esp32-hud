const test = require("node:test");
const assert = require("node:assert/strict");

const DomActions = require("../src/renderer/editorDomActions.js");

function fakeClassList() {
  const classes = new Set();
  return {
    classes,
    toggle(name, active) {
      if (active) {
        classes.add(name);
      } else {
        classes.delete(name);
      }
    },
  };
}

function fakeNode(dataset = {}) {
  return {
    classList: fakeClassList(),
    dataset,
    hidden: false,
    textContent: "",
    placeholder: "",
    children: [],
    append(child) {
      this.children.push(child);
    },
    replaceChildren() {
      this.children = [];
    },
  };
}

function fakeDocument(nodesBySelector = {}) {
  return {
    documentElement: { lang: "" },
    createElement(tag) {
      return { tag, className: "", textContent: "" };
    },
    querySelectorAll(selector) {
      return nodesBySelector[selector] || [];
    },
  };
}

test("showValidationDrawer stores messages renders message nodes and opens drawer", () => {
  const state = {};
  const dom = {
    validationDrawer: { hidden: true },
    validationMessages: fakeNode(),
  };
  const documentRef = fakeDocument();

  DomActions.showValidationDrawer(state, dom, ["bad binding", "bad color"], documentRef);

  assert.deepEqual(state.validationMessages, ["bad binding", "bad color"]);
  assert.equal(dom.validationDrawer.hidden, false);
  assert.deepEqual(dom.validationMessages.children.map((node) => [node.className, node.textContent]), [
    ["validation-message", "bad binding"],
    ["validation-message", "bad color"],
  ]);
});

test("hideValidationDrawer clears messages and hides drawer when present", () => {
  const state = { validationMessages: ["old"] };
  const dom = {
    validationDrawer: { hidden: false },
    validationMessages: fakeNode(),
  };
  dom.validationMessages.children.push({ textContent: "old" });

  DomActions.hideValidationDrawer(state, dom);

  assert.deepEqual(state.validationMessages, []);
  assert.equal(dom.validationDrawer.hidden, true);
  assert.deepEqual(dom.validationMessages.children, []);
});

test("updateFilePath renders dirty marker and class", () => {
  const state = { dirty: true, path: "layout.json" };
  const dom = { filePath: fakeNode() };

  DomActions.updateFilePath(state, dom, (key) => (key === "unsaved" ? "Unsaved" : key));

  assert.equal(dom.filePath.textContent, "layout.json · Unsaved");
  assert.equal(dom.filePath.classList.classes.has("dirty"), true);
});

test("setStatus updates text and status classes", () => {
  const parent = { classList: fakeClassList() };
  const dom = { statusText: { textContent: "", parentElement: parent } };

  DomActions.setStatus(dom, "Ready", "ok");

  assert.equal(dom.statusText.textContent, "Ready");
  assert.equal(parent.classList.classes.has("ok"), true);
  assert.equal(parent.classList.classes.has("error"), false);
});

test("applyLanguage updates document lang translated text and placeholders", () => {
  const textNode = fakeNode({ i18n: "open" });
  const placeholderNode = fakeNode({ i18nPlaceholder: "search" });
  const documentRef = fakeDocument({
    "[data-i18n]": [textNode],
    "[data-i18n-placeholder]": [placeholderNode],
  });

  DomActions.applyLanguage(documentRef, "ko", (key) => `t:${key}`);

  assert.equal(documentRef.documentElement.lang, "ko");
  assert.equal(textNode.textContent, "t:open");
  assert.equal(placeholderNode.placeholder, "t:search");
});
