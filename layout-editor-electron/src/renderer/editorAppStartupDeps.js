(function exposeEditorAppStartupDeps(globalScope) {
  function appBootstrapDeps(runtime) {
    return {
      applyLanguage: runtime.applyLanguage,
      applyLoadedLayout: runtime.applyLoadedLayout,
      documentRef: runtime.documentRef,
      domBindings: runtime.domBindings,
      handlers: editorEventHandlers(runtime),
      hudEditor: runtime.windowRef.hudEditor,
      renderAll: runtime.renderAll,
      renderPreview: runtime.renderPreview,
      setStatus: runtime.setStatus,
      translate: runtime.translate,
      windowRef: runtime.windowRef,
    };
  }

  function editorEventHandlers(runtime) {
    return {
      bumpZ: runtime.bumpZ,
      chooseBackgroundImage: runtime.chooseBackgroundImage,
      clearBackgroundImage: runtime.clearBackgroundImage,
      deleteSelected: runtime.deleteSelected,
      duplicateSelected: runtime.duplicateSelected,
      exportFieldPack: runtime.exportFieldPack,
      exportSnapshot: runtime.exportSnapshot,
      fetchWeather: runtime.fetchWeather,
      hideValidationDrawer: runtime.hideValidationDrawer,
      importOtherScreen: runtime.importOtherScreen,
      onBackgroundColor: runtime.onBackgroundColor,
      onKeyDown: runtime.onKeyDown,
      onLanguageChange: runtime.onLanguageChange,
      onPointerDown: runtime.onPointerDown,
      onPointerMove: runtime.onPointerMove,
      onPointerUp: runtime.onPointerUp,
      onScreenChange: runtime.onScreenChange,
      onVehicleChange: runtime.onVehicleChange,
      openLayout: runtime.openLayout,
      redo: runtime.redo,
      renderOverlay: runtime.renderOverlay,
      renderPalette: runtime.renderPalette,
      resetDefaultLayout: runtime.resetDefaultLayout,
      saveLayout: runtime.saveLayout,
      undo: runtime.undo,
      validateLayout: runtime.validateLayout,
    };
  }

  const api = {
    appBootstrapDeps,
    editorEventHandlers,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppStartupDeps = api;
})(typeof window !== "undefined" ? window : globalThis);
