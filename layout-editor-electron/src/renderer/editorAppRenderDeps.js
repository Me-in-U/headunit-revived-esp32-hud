(function exposeEditorAppRenderDeps(globalScope) {
  function renderCoordinatorDeps(runtime) {
    return {
      canvasScale: runtime.canvasScale,
      documentRef: runtime.documentRef,
      editor: runtime.editor,
      i18n: runtime.i18n,
      inspectorView: runtime.inspectorView,
      layerView: runtime.layerView,
      onPropertyInput: runtime.onPropertyInput,
      overlayView: runtime.overlayView,
      paletteView: runtime.paletteView,
      propertyLabel: runtime.propertyLabel,
      selectedElement: runtime.selectedElement,
      selectPaletteVariant: runtime.selectPaletteVariant,
      topControls: runtime.topControls,
      translate: runtime.translate,
      updateFilePath: runtime.updateFilePath,
      viewModel: runtime.viewModel,
    };
  }

  function previewDeps(runtime) {
    return {
      hideDragGhost: () => runtime.pointerActions.hideDragGhost(runtime.dom),
      renderOverlay: runtime.renderOverlay,
      renderPreview: (request) => runtime.windowRef.hudEditor.renderPreview(request),
      requestAnimationFrame: runtime.requestAnimationFrameRef,
      schedulePreview: runtime.schedulePreview,
      setStatus: runtime.setStatus,
      translate: runtime.translate,
    };
  }

  const api = {
    previewDeps,
    renderCoordinatorDeps,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppRenderDeps = api;
})(typeof window !== "undefined" ? window : globalThis);
