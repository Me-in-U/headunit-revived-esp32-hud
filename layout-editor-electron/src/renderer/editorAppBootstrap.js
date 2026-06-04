(function exposeEditorAppBootstrap(globalScope) {
  async function initializeEditor(state, dom, deps) {
    deps.domBindings.bindDom(dom, deps.documentRef);
    deps.domBindings.bindActions(dom, deps.windowRef, state, deps.handlers);
    dom.languageSelect.value = state.appLanguage;
    deps.applyLanguage();
    deps.setStatus(deps.translate("loading"));
    state.metadata = await deps.hudEditor.metadata();
    state.vehicleProfiles = state.metadata.vehicleProfiles || {};
    state.activeCategory = Object.keys(state.metadata.palette || {})[0] || "";
    const loaded = await deps.hudEditor.loadDefault();
    deps.applyLoadedLayout(loaded);
    deps.renderAll();
    await deps.renderPreview();
    if (deps.hudEditor.onVehicleLiveEvent) {
      state.vehicleLive.unsubscribe = deps.hudEditor.onVehicleLiveEvent(deps.handlers.onVehicleLiveEvent);
    }
  }

  const api = {
    initializeEditor,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppBootstrap = api;
})(typeof window !== "undefined" ? window : globalThis);
