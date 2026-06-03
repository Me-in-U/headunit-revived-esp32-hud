const assert = require("node:assert/strict");
const test = require("node:test");

const ViewHandlers = require("../src/renderer/editorAppViewHandlers.js");

test("createAppViewHandlers exposes canvas selection status language and confirmation helpers", () => {
  const calls = [];
  const state = {
    appLanguage: "ko",
    dirty: true,
    layout: { canvas: { width: 1920, height: 480 }, elements: [{ id: "speed" }] },
  };
  const stageRect = { left: 20, top: 30, width: 960, height: 240 };
  const dom = {
    previewStage: {
      getBoundingClientRect: () => stageRect,
    },
  };
  const refs = {
    documentRef: {},
    windowRef: {
      confirm: (message) => {
        calls.push(["confirm", message]);
        return false;
      },
    },
  };
  const modules = {
    domActions: {
      showValidationDrawer: (actualState, actualDom, messages, documentRef) =>
        calls.push(["showDrawer", actualState, actualDom, messages, documentRef]),
      hideValidationDrawer: (actualState, actualDom) => calls.push(["hideDrawer", actualState, actualDom]),
      updateFilePath: (actualState, actualDom, translate) => calls.push(["filePath", actualState, actualDom, translate("saved")]),
      setStatus: (actualDom, message, kind) => calls.push(["status", actualDom, message, kind]),
      applyLanguage: (documentRef, language, translate) => calls.push(["languageUi", documentRef, language, translate("open")]),
    },
    elementActions: {
      selectedElement: (actualState) => {
        calls.push(["selectedElement", actualState]);
        return actualState.layout.elements[0];
      },
      elementById: (layout, id) => {
        calls.push(["elementById", layout, id]);
        return layout.elements.find((element) => element.id === id);
      },
    },
    i18n: {
      propertyLabel: (language, key, fallback) => `label:${language}:${key}:${fallback}`,
      translate: (language, key) => `t:${language}:${key}`,
    },
    viewModel: {
      eventToCanvasPoint: (event, canvas, rect) => {
        calls.push(["eventToCanvas", event.clientX, canvas, rect]);
        return { x: 10, y: 20 };
      },
      canvasScale: (canvas, rect) => {
        calls.push(["canvasScale", canvas, rect]);
        return { sx: 0.5, sy: 0.5 };
      },
      hitTestElement: (elements, x, y) => {
        calls.push(["hitTest", elements, x, y]);
        return "speed";
      },
    },
  };

  const handlers = ViewHandlers.createAppViewHandlers({ state, dom, modules, refs });

  assert.deepEqual(handlers.eventToCanvas({ clientX: 120, clientY: 80 }), { x: 10, y: 20 });
  assert.deepEqual(handlers.canvasScale(), { sx: 0.5, sy: 0.5 });
  assert.equal(handlers.hitTest(10, 20), "speed");
  assert.equal(handlers.selectedElement().id, "speed");
  assert.equal(handlers.elementById("speed").id, "speed");
  assert.equal(handlers.confirmDiscardChanges(), false);
  handlers.showValidationDrawer(["bad"]);
  handlers.hideValidationDrawer();
  handlers.updateFilePath();
  handlers.setStatus("Ready", "ok");
  handlers.applyLanguage();

  assert.equal(handlers.translate("open"), "t:ko:open");
  assert.equal(handlers.propertyLabel("binding", "Binding"), "label:ko:binding:Binding");
  assert.equal(calls.find((call) => call[0] === "confirm")[1], "t:ko:unsaved. t:ko:discardConfirm");
});
