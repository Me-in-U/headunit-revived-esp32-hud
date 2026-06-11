const assert = require("node:assert/strict");
const test = require("node:test");

const Bootstrap = require("../src/renderer/editorAppBootstrap.js");

test("initializeEditor binds UI loads default layout and renders initial preview", async () => {
  const calls = [];
  const state = { appLanguage: "ko", vehicleLive: {} };
  const dom = { languageSelect: { value: "" } };
  const metadata = { palette: { Primary: [], Navigation: [] }, vehicleProfiles: { avante: {} } };
  const loaded = { ok: true, path: "default.json", layout: { id: "layout" } };

  await Bootstrap.initializeEditor(state, dom, {
    documentRef: "document",
    windowRef: "window",
    domBindings: {
      bindDom(target, documentRef) {
        calls.push(["bindDom", target === dom, documentRef]);
      },
      bindActions(target, windowRef, boundState, handlers) {
        calls.push(["bindActions", target === dom, windowRef, boundState === state, Object.keys(handlers).sort()]);
      },
    },
    handlers: {
      onVehicleLiveEvent() {},
      openLayout() {},
      saveLayout() {},
    },
    hudEditor: {
      async metadata() {
        calls.push(["metadata"]);
        return metadata;
      },
      async loadDefault() {
        calls.push(["loadDefault"]);
        return loaded;
      },
      onVehicleLiveEvent(handler) {
        calls.push(["onVehicleLiveEvent", handler.name]);
        return "unsubscribe-live";
      },
    },
    applyLanguage() {
      calls.push(["applyLanguage"]);
    },
    applyLoadedLayout(response) {
      calls.push(["applyLoadedLayout", response]);
    },
    renderAll() {
      calls.push(["renderAll"]);
    },
    async renderPreview() {
      calls.push(["renderPreview"]);
    },
    setStatus(message) {
      calls.push(["setStatus", message]);
    },
    translate(key) {
      return `t:${key}`;
    },
  });

  assert.equal(dom.languageSelect.value, "ko");
  assert.equal(state.metadata, metadata);
  assert.equal(state.vehicleProfiles, metadata.vehicleProfiles);
  assert.equal(state.activeCategory, "Primary");
  assert.equal(state.vehicleLive.unsubscribe, "unsubscribe-live");
  assert.deepEqual(calls, [
    ["bindDom", true, "document"],
    ["bindActions", true, "window", true, ["onVehicleLiveEvent", "openLayout", "saveLayout"]],
    ["applyLanguage"],
    ["setStatus", "t:loading"],
    ["metadata"],
    ["loadDefault"],
    ["applyLoadedLayout", loaded],
    ["renderAll"],
    ["renderPreview"],
    ["onVehicleLiveEvent", "onVehicleLiveEvent"],
  ]);
});

test("initializeEditor tolerates missing palette and vehicle profiles in metadata", async () => {
  const state = { appLanguage: "en", vehicleLive: {} };
  const dom = { languageSelect: { value: "" } };

  await Bootstrap.initializeEditor(state, dom, {
    documentRef: {},
    windowRef: {},
    domBindings: {
      bindDom() {},
      bindActions() {},
    },
    handlers: {},
    hudEditor: {
      async metadata() {
        return {};
      },
      async loadDefault() {
        return { ok: true, layout: {} };
      },
    },
    applyLanguage() {},
    applyLoadedLayout() {},
    renderAll() {},
    async renderPreview() {},
    setStatus() {},
    translate(key) {
      return key;
    },
  });

  assert.deepEqual(state.vehicleProfiles, {});
  assert.equal(state.activeCategory, "");
});
