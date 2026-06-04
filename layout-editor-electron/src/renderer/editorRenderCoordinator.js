(function exposeEditorRenderCoordinator(globalScope) {
  function renderAll(state, dom, deps) {
    if (!state.layout) {
      return false;
    }
    renderTopControls(state, dom, deps);
    renderPalette(state, dom, deps);
    renderProperties(state, dom, deps);
    renderLayers(state, dom, deps);
    renderVehicleTools(state, dom, deps);
    renderOverlay(state, dom, deps);
    deps.updateFilePath();
    return true;
  }

  function renderTopControls(state, dom, deps) {
    deps.topControls.renderTopControls(state, dom, {
      documentRef: deps.documentRef,
      validColor: deps.viewModel.validColor,
      vehicleLabel: deps.viewModel.vehicleLabel,
    });
  }

  function renderPalette(state, dom, deps) {
    deps.paletteView.renderPalette(state, dom, {
      documentRef: deps.documentRef,
      editor: deps.editor,
      viewModel: deps.viewModel,
      translate: deps.translate,
      onCategorySelect: (category) => {
        state.activeCategory = category;
        renderPalette(state, dom, deps);
      },
      onVariantSelect: deps.selectPaletteVariant,
    });
  }

  function renderProperties(state, dom, deps) {
    deps.inspectorView.renderProperties(state, dom, {
      documentRef: deps.documentRef,
      editor: deps.editor,
      viewModel: deps.viewModel,
      selectedElement: deps.selectedElement,
      translate: deps.translate,
      sectionLabel: (section) => deps.i18n.sectionLabel(state.appLanguage, section),
      propertyLabel: deps.propertyLabel,
      onPropertyInput: deps.onPropertyInput,
    });
  }

  function renderLayers(state, dom, deps) {
    deps.layerView.renderLayers(state, dom, {
      documentRef: deps.documentRef,
      viewModel: deps.viewModel,
      translate: deps.translate,
      onLayerSelect: (elementId) => {
        state.selectedId = elementId;
        renderAll(state, dom, deps);
      },
    });
  }

  function renderOverlay(state, dom, deps) {
    deps.overlayView.renderOverlay(state, dom, {
      documentRef: deps.documentRef,
      canvasScale: deps.canvasScale,
    });
  }

  function renderVehicleTools(state, dom, deps) {
    if (!deps.vehicleLiveView) {
      return;
    }
    deps.vehicleLiveView.renderVehicleTools(state, dom, {
      documentRef: deps.documentRef,
      translate: deps.translate,
    });
  }

  const api = {
    renderAll,
    renderLayers,
    renderOverlay,
    renderPalette,
    renderProperties,
    renderVehicleTools,
    renderTopControls,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorRenderCoordinator = api;
})(typeof window !== "undefined" ? window : globalThis);
