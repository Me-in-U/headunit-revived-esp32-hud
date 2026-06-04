(function exposeEditorAppRenderHandlers(globalScope) {
  function createAppRenderHandlers({ state, dom, modules, refs, runtimeFactory }) {
    let previewTimer = null;

    function deps(factoryName) {
      return modules.appDeps[factoryName](runtimeFactory());
    }

    function renderAll() {
      modules.renderCoordinator.renderAll(state, dom, deps("renderCoordinatorDeps"));
    }

    function renderTopControls() {
      modules.renderCoordinator.renderTopControls(state, dom, deps("renderCoordinatorDeps"));
    }

    function renderPalette() {
      modules.renderCoordinator.renderPalette(state, dom, deps("renderCoordinatorDeps"));
    }

    function selectPaletteVariant(item, category) {
      modules.editActions.selectPaletteVariant(state, item, category, deps("editActionDeps"));
    }

    function renderProperties() {
      modules.renderCoordinator.renderProperties(state, dom, deps("renderCoordinatorDeps"));
    }

    function renderLayers() {
      modules.renderCoordinator.renderLayers(state, dom, deps("renderCoordinatorDeps"));
    }

    function renderOverlay() {
      modules.renderCoordinator.renderOverlay(state, dom, deps("renderCoordinatorDeps"));
    }

    function renderVehicleTools() {
      modules.renderCoordinator.renderVehicleTools(state, dom, deps("renderCoordinatorDeps"));
    }

    async function renderPreview() {
      await modules.previewActions.renderPreview(state, dom, deps("previewDeps"));
    }

    function schedulePreview(delay = 100) {
      const clearTimeoutRef = refs.clearTimeoutRef || globalScope.clearTimeout;
      const setTimeoutRef = refs.setTimeoutRef || globalScope.setTimeout;
      clearTimeoutRef(previewTimer);
      previewTimer = setTimeoutRef(renderPreview, delay);
    }

    return {
      renderAll,
      renderLayers,
      renderOverlay,
      renderPalette,
      renderPreview,
      renderProperties,
      renderTopControls,
      renderVehicleTools,
      schedulePreview,
      selectPaletteVariant,
    };
  }

  const api = {
    createAppRenderHandlers,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppRenderHandlers = api;
})(typeof window !== "undefined" ? window : globalThis);
