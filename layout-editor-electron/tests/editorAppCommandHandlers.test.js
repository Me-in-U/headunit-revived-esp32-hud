const assert = require("node:assert/strict");
const test = require("node:test");

const CommandHandlers = require("../src/renderer/editorAppCommandHandlers.js");

test("createAppCommandHandlers routes command context background pointer history and file handlers", async () => {
  const calls = [];
  const runtime = { runtime: true };
  const response = { ok: true };
  const state = {
    layout: { elements: [{ id: "speed" }] },
  };
  const dom = {
    backgroundColor: { value: "#112233" },
    languageSelect: { value: "en" },
    screenSelect: { value: "bridge" },
    vehicleSelect: { value: "avante" },
  };
  const refs = {
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
      handlePropertyInput: (actualState, actualDom, event, selectedElement, deps) =>
        calls.push(["propertyInput", actualState, actualDom, event.target.name, selectedElement(), deps.name]),
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
    weatherActions: {
      fetchWeatherCommand: async (actualState, hudEditor, navigatorRef, deps) =>
        calls.push(["weather", actualState, hudEditor, navigatorRef, deps.name]),
    },
  };

  const handlers = CommandHandlers.createAppCommandHandlers({
    state,
    dom,
    modules,
    refs,
    runtimeFactory: () => runtime,
    selectedElement: () => state.layout.elements[0],
  });

  assert.equal(handlers.applyLoadedLayout(response), "loaded");
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

  assert.deepEqual(calls.map((call) => call[0]), [
    "deps:file",
    "applyLoadedLayout",
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
  ]);
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
    weatherActionDeps: dependency("weather"),
  };
}
