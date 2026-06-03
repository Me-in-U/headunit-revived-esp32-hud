const assert = require("node:assert/strict");
const test = require("node:test");

const AppHandlers = require("../src/renderer/editorAppHandlers.js");

test("createAppHandlers routes editor commands through module dependency factories", async () => {
  const calls = [];
  const runtime = { runtime: true };
  const response = { ok: true };
  const state = {
    appLanguage: "ko",
    dirty: false,
    layout: { canvas: { width: 1920, height: 480 }, elements: [] },
  };
  const dom = {
    backgroundColor: { value: "#112233" },
    languageSelect: { value: "en" },
    screenSelect: { value: "bridge" },
    vehicleSelect: { value: "avante" },
    previewStage: {
      getBoundingClientRect: () => ({ left: 10, top: 20, width: 960, height: 240 }),
    },
  };
  const refs = {
    documentRef: {},
    navigatorRef: {},
    windowRef: {
      hudEditor: {},
    },
  };

  const modules = {
    appDeps: dependencyFactories(calls, runtime),
    backgroundActions: {
      applyBackgroundColorCommand: (actualState, color, deps) => calls.push(["backgroundColor", actualState, color, deps.name]),
      chooseBackgroundImageCommand: async (actualState, hudEditor, deps) => calls.push(["chooseBackground", actualState, hudEditor, deps.name]),
      clearBackgroundImageCommand: (actualState, deps) => calls.push(["clearBackground", actualState, deps.name]),
    },
    commandActions: {
      duplicateSelected: (actualState, deps) => calls.push(["duplicate", actualState, deps.name]),
      handleKeyDown: (actualState, event, deps) => calls.push(["keyDown", actualState, event.key, deps.name]),
      deleteSelected: (actualState, deps) => calls.push(["delete", actualState, deps.name]),
      bumpZ: (actualState, delta, deps) => calls.push(["bumpZ", actualState, delta, deps.name]),
    },
    contextCommands: {
      applyVehicleCommand: (actualState, value, deps) => calls.push(["vehicle", actualState, value, deps.name]),
      applyScreenCommand: (actualState, value, deps) => calls.push(["screen", actualState, value, deps.name]),
      importOtherScreenCommand: (actualState, deps) => calls.push(["importOther", actualState, deps.name]),
      applyLanguageCommand: (actualState, value, deps) => calls.push(["language", actualState, value, deps.name]),
    },
    editActions: {
      selectPaletteVariant: (actualState, item, category, deps) => calls.push(["paletteVariant", actualState, item.id, category, deps.name]),
      handlePropertyInput: (actualState, actualDom, event, selectedElement, deps) =>
        calls.push(["propertyInput", actualState, actualDom, event.target.name, selectedElement(), deps.name]),
    },
    elementActions: {
      selectedElement: (actualState) => actualState.layout.elements[0] || null,
    },
    fileCommands: {
      applyLoadedLayoutCommand: (actualState, actualResponse, deps) => {
        calls.push(["applyLoadedLayout", actualState, actualResponse, deps.name]);
        return "loaded";
      },
      openLayoutCommand: async (actualState, hudEditor, deps) => calls.push(["open", actualState, hudEditor, deps.name]),
      resetDefaultLayoutCommand: async (actualState, hudEditor, deps) => calls.push(["reset", actualState, hudEditor, deps.name]),
      saveLayoutCommand: async (actualState, saveAs, hudEditor, deps) => calls.push(["save", actualState, saveAs, hudEditor, deps.name]),
      validateLayoutCommand: async (actualState, hudEditor, deps) => calls.push(["validate", actualState, hudEditor, deps.name]),
      exportSnapshotCommand: async (actualState, hudEditor, deps) => calls.push(["snapshot", actualState, hudEditor, deps.name]),
      exportFieldPackCommand: async (actualState, hudEditor, deps) => calls.push(["fieldPack", actualState, hudEditor, deps.name]),
    },
    historyCommands: {
      markDirtyCommand: (actualState, deps) => calls.push(["markDirty", actualState, deps.name]),
      snapshotStateCommand: (actualState, deps) => {
        calls.push(["snapshotState", actualState, deps.name]);
        return { snapshot: true };
      },
      recordHistoryCommand: (actualState, deps) => calls.push(["recordHistory", actualState, deps.name]),
      pushUndoSnapshotCommand: (actualState, snapshot, deps) => calls.push(["pushUndo", actualState, snapshot, deps.name]),
      undoCommand: (actualState, deps) => calls.push(["undo", actualState, deps.name]),
      redoCommand: (actualState, deps) => calls.push(["redo", actualState, deps.name]),
    },
    pointerActions: {
      handlePointerDown: (actualState, actualDom, event, deps) => calls.push(["pointerDown", actualState, actualDom, event.type, deps.name]),
      handlePointerMove: (actualState, actualDom, event, deps) => calls.push(["pointerMove", actualState, actualDom, event.type, deps.name]),
      handlePointerUp: (actualState, actualDom, deps) => calls.push(["pointerUp", actualState, actualDom, deps.name]),
    },
    previewActions: {
      renderPreview: async (actualState, actualDom, deps) => calls.push(["preview", actualState, actualDom, deps.name]),
    },
    renderCoordinator: {
      renderAll: (actualState, actualDom, deps) => calls.push(["renderAll", actualState, actualDom, deps.name]),
      renderTopControls: (actualState, actualDom, deps) => calls.push(["renderTopControls", actualState, actualDom, deps.name]),
      renderPalette: (actualState, actualDom, deps) => calls.push(["renderPalette", actualState, actualDom, deps.name]),
      renderProperties: (actualState, actualDom, deps) => calls.push(["renderProperties", actualState, actualDom, deps.name]),
      renderLayers: (actualState, actualDom, deps) => calls.push(["renderLayers", actualState, actualDom, deps.name]),
      renderOverlay: (actualState, actualDom, deps) => calls.push(["renderOverlay", actualState, actualDom, deps.name]),
    },
    weatherActions: {
      fetchWeatherCommand: async (actualState, hudEditor, navigatorRef, deps) =>
        calls.push(["weather", actualState, hudEditor, navigatorRef, deps.name]),
    },
  };

  const handlers = AppHandlers.createAppHandlers({
    state,
    dom,
    modules,
    refs,
    runtimeFactory: () => runtime,
  });

  assert.equal(handlers.applyLoadedLayout(response), "loaded");
  handlers.renderAll();
  handlers.renderTopControls();
  handlers.renderPalette();
  handlers.selectPaletteVariant({ id: "speed" }, "primary");
  handlers.renderProperties();
  handlers.renderLayers();
  handlers.renderOverlay();
  await handlers.renderPreview();
  await handlers.openLayout();
  await handlers.resetDefaultLayout();
  await handlers.saveLayout(true);
  handlers.duplicateSelected();
  await handlers.validateLayout();
  await handlers.exportSnapshot();
  await handlers.exportFieldPack();
  await handlers.fetchWeather();
  handlers.onVehicleChange();
  handlers.onScreenChange();
  handlers.importOtherScreen();
  handlers.onLanguageChange();
  handlers.onBackgroundColor();
  await handlers.chooseBackgroundImage();
  handlers.clearBackgroundImage();
  handlers.onPropertyInput({ target: { name: "label" } });
  handlers.onPointerDown({ type: "pointerdown" });
  handlers.onPointerMove({ type: "pointermove" });
  handlers.onPointerUp();
  handlers.onKeyDown({ key: "Delete" });
  handlers.deleteSelected();
  handlers.bumpZ(1);
  handlers.markDirty();
  assert.deepEqual(handlers.snapshotState(), { snapshot: true });
  handlers.recordHistory();
  handlers.pushUndoSnapshot({ saved: true });
  handlers.undo();
  handlers.redo();

  assert.deepEqual(
    calls.map((call) => call[0]),
    [
      "deps:file",
      "applyLoadedLayout",
      "deps:render",
      "renderAll",
      "deps:render",
      "renderTopControls",
      "deps:render",
      "renderPalette",
      "deps:edit",
      "paletteVariant",
      "deps:render",
      "renderProperties",
      "deps:render",
      "renderLayers",
      "deps:render",
      "renderOverlay",
      "deps:preview",
      "preview",
      "deps:file",
      "open",
      "deps:file",
      "reset",
      "deps:file",
      "save",
      "deps:command",
      "duplicate",
      "deps:file",
      "validate",
      "deps:file",
      "snapshot",
      "deps:file",
      "fieldPack",
      "deps:weather",
      "weather",
      "deps:context",
      "vehicle",
      "deps:context",
      "screen",
      "deps:context",
      "importOther",
      "deps:context",
      "language",
      "deps:background",
      "backgroundColor",
      "deps:background",
      "chooseBackground",
      "deps:background",
      "clearBackground",
      "deps:edit",
      "propertyInput",
      "deps:pointer",
      "pointerDown",
      "deps:pointer",
      "pointerMove",
      "deps:pointer",
      "pointerUp",
      "deps:command",
      "keyDown",
      "deps:command",
      "delete",
      "deps:command",
      "bumpZ",
      "deps:history",
      "markDirty",
      "deps:history",
      "snapshotState",
      "deps:history",
      "recordHistory",
      "deps:history",
      "pushUndo",
      "deps:history",
      "undo",
      "deps:history",
      "redo",
    ],
  );
});

test("createAppHandlers exposes view ui and timer helpers around shared state", () => {
  const calls = [];
  const state = {
    appLanguage: "ko",
    dirty: true,
    layout: { canvas: { width: 1920, height: 480 }, elements: [{ id: "speed", z: 1 }] },
  };
  const stageRect = { left: 20, top: 30, width: 960, height: 240 };
  const dom = {
    previewStage: {
      getBoundingClientRect: () => stageRect,
    },
  };
  let scheduledCallback = null;
  const refs = {
    clearTimeoutRef: (timer) => calls.push(["clearTimeout", timer]),
    documentRef: {},
    setTimeoutRef: (callback, delay) => {
      scheduledCallback = callback;
      calls.push(["setTimeout", delay]);
      return "timer-1";
    },
    windowRef: {
      confirm: (message) => {
        calls.push(["confirm", message]);
        return false;
      },
    },
  };
  const modules = {
    appDeps: dependencyFactories(calls, {}),
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
    previewActions: {
      renderPreview: async () => calls.push(["preview"]),
    },
    viewModel: {
      eventToCanvasPoint: (event, canvas, rect) => {
        calls.push(["eventToCanvas", event.clientX, canvas, rect]);
        return { x: 10, y: 20 };
      },
      canvasScale: (canvas, rect) => {
        calls.push(["canvasScale", canvas, rect]);
        return { x: 0.5, y: 0.5 };
      },
      hitTestElement: (elements, x, y) => {
        calls.push(["hitTest", elements, x, y]);
        return "speed";
      },
    },
  };

  const handlers = AppHandlers.createAppHandlers({
    state,
    dom,
    modules,
    refs,
    runtimeFactory: () => ({}),
  });

  assert.deepEqual(handlers.eventToCanvas({ clientX: 120, clientY: 80 }), { x: 10, y: 20 });
  assert.deepEqual(handlers.canvasScale(), { x: 0.5, y: 0.5 });
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
  handlers.schedulePreview(75);

  assert.equal(scheduledCallback, handlers.renderPreview);
  assert.deepEqual(calls.at(-2), ["clearTimeout", null]);
  assert.deepEqual(calls.at(-1), ["setTimeout", 75]);
});

function dependencyFactories(calls, expectedRuntime) {
  function dependency(name) {
    return (runtime) => {
      calls.push([`deps:${name}`, runtime]);
      assert.equal(runtime, expectedRuntime);
      return { name };
    };
  }

  return {
    backgroundActionDeps: dependency("background"),
    commandActionDeps: dependency("command"),
    contextCommandDeps: dependency("context"),
    editActionDeps: dependency("edit"),
    fileCommandDeps: dependency("file"),
    historyCommandDeps: dependency("history"),
    pointerActionDeps: dependency("pointer"),
    previewDeps: dependency("preview"),
    renderCoordinatorDeps: dependency("render"),
    weatherActionDeps: dependency("weather"),
  };
}
