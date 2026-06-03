const assert = require("node:assert/strict");
const test = require("node:test");

const RenderHandlers = require("../src/renderer/editorAppRenderHandlers.js");

test("createAppRenderHandlers routes render preview palette and timer handlers", async () => {
  const calls = [];
  const runtime = { runtime: true };
  const state = { layout: {} };
  const dom = {};
  let scheduledCallback = null;
  const refs = {
    clearTimeoutRef: (timer) => calls.push(["clearTimeout", timer]),
    setTimeoutRef: (callback, delay) => {
      scheduledCallback = callback;
      calls.push(["setTimeout", delay]);
      return "timer-1";
    },
  };
  const modules = {
    appDeps: {
      editActionDeps: dep("edit", calls, runtime),
      previewDeps: dep("preview", calls, runtime),
      renderCoordinatorDeps: dep("render", calls, runtime),
    },
    editActions: {
      selectPaletteVariant: (actualState, item, category, deps) => calls.push(["paletteVariant", actualState, item.id, category, deps.name]),
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
  };

  const handlers = RenderHandlers.createAppRenderHandlers({
    state,
    dom,
    modules,
    refs,
    runtimeFactory: () => runtime,
  });

  handlers.renderAll();
  handlers.renderTopControls();
  handlers.renderPalette();
  handlers.selectPaletteVariant({ id: "speed" }, "primary");
  handlers.renderProperties();
  handlers.renderLayers();
  handlers.renderOverlay();
  await handlers.renderPreview();
  handlers.schedulePreview(75);

  assert.deepEqual(calls.map((call) => call[0]), [
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
    "clearTimeout",
    "setTimeout",
  ]);
  assert.equal(scheduledCallback, handlers.renderPreview);
});

function dep(name, calls, expectedRuntime) {
  return (runtime) => {
    calls.push([`deps:${name}`, runtime]);
    assert.equal(runtime, expectedRuntime);
    return { name };
  };
}
