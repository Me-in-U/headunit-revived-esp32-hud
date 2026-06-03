(function exposeEditorDomBindings(globalScope) {
  const DOM_IDS = [
    "filePath",
    "openBtn",
    "saveBtn",
    "saveAsBtn",
    "undoBtn",
    "redoBtn",
    "resetBtn",
    "validateBtn",
    "exportPngBtn",
    "fieldPackBtn",
    "vehicleSelect",
    "screenSelect",
    "importScreenBtn",
    "languageSelect",
    "weatherBtn",
    "backgroundColor",
    "backgroundImageBtn",
    "clearBackgroundBtn",
    "categoryTabs",
    "paletteSearch",
    "paletteButtons",
    "previewFrame",
    "previewStage",
    "previewImage",
    "dragGhost",
    "selectionOverlay",
    "canvasMeta",
    "statusText",
    "pixelStatus",
    "zoomFitBtn",
    "deleteBtn",
    "selectedLabel",
    "propertyForm",
    "validationDrawer",
    "validationCloseBtn",
    "validationMessages",
    "frontBtn",
    "backBtn",
    "duplicateBtn",
    "layerCount",
    "layerList",
  ];

  function bindDom(dom, documentRef) {
    for (const id of DOM_IDS) {
      dom[id] = documentRef.getElementById(id);
    }
    return dom;
  }

  function bindActions(dom, windowRef, state, handlers) {
    dom.openBtn.addEventListener("click", handlers.openLayout);
    dom.saveBtn.addEventListener("click", () => handlers.saveLayout(false));
    dom.saveAsBtn.addEventListener("click", () => handlers.saveLayout(true));
    dom.undoBtn.addEventListener("click", handlers.undo);
    dom.redoBtn.addEventListener("click", handlers.redo);
    dom.resetBtn.addEventListener("click", handlers.resetDefaultLayout);
    dom.validateBtn.addEventListener("click", handlers.validateLayout);
    dom.exportPngBtn.addEventListener("click", handlers.exportSnapshot);
    dom.fieldPackBtn.addEventListener("click", handlers.exportFieldPack);
    dom.vehicleSelect.addEventListener("change", handlers.onVehicleChange);
    dom.screenSelect.addEventListener("change", handlers.onScreenChange);
    dom.importScreenBtn.addEventListener("click", handlers.importOtherScreen);
    dom.languageSelect.addEventListener("change", handlers.onLanguageChange);
    dom.weatherBtn.addEventListener("click", handlers.fetchWeather);
    dom.backgroundColor.addEventListener("input", handlers.onBackgroundColor);
    dom.backgroundImageBtn.addEventListener("click", handlers.chooseBackgroundImage);
    dom.clearBackgroundBtn.addEventListener("click", handlers.clearBackgroundImage);
    dom.paletteSearch.addEventListener("input", () => {
      state.paletteQuery = dom.paletteSearch.value.trim().toLowerCase();
      handlers.renderPalette();
    });
    dom.validationCloseBtn.addEventListener("click", handlers.hideValidationDrawer);
    dom.deleteBtn.addEventListener("click", handlers.deleteSelected);
    dom.duplicateBtn.addEventListener("click", handlers.duplicateSelected);
    dom.frontBtn.addEventListener("click", () => handlers.bumpZ(1));
    dom.backBtn.addEventListener("click", () => handlers.bumpZ(-1));
    dom.zoomFitBtn.addEventListener("click", handlers.renderOverlay);
    dom.selectionOverlay.addEventListener("pointerdown", handlers.onPointerDown);
    windowRef.addEventListener("pointermove", handlers.onPointerMove);
    windowRef.addEventListener("pointerup", handlers.onPointerUp);
    windowRef.addEventListener("resize", handlers.renderOverlay);
    windowRef.addEventListener("keydown", handlers.onKeyDown);
  }

  const api = {
    DOM_IDS,
    bindActions,
    bindDom,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorDomBindings = api;
})(typeof window !== "undefined" ? window : globalThis);
